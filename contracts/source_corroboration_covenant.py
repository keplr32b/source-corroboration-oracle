# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Source Corroboration Covenant
=============================

A standalone GenLayer Intelligent Contract primitive that records a fact only
when independent public HTTPS sources corroborate it under consensus.

Design goals (Intelligent Contracts category bar):
  - Real consensus: comparative equivalence on structured (value, ratio, accepted)
  - Fail-closed: fetch failures degrade sources; insufficient corroboration reverts
    before any state write
  - Closed integration surface: read_corroboration / read_fact for other contracts
  - Append-only archive: accepted facts never overwritten
  - Host allowlist: only pre-registered HTTPS hosts may be used as evidence

This is a pure decision primitive. It does not move funds and does not claim
truth beyond "validators agreed these sources support this value at this ratio."
"""

from genlayer import *
import json
from dataclasses import dataclass


try:
    _UserError = gl.vm.UserError
except Exception:
    _UserError = Exception


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise _UserError(msg)


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


def _host_of(url: str) -> str:
    u = (url or "").strip().lower()
    require(u.startswith("https://"), "only https urls allowed")
    rest = u[8:]
    host = rest.split("/")[0].split("?")[0].split("#")[0]
    require(len(host) > 0, "empty host")
    require("@" not in host, "userinfo not allowed")
    require(not host.replace(".", "").isdigit(), "ip literal hosts rejected")
    require("localhost" not in host, "localhost rejected")
    require(not host.endswith(".local"), "local tld rejected")
    return host


_MILLI = 1000


@allow_storage
@dataclass
class Fact:
    question: str
    value: str
    ratio_milli: u256
    sources_count: u256
    agreeing_count: u256
    manifest_hash: str


class SourceCorroborationCovenant(gl.Contract):
    """
    Lifecycle per establish() call:
      - caller supplies question + comma-separated HTTPS urls (2..8)
      - every url host must already be on the allowlist (owner-registered)
      - validators independently fetch + extract plurality value + agreeing_count
      - comparative consensus on value meaning + ratio within tolerance
      - deterministic threshold check; on failure the tx reverts (fail-closed)
      - on success, Fact is appended; latest index updated
    """

    owner: Address
    allowed_hosts: TreeMap[str, bool]
    facts: DynArray[Fact]
    latest: u256
    threshold_milli: u256
    tolerance_milli: u256

    def __init__(self, threshold_milli: int = 700, tolerance_milli: int = 150):
        require(0 < threshold_milli <= 1000, "threshold out of range")
        require(0 < tolerance_milli <= 500, "tolerance out of range")
        self.owner = gl.message.sender_address
        self.threshold_milli = u256(threshold_milli)
        self.tolerance_milli = u256(tolerance_milli)
        self.latest = u256(0)

    @gl.public.write
    def allow_host(self, host: str) -> None:
        require(gl.message.sender_address == self.owner, "only owner")
        h = (host or "").strip().lower()
        require(len(h) > 0, "empty host")
        require("://" not in h, "pass host only, not url")
        require("@" not in h, "userinfo not allowed")
        require(not h.replace(".", "").isdigit(), "ip literal rejected")
        self.allowed_hosts[h] = True

    @gl.public.write
    def disallow_host(self, host: str) -> None:
        require(gl.message.sender_address == self.owner, "only owner")
        h = (host or "").strip().lower()
        if h in self.allowed_hosts:
            self.allowed_hosts[h] = False

    @gl.public.write
    def establish(self, question: str, urls: str) -> str:
        q = (question if isinstance(question, str) else "").strip()
        require(len(q) > 0, "empty question")
        require(len(q) <= 500, "question too long")

        raw_urls = urls if isinstance(urls, str) else ""
        url_list = [u.strip() for u in raw_urls.split(",") if u.strip()]
        require(2 <= len(url_list) <= 8, "need 2 to 8 comma-separated urls")

        seen = {}
        for u in url_list:
            host = _host_of(u)
            require(self.allowed_hosts.get(host, False) is True, "host not allowed: " + host)
            require(u not in seen, "duplicate url")
            seen[u] = True

        tol = int(self.tolerance_milli)
        threshold = int(self.threshold_milli)
        total = len(url_list)
        urls_for_nondet = list(url_list)

        def corroborate() -> str:
            parts = []
            for i, u in enumerate(urls_for_nondet):
                try:
                    content = gl.nondet.web.render(u, mode="text")
                    snippet = (content[:3000] if content else "[EMPTY PAGE]")
                except Exception as e:
                    snippet = ("[FETCH FAILED: " + str(e) + "]")[:240]
                parts.append("SOURCE " + str(i + 1) + " (" + u + "):\n---\n" + snippet + "\n---")
            sources_block = "\n\n".join(parts)

            prompt = (
                "You are corroborating a fact across INDEPENDENT web sources.\n\n"
                "QUESTION: " + q + "\n\n"
                "There are " + str(total) + " sources below. A source that failed to fetch "
                "or is empty supports NO value and must NOT count as agreeing.\n\n"
                + sources_block
                + "\n\n"
                "Determine the single short value the PLURALITY of sources supports "
                "as the answer (a short phrase, not a sentence). Then count how many "
                "of the " + str(total) + " sources actually support that plurality value.\n\n"
                "Return ONLY strict JSON, no markdown, no prose:\n"
                '{ "value": "<short plurality value>", "agreeing_count": <int> }'
            )
            raw = gl.nondet.exec_prompt(prompt)
            data = parse_json_response(raw)
            value = str(data.get("value", "")).strip()
            require(len(value) > 0, "empty value from model")
            require(len(value) <= 200, "value too long")
            agreeing = int(data.get("agreeing_count", 0))
            agreeing = max(0, min(total, agreeing))
            ratio_milli = (agreeing * _MILLI) // total
            accepted = ratio_milli >= threshold
            return canonical(
                {
                    "value": value,
                    "ratio_milli": ratio_milli,
                    "sources_count": total,
                    "agreeing_count": agreeing,
                    "accepted": accepted,
                }
            )

        principle = (
            "The two results corroborate the same question across the same fixed "
            "set of sources. They are EQUIVALENT if and only if: (1) the 'value' "
            "fields mean the same thing (synonyms and minor paraphrase allowed), "
            "(2) the 'ratio_milli' values differ by at most " + str(tol) + ", "
            "(3) 'sources_count' is identical, and (4) the 'accepted' fields are "
            "identical. If values disagree in meaning, ratios diverge beyond "
            "tolerance, or acceptance differs, they are NOT equivalent."
        )
        agreed = gl.eq_principle.prompt_comparative(corroborate, principle)
        parsed = json.loads(agreed)

        value = str(parsed["value"]).strip()
        ratio_milli = int(parsed["ratio_milli"])
        sources_count = int(parsed["sources_count"])
        agreeing_count = int(parsed.get("agreeing_count", 0))
        accepted = bool(parsed["accepted"])

        require(sources_count == total, "sources_count mismatch")
        require(accepted == (ratio_milli >= threshold), "acceptance does not match ratio")
        require(accepted, "insufficient corroboration across sources")

        manifest_hash = canonical({"question": q, "urls": url_list})

        self.facts.append(
            Fact(
                question=q,
                value=value,
                ratio_milli=u256(ratio_milli),
                sources_count=u256(sources_count),
                agreeing_count=u256(agreeing_count),
                manifest_hash=manifest_hash,
            )
        )
        self.latest = u256(len(self.facts) - 1)
        return value

    @gl.public.view
    def count(self) -> u256:
        return u256(len(self.facts))

    @gl.public.view
    def read_corroboration(self, fact_id: int) -> str:
        require(0 <= fact_id < len(self.facts), "no such fact")
        f = self.facts[fact_id]
        return canonical(
            {
                "question": f.question,
                "value": f.value,
                "ratio_milli": int(f.ratio_milli),
                "sources_count": int(f.sources_count),
                "agreeing_count": int(f.agreeing_count),
                "manifest_hash": f.manifest_hash,
                "status": "AGREED",
            }
        )

    @gl.public.view
    def latest_corroboration(self) -> str:
        require(len(self.facts) > 0, "no facts yet")
        return self.read_corroboration(int(self.latest))

    @gl.public.view
    def is_host_allowed(self, host: str) -> bool:
        h = (host or "").strip().lower()
        return self.allowed_hosts.get(h, False) is True

    @gl.public.view
    def get_threshold_milli(self) -> u256:
        return self.threshold_milli

    @gl.public.view
    def get_tolerance_milli(self) -> u256:
        return self.tolerance_milli

    @gl.public.view
    def get_owner(self) -> Address:
        return self.owner
