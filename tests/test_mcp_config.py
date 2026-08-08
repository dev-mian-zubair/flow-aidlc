from flow_aidlc import mcp_config as mc

def _mcp():
    return {"mcpServers": {
        "github": {"command": "npx", "args": ["-y", "srv-github"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}},
        "graphify": {"command": "graphify-mcp", "args": ["graph.json"]},
        "pg": {"command": "npx", "args": ["pg"],
                "env": {"FLOW_DB_READONLY_URI": "${FLOW_DB_READONLY_URI}"}},
    }}

def test_secret_vars_only_secret_bearing_servers():
    assert mc.secret_vars(_mcp()) == {
        "github": ["GITHUB_TOKEN"], "pg": ["FLOW_DB_READONLY_URI"]}

def test_all_secret_vars_flat_sorted_unique():
    assert mc.all_secret_vars(_mcp()) == ["FLOW_DB_READONLY_URI", "GITHUB_TOKEN"]

def test_wrap_then_is_wrapped_and_drops_env():
    w = mc.wrap_server(_mcp()["mcpServers"]["github"], "infisical", ["run"])
    assert mc.is_wrapped(w)
    assert w["command"] == "infisical"
    assert w["args"] == ["run", "--", "npx", "-y", "srv-github"]
    assert "env" not in w
    assert w[mc.STASH_KEY]["env"] == {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}

def test_wrap_is_idempotent():
    once = mc.wrap_server(_mcp()["mcpServers"]["github"], "infisical", ["run"])
    twice = mc.wrap_server(once, "infisical", ["run"])
    assert twice == once

def test_wrap_with_env_flag():
    w = mc.wrap_server(_mcp()["mcpServers"]["github"], "infisical", ["run", "--env", "prod"])
    assert w["args"][:4] == ["run", "--env", "prod", "--"]

def test_unwrap_round_trips_exactly():
    orig = _mcp()["mcpServers"]["github"]
    assert mc.unwrap_server(mc.wrap_server(orig, "infisical", ["run"])) == orig

def test_unwrap_preserves_custom_keys_and_args():
    custom = {"command": "npx", "args": ["a", "b"],
              "env": {"T": "${T}", "EXTRA": "literal"}, "cwd": "/x"}
    assert mc.unwrap_server(mc.wrap_server(custom, "infisical", ["run"])) == custom

def test_unwrap_noop_when_not_wrapped():
    plain = _mcp()["mcpServers"]["graphify"]
    assert mc.unwrap_server(plain) == plain

def test_secret_vars_stable_after_wrap():
    m = _mcp()
    m["mcpServers"]["github"] = mc.wrap_server(m["mcpServers"]["github"], "infisical", ["run"])
    assert "GITHUB_TOKEN" in mc.secret_vars(m)["github"]
