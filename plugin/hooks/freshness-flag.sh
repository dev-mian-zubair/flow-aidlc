#!/usr/bin/env bash
# freshness-flag.sh — Hook: PostToolUse (Write | Edit)
# When .flow/knowledge-map.yaml exists, looks up the knowledge doc that
# "derives-from" the edited file path. If found:
#   1. Appends a stale entry to <worklog>/freshness.md
#   2. Sets/updates the owning doc's frontmatter "status:" field to STALE
# If knowledge-map.yaml is absent (WS-6 not built yet) → silent no-op.
# Fail-open: exits 0 under all conditions.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh" || true

flow_read_input

file_path="$(flow_field tool_input.file_path)"
[ -z "$file_path" ] && exit 0

root="$(flow_repo_root)"
[ -z "$root" ] && exit 0

knowledge_map="$root/.flow/knowledge-map.yaml"
# WS-6 not built yet → no-op
[ -f "$knowledge_map" ] || exit 0

worklog="$(flow_active_worklog)"
[ -z "$worklog" ] && exit 0

iso="$(flow_iso_now)"

# Use python3 to parse YAML (fallback: treat as plain text if PyYAML unavailable)
# and find the owning doc whose derives-from glob matches the edited path.
owning_doc="$(python3 -c "
import sys, fnmatch

edited = sys.argv[1]
# Strip leading ./
if edited.startswith('./'):
    edited = edited[2:]

try:
    import yaml
    with open(sys.argv[2]) as f:
        data = yaml.safe_load(f)
except ImportError:
    # PyYAML not available — fall back to line-scan heuristic
    data = None

if data is None:
    # Fallback: scan lines for 'derives-from:' patterns
    with open(sys.argv[2]) as f:
        content = f.read()
    lines = content.splitlines()
    current_doc = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('doc:') or stripped.endswith(':') and not stripped.startswith('-'):
            current_doc = stripped.rstrip(':').replace('doc:', '').strip()
        if 'derives-from' in stripped:
            import re
            patterns = re.findall(r'[\w/.*?-]+\.[\w*]+', stripped)
            for pat in patterns:
                if fnmatch.fnmatch(edited, pat) or fnmatch.fnmatch(edited, pat.lstrip('/')):
                    print(current_doc or '')
                    sys.exit(0)
    sys.exit(0)

# data is a dict or list
docs = data if isinstance(data, list) else data.get('docs', data.get('knowledge', []))
if not isinstance(docs, list):
    sys.exit(0)

for entry in docs:
    if not isinstance(entry, dict):
        continue
    derives = entry.get('derives-from', [])
    if isinstance(derives, str):
        derives = [derives]
    doc_path = entry.get('doc', entry.get('path', ''))
    for pattern in derives:
        if fnmatch.fnmatch(edited, pattern) or fnmatch.fnmatch(edited, pattern.lstrip('/')):
            print(doc_path)
            sys.exit(0)
" "$file_path" "$knowledge_map" 2>/dev/null || true)"

[ -z "$owning_doc" ] && exit 0

# 1. Append to freshness.md
freshness_file="$worklog/freshness.md"
if [ ! -f "$freshness_file" ]; then
    mkdir -p "$(dirname "$freshness_file")"
    touch "$freshness_file"
fi
echo "- $file_path → $owning_doc (stale @ $iso)" >> "$freshness_file"

# 2. Mark owning doc's frontmatter status: STALE
owning_doc_abs="$root/$owning_doc"
if [ -f "$owning_doc_abs" ]; then
    python3 -c "
import sys, re

path = sys.argv[1]
with open(path, 'r') as f:
    content = f.read()

# If frontmatter exists (--- block at top), update or add status:
if content.startswith('---'):
    # Find end of frontmatter
    end = content.find('---', 3)
    if end != -1:
        front = content[:end]
        rest = content[end:]
        if re.search(r'^status:', front, re.MULTILINE):
            front = re.sub(r'^status:.*$', 'status: STALE', front, flags=re.MULTILINE)
        else:
            front = front.rstrip('\n') + '\nstatus: STALE\n'
        with open(path, 'w') as f:
            f.write(front + rest)
    # else: malformed frontmatter, skip
else:
    # Prepend frontmatter
    with open(path, 'w') as f:
        f.write('---\nstatus: STALE\n---\n' + content)
" "$owning_doc_abs" 2>/dev/null || true
fi

exit 0
