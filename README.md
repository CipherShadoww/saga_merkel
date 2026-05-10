# SAGA Runbook with Merkleized Interaction Ledger

This guide explains how to set up, run, and test this SAGA project from a fresh clone. It also explains the added Merkleized Agent Interaction Ledger extension, which records agent interactions in a tamper-evident hash chain and builds Merkle trees for efficient verification.

The commands below assume you are running them from the repository root.

```bash
cd saga
```

If your clone has a different folder name, replace `saga` with your local folder.

## What This Project Contains

SAGA is a security architecture for governing multi-agent systems. The original framework provides:

- user and agent registration
- cryptographic identities
- Provider-mediated agent discovery
- secure agent-to-agent communication
- contact policies and access-control tokens
- experiments for meeting scheduling, expense reports, blog writing, and attack models

This version also adds:

- `saga/security/interaction_ledger.py`: append-only interaction ledger
- `saga/security/merkle_tree.py`: Merkle tree, root, proof, and verification helpers
- `saga/security/exposure_tracer.py`: compromise propagation tracing
- `saga/security/integrity_verifier.py`: ledger integrity verification facade
- `reports/merkle_tree_report.md`: example report generated from the demo ledger

## Architecture Overview

SAGA has four main runtime pieces:

- **Certificate Authority (CA)**: creates and signs certificates used by users, agents, and the Provider.
- **Provider**: central registry service. It stores registered users, registered agents, contact policies, public cryptographic material, and one-time keys.
- **Users**: owners of agents. A user registers with the Provider, then registers one or more agents.
- **Agents**: autonomous software entities that can listen for incoming agent conversations or initiate conversations with other agents.

The normal flow is:

1. Start MongoDB.
2. Start the CA file server.
3. Start the Provider.
4. Register users.
5. Register agents for those users.
6. Seed local tool data.
7. Start one agent in `listen` mode.
8. Start another agent in `query` mode.
9. The initiating agent asks the Provider for access to the receiving agent.
10. The Provider checks the receiving agent's contact policy and returns connection material plus a one-time key.
11. The agents derive an access-control token and communicate directly.
12. The Merkleized ledger records outbound interaction messages.

## Repository Layout

Important files and directories:

```text
agent_backend/                    Local LLM-agent wrapper and tools
agent_backend/tools/              Calendar, email, and document tools
experiments/                      Runnable task and attack-model scripts
experiments/data/                 Synthetic seed data for local tools
proofs/                           ProVerif and Verifpal formal models
reports/                          Local generated reports and experiment logs
saga/agent.py                     Core SAGA Agent implementation
saga/ca/CA.py                     Certificate authority logic
saga/provider/provider.py         Provider HTTPS service
saga/user/user.py                 User and agent registration CLI
saga/common/crypto.py             Cryptographic helper functions
saga/common/contact_policy.py     Agent contact policy matching
saga/security/                    Merkleized interaction ledger extension
user_configs/                     Example user and agent configurations
config.yaml                       Active runtime configuration
config_local.yaml                 Localhost runtime configuration
```

## Main Concepts

### User

A user owns one or more agents. In the example configs, users include Alice, Bob, Emma, Raj, Candice, and Mallory.

Each user config contains:

```yaml
name: Alice Smith
email: alice_final@mail.com
passwd: "alice"
agents:
  - name: meeting_agent
    description: "Meeting coordinator"
    endpoint:
      ip: 127.0.0.1
      port: 9010
      device_name: "lambda"
    contact_rulebook:
      - pattern: "*"
        budget: 100
    num_one_time_keys: 5
    local_agent_config:
      model_type: "huggingface"
      model: "Qwen/Qwen2.5-Coder-32B-Instruct"
      tools: [email, calendar]
```

### Agent ID

An agent ID has this form:

```text
user_email:agent_name
```

Example:

```text
alice_final@mail.com:meeting_agent
```

### Contact Policy

Each agent has a contact rulebook. It decides which other agents can request access.

Allow everyone with budget 100:

```yaml
contact_rulebook:
  - pattern: "*"
    budget: 100
```

Allow only Bob's meeting agent:

```yaml
contact_rulebook:
  - pattern: "bob_final@mail.com:meeting_agent"
    budget: 10
```

Block a specific agent:

```yaml
contact_rulebook:
  - pattern: "mallory@mail.com:dummy_agent"
    budget: -1
```

The budget controls how many one-time key authorizations can be issued for matching agents.

### Agent Manifest

After an agent is registered, SAGA creates a working directory under:

```text
saga/user/<agent_id>/
```

Example:

```text
saga/user/alice_final@mail.com:meeting_agent/
```

The most important file is:

```text
agent.json
```

It contains the agent's registered metadata, certificate, public and private keys, access-control keys, one-time keys, contact rulebook, and Provider stamp. The `Agent` class reads this file when starting a listener or initiating a query.

## System Requirements

Install these first:

- Python 3.10 or newer
- Git
- MongoDB, or Docker for running MongoDB
- macOS, Linux, or WSL on Windows

Check Python:

```bash
python3 --version
```

You should see Python `3.10.x` or newer.

## Step 1: Clone the Repository

```bash
git clone https://github.com/gsiros/saga.git
cd saga
```

If you are using your fork:

```bash
git clone https://github.com/YOUR_USERNAME/saga.git
cd saga
```

## Step 2: Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## Step 3: Install Python Dependencies

Install the package in editable mode:

```bash
pip install -e .
```

Install the requirements file as well:

```bash
pip install -r requirements.txt
```

Quick import check:

```bash
python - <<'PY'
import saga
from saga.security.interaction_ledger import InteractionLedger
print("SAGA import OK")
print("Merkle ledger import OK")
PY
```

## Step 4: Start MongoDB

SAGA uses MongoDB for Provider state and local tool data.

### Option A: Start MongoDB with Docker

This is the easiest portable option.

```bash
docker run --name saga-mongo -p 27017:27017 -d mongo:7
```

Check that it is running:

```bash
docker ps
```

If you already created the container earlier, start it with:

```bash
docker start saga-mongo
```

### Option B: Start MongoDB on macOS with Homebrew

If MongoDB is installed through Homebrew:

```bash
brew services start mongodb-community
```

Check:

```bash
brew services list | grep mongodb
```

### Option C: Start MongoDB Manually

If `mongod` is installed directly:

```bash
mongod --dbpath /tmp/saga-mongo
```

Keep this terminal open.

## Step 5: Use Local Configuration

The repo includes a local configuration that points everything to `127.0.0.1`.

```bash
cp config_local.yaml config.yaml
```

Confirm the important endpoints:

```bash
python - <<'PY'
import yaml
with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
print("CA endpoint:", cfg["ca"]["endpoint"])
print("Provider endpoint:", cfg["provider"]["endpoint"])
print("Tool Mongo URI:", cfg["mongo_uri_for_tools"])
PY
```

Expected values:

```text
CA endpoint: http://127.0.0.1:8000
Provider endpoint: https://127.0.0.1:5001
Tool Mongo URI: mongodb://127.0.0.1:27017/saga_tools
```

## Step 6: Generate CA Credentials

From the repo root:

```bash
python generate_credentials.py ca saga/ca/
```

This creates CA files under `saga/ca/`.

## Step 7: Start the CA File Server

Open a new terminal.

```bash
cd /path/to/saga
source .venv/bin/activate
cd saga/ca
python -m http.server 8000
```

Keep this terminal open.

Expected output looks like:

```text
Serving HTTP on :: port 8000 ...
```

## Step 8: Start the Provider

Open another new terminal.

```bash
cd /path/to/saga
source .venv/bin/activate
cd saga/provider
python provider.py
```

Keep this terminal open.

Expected endpoint:

```text
https://127.0.0.1:5001
```

## Step 9: Register Users and Agents

Open another terminal at the repo root.

```bash
cd /path/to/saga
source .venv/bin/activate
```

Register Alice:

```bash
cd saga/user
python user.py --register --register-agents --uconfig ../../user_configs/alice.yaml
cd ../..
```

Register Bob:

```bash
cd saga/user
python user.py --register --register-agents --uconfig ../../user_configs/bob.yaml
cd ../..
```

If you want to run attack model experiments, also register Mallory and Candice:

```bash
cd saga/user
python user.py --register --register-agents --uconfig ../../user_configs/mallory.yaml
python user.py --register --register-agents --uconfig ../../user_configs/candice.yaml
cd ../..
```

If you get an "already exists" error, that user or agent is already registered in MongoDB. You can either keep going, use a new email/port in the YAML file, or clear the MongoDB database.

Clear local MongoDB databases only if you want a clean reset:

```bash
python - <<'PY'
from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017")
client.drop_database("saga")
client.drop_database("saga_tools")
print("Dropped saga and saga_tools databases")
PY
```

Then register users again.

### Interactive Registration Mode

For beginners, the config-file path above is easiest. SAGA also supports interactive registration.

```bash
cd saga/user
python user.py --interactive
```

You will see a CLI menu similar to:

```text
======= SAGA User Client CLI =======
1. Register
2. Login
3. Register Agent
4. Exit
```

Use this mode if you want to type the email, password, agent name, IP, port, and contact rulebook manually.

Example contact rulebook input:

```json
[{"pattern":"*", "budget":10}]
```

### Register User and Agents Separately

Register only the user:

```bash
cd saga/user
python user.py --register --uconfig ../../user_configs/alice.yaml
cd ../..
```

Register only that user's agents:

```bash
cd saga/user
python user.py --register-agents --uconfig ../../user_configs/alice.yaml
cd ../..
```

Register both at once:

```bash
cd saga/user
python user.py --register --register-agents --uconfig ../../user_configs/alice.yaml
cd ../..
```

### Check Generated Agent Files

After registration, check the agent working directory:

```bash
find saga/user -maxdepth 2 -name agent.json -print
```

Print one manifest in readable JSON:

```bash
python - <<'PY'
import json
from pathlib import Path

for path in Path("saga/user").glob("*:*/agent.json"):
    print("Manifest:", path)
    print(json.dumps(json.loads(path.read_text()), indent=2)[:2000])
    break
PY
```

You should see fields like:

```text
aid
device
IP
port
agent_cert
pac
sac
otks
sotks
contact_rulebook
stamp
```

## Step 10: Seed Tool Data

From the repo root:

```bash
cd experiments
python seed_tool_data.py
cd ..
```

## Step 11: Run a Basic Agent Task

Some experiments use LLM backends. If your selected configs use OpenAI models, set:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
```

For the meeting scheduling task, start the receiving agent first.

Terminal 1:

```bash
cd /path/to/saga
source .venv/bin/activate
cd experiments
python schedule_meeting.py listen ../user_configs/bob.yaml
```

Terminal 2:

```bash
cd /path/to/saga
source .venv/bin/activate
cd experiments
python schedule_meeting.py query ../user_configs/alice.yaml ../user_configs/bob.yaml
```

When agents send messages, the Merkleized ledger extension records outbound interactions automatically.

Default ledger paths:

```text
reports/security/interaction_ledger.jsonl
reports/security/merkle_roots.jsonl
```

## Core Agent Communication API

Most users will run the experiment scripts, but the underlying API is small.

### Start an Agent Listener

```python
from saga.agent import Agent, get_agent_material
from agent_backend.base import get_agent
from saga.config import UserConfig, get_index_of_agent, ROOT_DIR
import os

config = UserConfig.load("user_configs/alice.yaml", drop_extra_fields=True)
agent_index = get_index_of_agent(config, "meeting_agent")
local_agent = get_agent(config, config.agents[agent_index].local_agent_config)

workdir = os.path.join(ROOT_DIR, f"user/{config.email}:{config.agents[agent_index].name}/")
material = get_agent_material(workdir)

agent = Agent(workdir=workdir, material=material, local_agent=local_agent)
agent.listen()
```

### Connect to Another Agent

```python
from saga.agent import Agent, get_agent_material
from agent_backend.base import get_agent
from saga.config import UserConfig, get_index_of_agent, ROOT_DIR
import os

config = UserConfig.load("user_configs/bob.yaml", drop_extra_fields=True)
agent_index = get_index_of_agent(config, "meeting_agent")
local_agent = get_agent(config, config.agents[agent_index].local_agent_config)

workdir = os.path.join(ROOT_DIR, f"user/{config.email}:{config.agents[agent_index].name}/")
material = get_agent_material(workdir)

agent = Agent(workdir=workdir, material=material, local_agent=local_agent)
agent.connect("alice_final@mail.com:meeting_agent", "Hello, can we schedule a meeting?")
```

### Local Agent Interface

Custom agent backends must inherit from `saga.local_agent.LocalAgent` and implement:

```python
def run(self, query: str, initiating_agent: bool, agent_instance=None, **kwargs):
    return agent_instance, "response text"
```

The SAGA wrapper expects:

- `query`: incoming text from another agent
- `initiating_agent`: whether this agent started the task
- `agent_instance`: optional previous backend state
- return value: `(agent_instance, response_text)`

The built-in implementation in `agent_backend/base.py` wraps `smolagents` and exposes email, calendar, document, and reimbursement tools.

## Running the Included Experiments

The paper's three task experiments live under `experiments/`.

| File | What It Does |
|---|---|
| `schedule_meeting.py` | Two meeting agents coordinate a common time and calendar invite. |
| `expense_report.py` | Email agents gather expense information and submit a report. |
| `create_blogpost.py` | Writing agents collaborate using stored document context. |

General pattern:

1. Start the receiving agent in one terminal.
2. Start the initiating agent in another terminal.

Template:

```bash
cd experiments
python TASK_FILE.py listen ../user_configs/RECEIVER.yaml
```

Then:

```bash
cd experiments
python TASK_FILE.py query ../user_configs/INITIATOR.yaml ../user_configs/RECEIVER.yaml
```

### Meeting Scheduling

Terminal 1:

```bash
cd experiments
python schedule_meeting.py listen ../user_configs/bob.yaml
```

Terminal 2:

```bash
cd experiments
python schedule_meeting.py query ../user_configs/alice.yaml ../user_configs/bob.yaml
```

### Expense Report

Terminal 1:

```bash
cd experiments
python expense_report.py listen ../user_configs/raj.yaml
```

Terminal 2:

```bash
cd experiments
python expense_report.py query ../user_configs/emma.yaml ../user_configs/raj.yaml
```

### Collaborative Blogpost

Terminal 1:

```bash
cd experiments
python create_blogpost.py listen ../user_configs/raj.yaml
```

Terminal 2:

```bash
cd experiments
python create_blogpost.py query ../user_configs/emma.yaml ../user_configs/raj.yaml
```

If an experiment says an agent name is missing, inspect the corresponding `user_configs/*.yaml`. The script may expect a specific agent name such as `meeting_agent`, `email_agent`, `writing_agent`, or `dummy_agent`.

## Running Agents Without the Full SAGA Protocol

You can also use the local LLM/tool backend without SAGA networking.

```python
from agent_backend.base import get_agent
from saga.config import UserConfig

config = UserConfig.load("user_configs/alice.yaml", drop_extra_fields=True)
agent_config = config.agents[0]

local_agent = get_agent(config, agent_config.local_agent_config)

agent_instance, response = local_agent.run(
    "Check my upcoming events.",
    initiating_agent=True,
    agent_instance=None,
)

print(response)
```

This is useful when debugging tool behavior before running the full Provider/Agent protocol.

## Merkleized Interaction Ledger

The ledger is append-only JSONL. Each record has:

```json
{
  "interaction_id": "uuid",
  "timestamp": 1715342400.0,
  "source_agent": "agent_A",
  "destination_agent": "agent_B",
  "session_id": "session-001",
  "payload_digest": "sha256(payload)",
  "previous_hash": "previous interaction hash",
  "interaction_hash": "sha256(record fields)"
}
```

Every record links to the previous record hash. This detects modification, deletion, and reordering. Every batch of interactions also gets a Merkle root for efficient proof verification.

Default batch size:

```text
100
```

Override ledger directory:

```bash
export SAGA_LEDGER_DIR="$PWD/reports/security"
```

Override Merkle batch size:

```bash
export SAGA_LEDGER_BATCH_SIZE=10
```

## Run the Merkle Demo

This command creates a demo ledger separate from the live ledger, appends 5 interactions, builds a Merkle tree, verifies a proof, checks integrity, and traces exposure from `agent_A`.

```bash
python - <<'PY'
from pathlib import Path
from shutil import rmtree
from saga.security.interaction_ledger import InteractionLedger
from saga.security.exposure_tracer import ExposureTracer

ledger_dir = Path("reports/security/demo_merkle")
if ledger_dir.exists():
    rmtree(ledger_dir)

ledger = InteractionLedger(ledger_dir=ledger_dir, batch_size=4)

entries = [
    ("agent_A", "agent_B", "session-001", "A asks B for calendar availability", 1715342400.0),
    ("agent_B", "agent_C", "session-002", "B delegates email lookup to C", 1715342460.0),
    ("agent_A", "agent_D", "session-003", "A asks D for document context", 1715342520.0),
    ("agent_C", "agent_E", "session-004", "C asks E to summarize attachment", 1715342580.0),
    ("agent_D", "agent_F", "session-005", "D requests final citation check", 1715342640.0),
]

for source, dest, session, payload, timestamp in entries:
    ledger.append_interaction(source, dest, session, payload, timestamp=timestamp)

records = ledger.load_records()
hashes = [record["interaction_hash"] for record in records]
tree = ledger.build_merkle_tree(hashes)

print("Ledger directory:", ledger_dir)
print("Record count:", len(records))
print("Current Merkle root:", ledger.generate_merkle_root())
print("Integrity:", ledger.verify_ledger_integrity())

print("\nMerkle tree:")
for level_index, level in enumerate(tree):
    print(f"Level {level_index} ({len(level)} nodes)")
    for node_index, node in enumerate(level):
        print(f"  [{node_index}] {node}")

target_hash = hashes[2]
proof = ledger.generate_merkle_proof(target_hash)
print("\nProof target:", target_hash)
print("Proof:", proof)
print("Proof valid:", ledger.verify_merkle_proof(target_hash, proof["proof"], proof["merkle_root"]))

report = ExposureTracer(ledger).propagate_compromise_alert("agent_A")
print("\nCompromise report:")
print("Compromised:", report["compromised_agent"])
print("Directly exposed:", report["directly_exposed"])
print("Indirectly exposed:", report["indirectly_exposed"])
print("Potentially compromised:", report["potentially_compromised_agents"])
print("Exposure depth:", report["exposure_depth"])
print("Ledger integrity:", report["ledger_integrity"])
PY
```

Expected high-level output:

```text
Record count: 5
Current Merkle root: 7a577cb82d865376996c80a03d5a48d4cabb9109583a8aa2d3b6c8773bcc46aa
Proof valid: True
Directly exposed: ['agent_B', 'agent_D']
Indirectly exposed: ['agent_C', 'agent_E', 'agent_F']
Ledger integrity: VALID
```

## Print Only the Merkle Tree

After running the demo:

```bash
python - <<'PY'
from saga.security.interaction_ledger import InteractionLedger

ledger = InteractionLedger(ledger_dir="reports/security/demo_merkle", batch_size=4)
records = ledger.load_records()
hashes = [record["interaction_hash"] for record in records]
tree = ledger.build_merkle_tree(hashes)

for level_index, level in enumerate(tree):
    print(f"Level {level_index} ({len(level)} nodes)")
    for node_index, node in enumerate(level):
        print(f"  [{node_index}] {node}")
PY
```

## Print Merkle Roots

```bash
cat reports/security/demo_merkle/merkle_roots.jsonl
```

Pretty print:

```bash
python -m json.tool reports/security/demo_merkle/merkle_roots.jsonl
```

If `python -m json.tool` fails on JSONL, use:

```bash
python - <<'PY'
import json
from pathlib import Path

for line in Path("reports/security/demo_merkle/merkle_roots.jsonl").read_text().splitlines():
    print(json.dumps(json.loads(line), indent=2))
PY
```

## Verify Ledger Integrity

For the demo ledger:

```bash
python - <<'PY'
import json
from saga.security.interaction_ledger import InteractionLedger

ledger = InteractionLedger(ledger_dir="reports/security/demo_merkle", batch_size=4)
print(json.dumps(ledger.verify_ledger_integrity(), indent=2))
PY
```

For the live ledger:

```bash
python - <<'PY'
import json
from saga.security.interaction_ledger import InteractionLedger

ledger = InteractionLedger()
print(json.dumps(ledger.verify_ledger_integrity(), indent=2))
PY
```

Expected valid result:

```json
{
  "valid": true,
  "errors": []
}
```

## Generate and Verify a Merkle Proof

This verifies record index `2` in the demo ledger:

```bash
python - <<'PY'
import json
from saga.security.interaction_ledger import InteractionLedger

ledger = InteractionLedger(ledger_dir="reports/security/demo_merkle", batch_size=4)
records = ledger.load_records()
target = records[2]["interaction_hash"]
proof = ledger.generate_merkle_proof(target)
valid = ledger.verify_merkle_proof(target, proof["proof"], proof["merkle_root"])

print("Target:", target)
print("Proof:")
print(json.dumps(proof, indent=2))
print("Valid:", valid)
PY
```

Expected:

```text
Valid: True
```

## Trace Exposure from a Compromised Agent

Demo ledger:

```bash
python - <<'PY'
import json
from saga.security.interaction_ledger import InteractionLedger
from saga.security.exposure_tracer import ExposureTracer

ledger = InteractionLedger(ledger_dir="reports/security/demo_merkle", batch_size=4)
report = ExposureTracer(ledger).propagate_compromise_alert("agent_A")
print(json.dumps(report, indent=2))
PY
```

Live ledger:

```bash
python - <<'PY'
import json
from saga.security.exposure_tracer import propagate_compromise_alert

report = propagate_compromise_alert("alice@mail.com:meeting_agent")
print(json.dumps(report, indent=2))
PY
```

Replace `alice@mail.com:meeting_agent` with the real agent ID you want to investigate.

## List Interaction Neighbors

```bash
python - <<'PY'
from saga.security.interaction_ledger import InteractionLedger
from saga.security.exposure_tracer import ExposureTracer

ledger = InteractionLedger(ledger_dir="reports/security/demo_merkle", batch_size=4)
neighbors = ExposureTracer(ledger).get_interaction_neighbors("agent_A")
for neighbor in neighbors:
    print(neighbor)
PY
```

Expected:

```text
{'agent_id': 'agent_B', ...}
{'agent_id': 'agent_D', ...}
```

## Tamper Test

This test copies the demo ledger, modifies one record, and verifies that integrity fails.

```bash
cp -R reports/security/demo_merkle reports/security/demo_merkle_tampered
```

Modify the first ledger record:

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("reports/security/demo_merkle_tampered/interaction_ledger.jsonl")
lines = path.read_text().splitlines()
record = json.loads(lines[0])
record["destination_agent"] = "agent_ATTACKER"
lines[0] = json.dumps(record, sort_keys=True, separators=(",", ":"))
path.write_text("\n".join(lines) + "\n")
print("Tampered first record")
PY
```

Verify:

```bash
python - <<'PY'
import json
from saga.security.interaction_ledger import InteractionLedger

ledger = InteractionLedger(ledger_dir="reports/security/demo_merkle_tampered", batch_size=4)
print(json.dumps(ledger.verify_ledger_integrity(), indent=2))
PY
```

Expected:

```json
{
  "valid": false
}
```

The error list should include a hash mismatch and/or chain/root mismatch.

## Regenerate the Merkle Report

The repository includes:

```text
reports/merkle_tree_report.md
```

To regenerate a similar report manually, run the Merkle demo command above and copy the printed tree, proof, integrity report, and exposure report into a markdown file.

## Attack Model Experiments

The attack model runner lives in `experiments/adversary.py`.

Attack models use agents named `dummy_agent`. Make sure the relevant configs have a `dummy_agent` entry and that those agents were registered.

General pattern:

```bash
cd experiments
python adversary.py listen ../user_configs/VICTIM.yaml
```

Then, in another terminal:

```bash
cd experiments
python adversary.py query ../user_configs/ATTACKER.yaml ../user_configs/VICTIM.yaml ATTACK_ID
```

### A1: No TLS Credentials

Expected idea: an adversarial agent tries to contact a victim without proper TLS credentials.

Terminal 1:

```bash
cd experiments
python adversary.py listen ../user_configs/bob.yaml
```

Terminal 2:

```bash
cd experiments
python adversary.py query ../user_configs/mallory.yaml ../user_configs/bob.yaml 1
```

### A2: No Access-Control Credential

Expected idea: the adversary connects without a valid one-time key or token.

Terminal 1:

```bash
cd /path/to/saga
source .venv/bin/activate
cd experiments
python adversary.py listen ../user_configs/bob.yaml
```

Terminal 2:

```bash
cd /path/to/saga
source .venv/bin/activate
cd experiments
python adversary.py query ../user_configs/mallory.yaml ../user_configs/bob.yaml 2
```

### A3: Expired or Reused Token

Expected idea: the adversary tries to reuse an invalid token.

Terminal 1:

```bash
cd experiments
python adversary.py listen ../user_configs/bob.yaml
```

Terminal 2:

```bash
cd experiments
python adversary.py query ../user_configs/mallory.yaml ../user_configs/bob.yaml 3
```

### A4: Invalid Provider Stamp

Expected idea: the adversary sends a wrong Provider stamp.

Terminal 1:

```bash
cd experiments
python adversary.py listen ../user_configs/bob.yaml
```

Terminal 2:

```bash
cd experiments
python adversary.py query ../user_configs/mallory.yaml ../user_configs/bob.yaml 4
```

### A5: Stolen Token Replay

Expected idea: one agent obtains a token and another adversarial agent attempts to reuse it.

Terminal 1:

```bash
cd experiments
python adversary.py listen ../user_configs/bob.yaml placeholder 5
```

Terminal 2:

```bash
cd experiments
python adversary.py query ../user_configs/alice.yaml ../user_configs/bob.yaml 5 ../user_configs/mallory.yaml
```

### A6: Contact Policy Denial

Expected idea: the Provider denies access because the target agent's contact policy does not authorize the initiator.

Terminal 1:

```bash
cd experiments
python adversary.py listen ../user_configs/candice.yaml
```

Terminal 2:

```bash
cd experiments
python adversary.py query ../user_configs/mallory.yaml ../user_configs/candice.yaml 6
```

### A7: Human Verification Assumption

`A7` is not a runnable local script in this repository. It is handled by the system assumption that user registration is protected by a human-verification service.

### A8: Valid Token Malicious Window

Expected idea: an adversarial agent has a valid token, so communication is allowed only within token quota and lifetime.

Terminal 1:

```bash
cd experiments
python adversary.py listen ../user_configs/bob.yaml
```

Terminal 2:

```bash
cd experiments
python adversary.py query ../user_configs/mallory.yaml ../user_configs/bob.yaml 8
```

Available runnable adversary IDs:

```text
1, 2, 3, 4, 5, 6, 8
```

After running attack models, check generated logs if you redirect output to files:

```bash
ls reports/attack_logs
```

This repository also includes an example reproduction report:

```text
reports/attack_models_repro_report.md
```

## Protocol Overhead Reports

The `reports/` directory contains scripts and CSV/PNG artifacts for protocol overhead measurements.

Useful files:

```text
reports/protocol_overhead.py
reports/measured_protocol_overhead.py
reports/comparison_protocol_overhead.py
reports/protocol_overhead.csv
reports/measured_protocol_overhead.csv
reports/comparison_protocol_overhead.csv
reports/protocol_overhead.png
reports/measured_protocol_overhead.png
reports/comparison_protocol_overhead.png
```

Run one report script:

```bash
python reports/protocol_overhead.py
```

Run measured overhead processing:

```bash
python reports/measured_protocol_overhead.py
```

Run comparison plot generation:

```bash
python reports/comparison_protocol_overhead.py
```

If a plotting script fails, install plotting dependencies such as `matplotlib` and `pandas`:

```bash
pip install matplotlib pandas
```

## Formal Verification Artifacts

Formal protocol models are stored in:

```text
proofs/proverif/
proofs/verifpal/
```

Examples:

```text
proofs/proverif/agent_communication.pv
proofs/proverif/registration.pv
proofs/verifpal/agent_communication.vp
proofs/verifpal/registration.vp
```

If you have ProVerif installed:

```bash
proverif proofs/proverif/agent_communication.pv
```

If you have Verifpal installed:

```bash
verifpal verify proofs/verifpal/agent_communication.vp
```

These tools are optional for running the local Python demo, but useful if you want to inspect the formal models.

## Useful Files

```text
README.md                                      Original project README
README_RUNBOOK.md                              This step-by-step guide
saga/security/interaction_ledger.py            Ledger and integrity logic
saga/security/merkle_tree.py                    Merkle tree helpers
saga/security/exposure_tracer.py                Exposure graph traversal
saga/security/integrity_verifier.py             Integrity facade
saga/agent.py                                  Agent communication integration
reports/security/interaction_ledger.jsonl       Live interaction ledger
reports/security/merkle_roots.jsonl             Live Merkle roots
reports/security/demo_merkle/                   Demo ledger artifacts
reports/merkle_tree_report.md                   Example generated report
```

## Troubleshooting

### `ModuleNotFoundError: No module named saga`

Activate the virtual environment and install the project:

```bash
source .venv/bin/activate
pip install -e .
```

### Provider Cannot Connect to MongoDB

Make sure MongoDB is running:

```bash
docker ps
```

or:

```bash
brew services list | grep mongodb
```

### Agent Port Already in Use

Change the port in the relevant `user_configs/*.yaml` file. For example:

```yaml
endpoint:
  ip: 127.0.0.1
  port: 9015
```

Then re-register the agent or reset MongoDB.

### User or Agent Already Exists

Use a different email or agent port, or reset local MongoDB:

```bash
python - <<'PY'
from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017")
client.drop_database("saga")
client.drop_database("saga_tools")
print("Reset complete")
PY
```

### Live Ledger Is Empty

The live ledger only records actual agent messages. Run an experiment first, or use the demo ledger commands.

Check live ledger:

```bash
wc -l reports/security/interaction_ledger.jsonl
```

Check demo ledger:

```bash
wc -l reports/security/demo_merkle/interaction_ledger.jsonl
```
