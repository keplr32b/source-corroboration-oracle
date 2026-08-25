# Studionet E2E verification matrix

## Deployment

| Item | Value |
|------|--------|
| Network | Studionet (chain id 61999) |
| Contract address | [`0x00722cb74ec93f30572b01E6587A2F7Af86447DD`](https://explorer-studio.genlayer.com/address/0x00722cb74ec93f30572b01E6587A2F7Af86447DD) |
| Deploy tx | [`0xc804f9eba16d75f7e230a573161c8ee8e0ffdf1e04b164faaaf91c17181ad63a`](https://explorer-studio.genlayer.com/tx/0xc804f9eba16d75f7e230a573161c8ee8e0ffdf1e04b164faaaf91c17181ad63a) |
| Establish SUCCESS tx | [`0xd29bdcfd8ca803780a00ebc724721ea5f183e415cd00cda47e4f94ba5424a055`](https://explorer-studio.genlayer.com/tx/0xd29bdcfd8ca803780a00ebc724721ea5f183e415cd00cda47e4f94ba5424a055) |
| Deployer | `0xcA448B203A7a15e1a37778ac319F8379aE050091` |
| Status | FINALIZED · SUCCESS · Consensus Accepted |

## Scenarios executed

### 1. Allow hosts

| Step | Result |
|------|--------|
| `allow_host("example.com")` | SUCCESS · FINALIZED |
| `allow_host("example.org")` | SUCCESS · FINALIZED |
| `allow_host("www.example.org")` | SUCCESS · FINALIZED |

### 2. Fail-closed: host not allowed

| Step | Result |
|------|--------|
| `establish` with `www.example.org` before allow | ERROR · rollback `host not allowed: www.example.org` |

### 3. Fail-closed: insufficient corroboration

| Step | Result |
|------|--------|
| `establish` (hard question on example pages) | ERROR · `insufficient corroboration` · ratio_milli 0 · state unchanged |

### 4. Successful establish

| Step | Result |
|------|--------|
| Tx | [`0xd29bdcfd8ca803780a00ebc724721ea5f183e415cd00cda47e4f94ba5424a055`](https://explorer-studio.genlayer.com/tx/0xd29bdcfd8ca803780a00ebc724721ea5f183e415cd00cda47e4f94ba5424a055) |
| Question | What short name or title do these pages primarily display? |
| URLs | `https://example.com,https://www.example.org` |
| Execution | FINALIZED · SUCCESS |
| Output value | `Example Domain` |
| Equivalence | `accepted: true`, `agreeing_count: 2`, `ratio_milli: 1000`, `sources_count: 2` |

### 5. Read integration surface

| Call | Result |
|------|--------|
| `count()` | `1` |
| `latest_corroboration()` | `status: AGREED`, `value: Example Domain`, `ratio_milli: 1000`, `agreeing_count: 2` |

## Notes

- Fail-closed paths (unauthorized host, low corroboration) left storage empty until a successful establish.
- Successful path required comparative consensus and deterministic threshold check before append.
- Explorer: https://explorer-studio.genlayer.com/address/0x00722cb74ec93f30572b01E6587A2F7Af86447DD
