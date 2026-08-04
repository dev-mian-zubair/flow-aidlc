"""Offline, deterministic reproducibility scorer for Flow artifacts.

Scores how close a candidate set of Flow artifacts is to a hand-authored
golden reference WITHOUT any LLM or network call — safe to run in CI.

Adopted from AWS AI-DLC's HeuristicScorer approach: three heuristic dimensions
(intent, design, completeness) weighted into a single overall score.

Usage:
    python -m flow_aidlc.checks.scorer <ref_dir> <cand_dir>

    Prints per-file overall scores and mean_overall; exits 0 always
    (scoring is reporting; gating lives in reference_check).
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Stopwords — small English set removed from TF vectors
# ---------------------------------------------------------------------------

_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by",
    "do", "for", "from", "has", "have", "he", "her", "him", "his",
    "how", "i", "if", "in", "is", "it", "its", "me", "my", "not",
    "of", "on", "or", "our", "out", "she", "so", "that", "the",
    "their", "them", "then", "there", "they", "this", "to", "us",
    "was", "we", "were", "what", "when", "where", "which", "who",
    "will", "with", "would", "you", "your",
})

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _word_tokens(text: str) -> list[str]:
    """Lowercase word tokens with stopwords removed."""
    raw = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in raw if t not in _STOPWORDS]


def _tf_vector(tokens: list[str]) -> dict[str, float]:
    """Term-frequency vector (counts, not normalised — cosine handles that)."""
    vec: dict[str, float] = {}
    for t in tokens:
        vec[t] = vec.get(t, 0.0) + 1.0
    return vec


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two TF dicts.  Empty-both → 1.0 (no disagreement)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    dot = sum(a.get(k, 0.0) * v for k, v in b.items())
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    # Clamp to 1.0: floating-point rounding can push the ratio to
    # 1.0000000000000002, which would violate the [0, 1] contract and make
    # score_docs(t, t) only approximately 1.0 instead of exactly 1.0.
    return min(dot / (mag_a * mag_b), 1.0)


def _tech_identifiers(text: str) -> set[str]:
    """Extract technical identifiers: tokens containing _, /, . or an internal uppercase."""
    # Broad capture of identifier-like tokens
    raw = re.findall(r"[A-Za-z_][A-Za-z0-9_/.]*[A-Za-z0-9_]", text)
    result: set[str] = set()
    for tok in raw:
        # keep if it contains _, /, . or has an internal uppercase after first char
        if "_" in tok or "/" in tok or "." in tok:
            result.add(tok)
        elif any(c.isupper() for c in tok[1:]):
            # CamelCase: internal uppercase
            result.add(tok)
    return result


def _heading_lines(text: str) -> set[str]:
    """Return the set of lines that start with '#' (markdown headings)."""
    result: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            result.add(stripped)
    return result


def _jaccard(a: set, b: set) -> float:
    """Jaccard index. Both empty → 1.0 (no disagreement). One empty → 0.0."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 1.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_docs(reference_text: str, candidate_text: str) -> dict:
    """Score candidate against reference; returns dict with intent/design/completeness/overall.

    All values are in [0, 1].  Weights: overall = 0.4*intent + 0.4*design + 0.2*completeness.

    Identical non-empty texts yield overall == 1.0.
    """
    # --- intent: cosine of TF vectors ---
    ref_tokens = _word_tokens(reference_text)
    cand_tokens = _word_tokens(candidate_text)
    ref_tf = _tf_vector(ref_tokens)
    cand_tf = _tf_vector(cand_tokens)
    intent = _cosine(ref_tf, cand_tf)

    # --- design: mean of two Jaccard indices ---
    ref_ids = _tech_identifiers(reference_text)
    cand_ids = _tech_identifiers(candidate_text)
    jaccard_ids = _jaccard(ref_ids, cand_ids)

    ref_headings = _heading_lines(reference_text)
    cand_headings = _heading_lines(candidate_text)
    jaccard_headings = _jaccard(ref_headings, cand_headings)

    design = (jaccard_ids + jaccard_headings) / 2.0

    # --- completeness: fraction of reference's headings present in candidate ---
    if not ref_headings:
        completeness = 1.0
    else:
        present = len(ref_headings & cand_headings)
        completeness = present / len(ref_headings)

    # --- overall ---
    overall = 0.4 * intent + 0.4 * design + 0.2 * completeness

    return {
        "intent": float(intent),
        "design": float(design),
        "completeness": float(completeness),
        "overall": float(overall),
    }


def score_dirs(reference_dir: Path | str, candidate_dir: Path | str) -> dict:
    """Score candidate directory against reference directory.

    Pairs files by path relative to each root; only files present in BOTH are
    scored.  Returns:
        {
            "per_file": {<relpath>: <score_docs dict>, ...},
            "mean_overall": float,   # 0.0 if no common files
        }
    """
    reference_dir = Path(reference_dir)
    candidate_dir = Path(candidate_dir)

    ref_files: dict[str, Path] = {}
    for p in reference_dir.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(reference_dir))
            ref_files[rel] = p

    per_file: dict[str, dict] = {}
    for rel, ref_path in ref_files.items():
        cand_path = candidate_dir / rel
        if cand_path.exists() and cand_path.is_file():
            ref_text = ref_path.read_text(encoding="utf-8", errors="replace")
            cand_text = cand_path.read_text(encoding="utf-8", errors="replace")
            per_file[rel] = score_docs(ref_text, cand_text)

    if per_file:
        mean_overall = sum(s["overall"] for s in per_file.values()) / len(per_file)
    else:
        mean_overall = 0.0

    return {"per_file": per_file, "mean_overall": float(mean_overall)}


def main(argv: list[str] | None = None) -> int:
    """CLI: python -m flow_aidlc.checks.scorer <ref_dir> <cand_dir>

    Prints per-file overall scores and mean_overall.  Exits 0 always.
    """
    args = (argv or sys.argv)[1:]
    if len(args) < 2:
        print("Usage: python -m flow_aidlc.checks.scorer <ref_dir> <cand_dir>", file=sys.stderr)
        return 1

    ref_dir = Path(args[0])
    cand_dir = Path(args[1])

    result = score_dirs(ref_dir, cand_dir)
    per_file = result["per_file"]

    if not per_file:
        print("(no common files found between ref and candidate)")
    else:
        for relpath, scores in sorted(per_file.items()):
            print(f"  {relpath:50s}  overall={scores['overall']:.4f}")
    print(f"mean_overall: {result['mean_overall']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
