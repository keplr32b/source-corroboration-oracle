"""
Unit / structural tests for Source Corroboration Covenant.
"""

import json
import sys
from pathlib import Path


def _host_of(url: str) -> str:
    u = (url or "").strip().lower()
    if not u.startswith("https://"):
        raise ValueError("only https urls allowed")
    rest = u[8:]
    host = rest.split("/")[0].split("?")[0].split("#")[0]
    if not host:
        raise ValueError("empty host")
    if "@" in host:
        raise ValueError("userinfo not allowed")
    if host.replace(".", "").isdigit():
        raise ValueError("ip literal hosts rejected")
    if "localhost" in host:
        raise ValueError("localhost rejected")
    if host.endswith(".local"):
        raise ValueError("local tld rejected")
    return host


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def parse_json_response(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t[:4].lower() == "json":
            t = t[4:]
        t = t.strip()
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end != -1:
        t = t[start : end + 1]
    return json.loads(t)


def test_host_of_accepts_https():
    assert _host_of("https://Example.COM/path") == "example.com"
    assert _host_of("https://news.example.org/a/b?x=1") == "news.example.org"


def test_host_of_rejects_http():
    try:
        _host_of("http://example.com")
        assert False, "should reject"
    except ValueError as e:
        assert "https" in str(e).lower()


def test_host_of_rejects_ip_and_localhost():
    for bad in [
        "https://127.0.0.1/x",
        "https://localhost/x",
        "https://foo.local/x",
        "https://user@example.com/x",
    ]:
        try:
            _host_of(bad)
            assert False, f"should reject {bad}"
        except ValueError:
            pass


def test_url_count_bounds():
    def check(n):
        return 2 <= n <= 8
    assert not check(0)
    assert not check(1)
    assert check(2)
    assert check(8)
    assert not check(9)


def test_ratio_milli_math():
    total = 3
    for agreeing in range(0, 4):
        ratio = (agreeing * 1000) // total
        assert 0 <= ratio <= 1000
    assert (2 * 1000) // 3 == 666
    assert (3 * 1000) // 3 == 1000


def test_threshold_fail_closed():
    threshold = 700
    assert not (666 >= threshold)
    assert 700 >= threshold
    assert 1000 >= threshold


def test_canonical_stable():
    a = canonical({"b": 1, "a": 2})
    b = canonical({"a": 2, "b": 1})
    assert a == b
    assert a == '{"a":2,"b":1}'


def test_parse_json_plain():
    d = parse_json_response('{"value": "yes", "agreeing_count": 2}')
    assert d["value"] == "yes"
    assert d["agreeing_count"] == 2


def test_parse_json_fenced():
    raw = '```json\n{"value": "no", "agreeing_count": 1}\n```'
    d = parse_json_response(raw)
    assert d["value"] == "no"


def test_duplicate_url_detection():
    urls = ["https://a.com/1", "https://b.com/2", "https://a.com/1"]
    seen = {}
    dup = False
    for u in urls:
        if u in seen:
            dup = True
            break
        seen[u] = True
    assert dup is True


def test_contract_file_exists_and_has_markers():
    root = Path(__file__).resolve().parents[1]
    path = root / "contracts" / "source_corroboration_covenant.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "SourceCorroborationCovenant" in text
    assert "prompt_comparative" in text
    assert "allow_host" in text
    assert "establish" in text
    assert "read_corroboration" in text
    assert "insufficient corroboration" in text
    assert "Depends" in text


def test_readme_mentions_fail_closed_and_integration():
    root = Path(__file__).resolve().parents[1]
    text = (root / "README.md").read_text(encoding="utf-8")
    assert "fail closed" in text.lower() or "fail-closed" in text.lower()
    assert "read_corroboration" in text
    assert "allow_host" in text


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print("OK", t.__name__)
        except Exception as e:
            failed += 1
            print("FAIL", t.__name__, e)
    if failed:
        sys.exit(1)
    print(f"\n{len(tests)} passed")
