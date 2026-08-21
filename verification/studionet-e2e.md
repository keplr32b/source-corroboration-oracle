# Studionet E2E verification matrix

Fill this file after deploying on GenLayer Studionet.

## Deployment

| Item | Value |
|------|--------|
| Network | Studionet (chain id 61999) |
| Contract address | _pending_ |
| Deploy tx | _pending_ |
| Deployer | _pending_ |
| Source SHA-256 | _pending_ |

## Scenarios

### 1. Allow hosts + successful establish

| Step | Tx / readback | Expected |
|------|----------------|----------|
| allow_host(example.com) | | SUCCESS |
| allow_host(example.org) | | SUCCESS |
| establish(question, two https urls) | | SUCCESS, value returned |
| latest_corroboration() | | status AGREED, ratio_milli ≥ threshold |

### 2. Host not allowed

| Step | Expected |
|------|----------|
| establish with url on non-allowed host | ERROR / revert |

### 3. Insufficient corroboration

| Step | Expected |
|------|----------|
| establish with sources that clearly disagree or are empty | ERROR `insufficient corroboration`, facts count unchanged |

### 4. Non-HTTPS rejected

| Step | Expected |
|------|----------|
| establish with `http://...` | ERROR |

### 5. Read integration surface

| Call | Expected |
|------|----------|
| count() | matches number of successful establish calls |
| read_corroboration(0) | JSON with question, value, ratio_milli, manifest_hash |

## Notes

- Always record FINALIZED + execution result + state readback.
- A successful tx is not enough; confirm storage via views.
