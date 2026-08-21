# Source Corroboration Covenant

A standalone GenLayer Intelligent Contract primitive that records a fact **only when independent public HTTPS sources corroborate it under consensus**.

Insufficient corroboration, fetch failure patterns that drag the ratio below threshold, host violations, and validator disagreement all **fail closed** — no state is written.

Other contracts and apps integrate via `read_corroboration` / `latest_corroboration`.

## Why GenLayer

A single backend reading one URL is a single point of trust. This covenant makes validators independently fetch the same caller-named sources, extract a plurality value, and agree on both the **value** and the **corroboration ratio**. The write only commits when the ratio clears a configured threshold.

Do **not** use this when a single signed API already returns a deterministic field you can verify with `strict_eq`. Use it when the answer lives in natural-language public pages and you need shared, replay-safe agreement that multiple sources support the same claim.

## Live deployment

Deploy on GenLayer Studionet (chain id `61999`) from [studio.genlayer.com](https://studio.genlayer.com) using `contracts/source_corroboration_covenant.py`.

After deploy:

1. Call `allow_host` for each evidence host (e.g. `example.com`, `reuters.com`).
2. Call `establish(question, "https://a/...,https://b/...")` with 2–8 allowlisted HTTPS URLs.
3. On success, `latest_corroboration()` returns the sealed fact JSON.
4. On insufficient corroboration the transaction reverts — state unchanged.

Record deploy tx, `establish` txs, and readbacks in `verification/studionet-e2e.md`.

## How it works

1. **Owner** registers allowed hosts (`allow_host`).
2. Anyone calls `establish(question, urls)` with 2–8 comma-separated HTTPS URLs.
3. Every URL host must be allowlisted; IP literals, localhost, and non-HTTPS are rejected.
4. Leader and validators independently fetch each source (fetch failures become non-agreeing evidence, not aborts).
5. Comparative consensus requires agreement on value meaning and `ratio_milli` within tolerance.
6. Deterministic threshold check: if `ratio_milli < threshold_milli`, the call **reverts** (fail-closed).
7. On success, a `Fact` is appended to an append-only archive.

## Public API

| Method | Type | Description |
|--------|------|-------------|
| `allow_host(host)` | write | Owner only — add HTTPS host to allowlist |
| `disallow_host(host)` | write | Owner only — disable host |
| `establish(question, urls)` | write | Corroborate and append fact (or revert) |
| `read_corroboration(fact_id)` | view | Integration JSON for one fact |
| `latest_corroboration()` | view | Integration JSON for latest fact |
| `count()` | view | Number of accepted facts |
| `is_host_allowed(host)` | view | Allowlist check |
| `get_threshold_milli()` / `get_tolerance_milli()` | view | Config |
| `get_owner()` | view | Owner address |

Constructor: `threshold_milli` (default 700), `tolerance_milli` (default 150).

## Consensus binding

| Field | Source | Stored | Validator check | Binding |
|-------|--------|--------|-----------------|---------|
| `value` | plurality extraction | yes | comparative meaning | comparative |
| `ratio_milli` | agreeing/total | yes | within tolerance | comparative + exact range |
| `accepted` | ratio ≥ threshold | derived then checked | must match | exact |
| `sources_count` | manifest length | yes | identical | exact |
| `manifest_hash` | canonical question+urls | yes | deterministic | deterministic |

No free-form rationale or model prose is stored.

## Fail-closed behavior

- Host not allowlisted → revert before fetch  
- Non-HTTPS / IP literal / localhost → revert  
- Duplicate URL → revert  
- Comparative disagreement → consensus failure (no write)  
- `ratio_milli < threshold` → revert after consensus (`insufficient corroboration`)  
- Empty question / wrong URL count → revert  

Fetch failure on a single source does **not** abort the transaction; that source simply does not count toward agreement.

## Integration pattern

```text
status_json = covenant.latest_corroboration()
# parse value + ratio_milli
# only release funds / update registry if ratio_milli >= your policy floor
