# Merkleized Interaction Ledger Report

Date: 2026-05-10  
Workspace: `/Users/deepesh/Desktop/saga`

## Scope

The live ledger at `reports/security/interaction_ledger.jsonl` was empty, so this report uses an isolated demo ledger:

- Ledger directory: `reports/security/demo_merkle/`
- Ledger file: `reports/security/demo_merkle/interaction_ledger.jsonl`
- Merkle roots file: `reports/security/demo_merkle/merkle_roots.jsonl`
- Batch size: `4`

This avoids polluting the real SAGA interaction ledger while still exercising the implemented hash-chain, Merkle tree, proof, integrity verification, and exposure tracing code.

## Command Run

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from shutil import rmtree
from saga.security.interaction_ledger import InteractionLedger
from saga.security.exposure_tracer import ExposureTracer

ledger_dir = Path('reports/security/demo_merkle')
if ledger_dir.exists():
    rmtree(ledger_dir)
ledger = InteractionLedger(ledger_dir=ledger_dir, batch_size=4)
entries = [
    ('agent_A', 'agent_B', 'session-001', 'A asks B for calendar availability', 1715342400.0),
    ('agent_B', 'agent_C', 'session-002', 'B delegates email lookup to C', 1715342460.0),
    ('agent_A', 'agent_D', 'session-003', 'A asks D for document context', 1715342520.0),
    ('agent_C', 'agent_E', 'session-004', 'C asks E to summarize attachment', 1715342580.0),
    ('agent_D', 'agent_F', 'session-005', 'D requests final citation check', 1715342640.0),
]
for source, dest, session, payload, ts in entries:
    ledger.append_interaction(source, dest, session, payload, timestamp=ts)

records = ledger.load_records()
hashes = [record['interaction_hash'] for record in records]
tree = ledger.build_merkle_tree(hashes)
integrity = ledger.verify_ledger_integrity()
proof_target = hashes[2]
proof = ledger.generate_merkle_proof(proof_target)
proof_valid = ledger.verify_merkle_proof(proof_target, proof['proof'], proof['merkle_root'])
exposure = ExposureTracer(ledger).propagate_compromise_alert('agent_A')
PY
```

## Interaction Records

| Index | Source | Destination | Session | Timestamp | Interaction Hash |
|---:|---|---|---|---:|---|
| 0 | `agent_A` | `agent_B` | `session-001` | `1715342400.0` | `d9624cf887c6d946e7f062986c81ffc2a96fece5193c66af83fd5bc6e03a8ad8` |
| 1 | `agent_B` | `agent_C` | `session-002` | `1715342460.0` | `5b62be6bb407783f457b0f0d7c8e3c1e60fd2ea6d42e2ef283c5608d9cac05e8` |
| 2 | `agent_A` | `agent_D` | `session-003` | `1715342520.0` | `4a68a9621f92a344837bc0bdf03161af825e7d18a0bb66351372873cd83902d3` |
| 3 | `agent_C` | `agent_E` | `session-004` | `1715342580.0` | `f7d5cfa9192897c21e9f7f0bf43c467826fd9b4cb83720cf472315a64f567c18` |
| 4 | `agent_D` | `agent_F` | `session-005` | `1715342640.0` | `178cda4c52a7aa2290d573f6a4d7652ce2b36807e8cab05146a65fe0cacdbe74` |

## Printed Merkle Tree

```text
Level 0 (5 nodes)
  [0] d9624cf887c6d946e7f062986c81ffc2a96fece5193c66af83fd5bc6e03a8ad8
  [1] 5b62be6bb407783f457b0f0d7c8e3c1e60fd2ea6d42e2ef283c5608d9cac05e8
  [2] 4a68a9621f92a344837bc0bdf03161af825e7d18a0bb66351372873cd83902d3
  [3] f7d5cfa9192897c21e9f7f0bf43c467826fd9b4cb83720cf472315a64f567c18
  [4] 178cda4c52a7aa2290d573f6a4d7652ce2b36807e8cab05146a65fe0cacdbe74

Level 1 (3 nodes)
  [0] acc04b0f97196ffdba24bde1233a64b2a764b93f11e586f31d681c6c9fa37a67
  [1] e38aa31bcd46651c78926a9567959ef73b4e288819e21a8767ce525fbf73e758
  [2] 1220f2e77c79d7d45e735d6f6fb8cd1aec1a556e04438981f54efa5066cd2ccd

Level 2 (2 nodes)
  [0] 1c6d13e25bef4b10cd8bda23d3904d61f782e6112c6bac24cc184ac650343d48
  [1] a03b93c44c87b6f51cff441935577aaa19978a8dc86bb6de370b1112121516f5

Level 3 (1 nodes)
  [0] 7a577cb82d865376996c80a03d5a48d4cabb9109583a8aa2d3b6c8773bcc46aa
```

## Merkle Roots

- Persisted batch root for records `0..3`: `1c6d13e25bef4b10cd8bda23d3904d61f782e6112c6bac24cc184ac650343d48`
- Current root over all 5 records: `7a577cb82d865376996c80a03d5a48d4cabb9109583a8aa2d3b6c8773bcc46aa`

## Merkle Proof

Target interaction hash:

```text
4a68a9621f92a344837bc0bdf03161af825e7d18a0bb66351372873cd83902d3
```

Proof:

```json
[
  {
    "position": "right",
    "hash": "f7d5cfa9192897c21e9f7f0bf43c467826fd9b4cb83720cf472315a64f567c18"
  },
  {
    "position": "left",
    "hash": "acc04b0f97196ffdba24bde1233a64b2a764b93f11e586f31d681c6c9fa37a67"
  }
]
```

Proof root:

```text
1c6d13e25bef4b10cd8bda23d3904d61f782e6112c6bac24cc184ac650343d48
```

Proof verification result: `True`

## Integrity Verification

```json
{
  "valid": true,
  "record_count": 5,
  "latest_hash": "178cda4c52a7aa2290d573f6a4d7652ce2b36807e8cab05146a65fe0cacdbe74",
  "merkle_root": "7a577cb82d865376996c80a03d5a48d4cabb9109583a8aa2d3b6c8773bcc46aa",
  "errors": []
}
```

Ledger Integrity: **VALID**

## Compromise Propagation Report

Compromised Agent: `agent_A`

Directly Exposed:

- `agent_B`
- `agent_D`

Indirectly Exposed:

- `agent_C`
- `agent_E`
- `agent_F`

Potentially Compromised:

- `agent_B`
- `agent_C`
- `agent_D`
- `agent_E`
- `agent_F`

Exposure Depth: `3`

Lineage:

```text
agent_A
├── agent_B
│   └── agent_C
│       └── agent_E
└── agent_D
    └── agent_F
```

