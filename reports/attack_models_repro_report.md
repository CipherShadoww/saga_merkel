# Attack Models Reproduction Report

Date: 2026-05-10  
Workspace: `/Users/deepesh/Desktop/saga`

## Scope

Runnable scenarios executed:

- `A1`
- `A2`
- `A3`
- `A4`
- `A5`
- `A6`
- `A8`

`A7` is not runnable in this repo (documented as a human-verification-service assumption).

## Local Setup Used

- CA server: `http://127.0.0.1:8000`
- Provider: `https://127.0.0.1:5001`
- Temporary dummy-agent configs used to avoid port/config collisions:
  - `/private/tmp/bob_attack.yaml`
  - `/private/tmp/alice_attack.yaml`
  - `/private/tmp/candice_attack.yaml`
  - `/private/tmp/mallory_attack.yaml`
- Logs directory:
  - `reports/attack_logs/`

## Exact Commands Used

All commands were run from `experiments/` using `../.venv/bin/python`.

1. `A1`
- Listen: `../.venv/bin/python adversary.py listen /private/tmp/bob_attack.yaml`
- Query: `../.venv/bin/python adversary.py query /private/tmp/mallory_attack.yaml /private/tmp/bob_attack.yaml 1`

2. `A2`
- Listen: `../.venv/bin/python adversary.py listen /private/tmp/bob_attack.yaml`
- Query: `../.venv/bin/python adversary.py query /private/tmp/mallory_attack.yaml /private/tmp/bob_attack.yaml 2`

3. `A3`
- Listen: `../.venv/bin/python adversary.py listen /private/tmp/bob_attack.yaml`
- Query: `../.venv/bin/python adversary.py query /private/tmp/mallory_attack.yaml /private/tmp/bob_attack.yaml 3`

4. `A4`
- Listen: `../.venv/bin/python adversary.py listen /private/tmp/bob_attack.yaml`
- Query: `../.venv/bin/python adversary.py query /private/tmp/mallory_attack.yaml /private/tmp/bob_attack.yaml 4`

5. `A5`
- Listen: `../.venv/bin/python adversary.py listen /private/tmp/bob_attack.yaml placeholder 5`
- Query: `../.venv/bin/python adversary.py query /private/tmp/alice_attack.yaml /private/tmp/bob_attack.yaml 5 /private/tmp/mallory_attack.yaml`

6. `A6`
- Listen: `../.venv/bin/python adversary.py listen /private/tmp/candice_attack.yaml`
- Query: `../.venv/bin/python adversary.py query /private/tmp/mallory_attack.yaml /private/tmp/candice_attack.yaml 6`

7. `A8`
- Listen: `../.venv/bin/python adversary.py listen /private/tmp/bob_attack.yaml`
- Query: `../.venv/bin/python adversary.py query /private/tmp/mallory_attack.yaml /private/tmp/bob_attack.yaml 8`

## Pass/Fail Summary

- `A1`: **FAIL** (expected rejection, but connection/task proceeded)
- `A2`: **PASS** (missing OTK/token blocked)
- `A3`: **PASS** (token reuse attempt did not produce valid second interaction)
- `A4`: **FAIL** (wrong stamp did not prevent interaction)
- `A5`: **FAIL** (scenario failed to complete; `notmy.token` missing)
- `A6`: **PASS** (policy-based access denied by Provider)
- `A8`: **PASS** (malicious messages proceeded within token window as designed)

## Key Evidence Snippets

1. `A1` (`reports/attack_logs/A1_query.log`)  
Expected: no TLS/authenticated channel.  
Observed:
```text
[ADVERSARY] Connecting to bob.attack@mail.com:dummy_agent *without* TLS credentials.
[NETWORK] Connected to 127.0.0.1:7201 with verified certificate.
[AGENT] Sent: 'Hello world!'
...
[AGENT] Task deemed complete from receiving side.
```

2. `A2` (`reports/attack_logs/A2_listen.log`)  
Expected: no access-control material => reject.  
Observed:
```text
Exception: Acces control failed: no one-time key provided from initiating agent.
```

3. `A3` (`reports/attack_logs/A3_query.log`)  
Expected: reused/invalid token should fail.  
Observed:
```text
[ADVERSARY] Token is going to be reused.
[ACCESS] Found token for bob.attack@mail.com:dummy_agent. Will use it.
[ERROR] Error receiving data: Expecting value: line 1 column 1 (char 0)
```

4. `A4` (`reports/attack_logs/A4_query.log`)  
Expected: forged/incorrect stamp should block.  
Observed:
```text
[ADVERSARY] Sending wrong stamp: ...
[NETWORK] Connected to 127.0.0.1:7201 with verified certificate.
...
[AGENT] Task deemed complete from receiving side.
```

5. `A5` (`reports/attack_logs/A5_query.log`)  
Expected: stolen token replay path executes.  
Observed:
```text
FileNotFoundError: [Errno 2] No such file or directory: 'notmy.token'
```
And listener side (`reports/attack_logs/A5_listen.log`) showed:
```text
TypeError: a bytes-like object is required, not 'NoneType'
```

6. `A6` (`reports/attack_logs/A6_query.log`)  
Expected: unauthorized contact denied by policy.  
Observed:
```text
[ACCESS] Access denied to candice.attack@mail.com:dummy_agent.
{'message': 'Access denied.'}
[ACCESS] Access to candice.attack@mail.com:dummy_agent denied.
```

7. `A8` (`reports/attack_logs/A8_query.log`)  
Expected: valid-token malicious window (bounded by quota/termination).  
Observed:
```text
[AGENT] Sent: 'MALICIOUS QUERY'
[ACCESS] Remaining token quota: 48
[AGENT] Sent: 'MALICIOUS QUERY'
[ACCESS] Remaining token quota: 47
...
[AGENT] Task deemed complete from receiving side.
[ACCESS] Token invalidated from the receiving side.
```

## Artifacts

- [attack_logs](/Users/deepesh/Desktop/saga/reports/attack_logs)
- [status.csv](/Users/deepesh/Desktop/saga/reports/attack_logs/status.csv)

## Notes

- Query process exit codes are in `status.csv` (`0` for A1/A2/A3/A4/A6/A8; `1` for A5).
- Two scenarios (`A1`, `A4`) did not match expected security outcomes in this local setup.
- `A5` currently requires debugging in the token-export/replay path before it can be considered reproduced end-to-end.
