# Architecture - Source Corroboration Covenant

## Problem

On-chain systems often need a shared answer to a question whose evidence lives on multiple public web pages. A single off-chain backend is a trust bottleneck. GenLayer validators can fetch and judge those pages independently; this contract turns that capability into a **reusable corroboration primitive**.

## State

- `owner` - allowlist admin  
- `allowed_hosts: TreeMap[str, bool]` - HTTPS hosts permitted as evidence  
- `facts: DynArray[Fact]` - append-only accepted corroborations  
- `latest` - index of last accepted fact  
- `threshold_milli` / `tolerance_milli` — acceptance and comparative tolerance  

`Fact` holds: question, value, ratio_milli, sources_count, agreeing_count, manifest_hash.

## Consensus pattern

**Comparative** (`prompt_comparative`): every validator re-fetches the same URL list and re-extracts `{value, agreeing_count → ratio_milli, accepted}`. Equivalence requires:

1. Same meaning of `value` (paraphrase allowed)  
2. `ratio_milli` within `tolerance_milli`  
3. Identical `sources_count` and `accepted`  

After consensus, a **deterministic** check enforces `accepted == (ratio_milli >= threshold_milli)` and requires `accepted` before append.

## Why not strict_eq alone?

LLM extraction of a short value from heterogeneous pages is not byte-stable across models. Comparative equivalence on meaning + numeric tolerance is the correct instrument. Threshold enforcement stays deterministic so low-confidence results never enter storage.

## Fail-closed matrix

| Condition | Effect |
|-----------|--------|
| Host not allowlisted | revert |
| Non-HTTPS / IP / localhost | revert |
| URL count not in [2, 8] | revert |
| Comparative disagreement | no commit |
| ratio below threshold | revert (`insufficient corroboration`) |
| Single source fetch fail | source counts as non-agreeing; continue |

## Integration surface

Downstream contracts should treat `read_corroboration` JSON as a **signal**, not legal truth:

- Gate registry listings on `ratio_milli`  
- Pause settlement until `latest_corroboration` matches an expected value family  
- Audit via `manifest_hash` (canonical question + url list)

## Differences from a thin "AI decides X" demo

- Host allowlist and URL hygiene  
- Explicit ratio + threshold, not a free verdict string alone  
- Fail-closed on low corroboration  
- Append-only archive with stable read API  
- Comparative consensus chosen and documented deliberately
