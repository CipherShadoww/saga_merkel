# Calendar Task Reproduction Report (SAGA, `gpt-4.1-mini`)

## 1. Objective

Reproduce the **Calendar task completion** behavior from the SAGA paper using a low-cost OpenAI model configuration (`gpt-4.1-mini`) and capture runtime/overhead observations from a successful local run.

## 2. Date and Environment

- Run date: **2026-05-10**
- Repo: local `saga` workspace
- Core services used:
  - CA file server (`http://127.0.0.1:8000`)
  - Provider (`https://127.0.0.1:5001`)
  - MongoDB (local)
- Python venv: `.venv`
- Script under test: [schedule_meeting.py](/Users/deepesh/Desktop/saga/experiments/schedule_meeting.py)

## 3. Notes About Local Code/Env Drift

During reproduction, the local codebase/environment had differences from paper-era assumptions:

1. [schedule_meeting.py](/Users/deepesh/Desktop/saga/experiments/schedule_meeting.py) expects `meeting_agent` (not `calendar_agent`) in user configs.
2. Local config ports conflicted with existing processes (for example `7000` occupied by macOS Control Center), so temporary configs were used on free ports.
3. `OpenAIServerModel` import path was missing in [base.py](/Users/deepesh/Desktop/saga/agent_backend/base.py), which caused model initialization failure and was fixed.
4. Missing runtime deps for this path were installed into `.venv`:
   - `openai`
   - `ddgs`

These are implementation/runtime fixes, not protocol changes.

## 4. Reproduction Configuration

Temporary configs were used to isolate a clean run:

- `/private/tmp/emma_meeting_tmp.yaml`
- `/private/tmp/raj_meeting_tmp.yaml`

Both use:

- `model_type: OpenAIServerModel`
- `model: gpt-4.1-mini-2025-04-14`
- calendar tool stack
- unique local ports (`7100`, `7104`)

Synthetic calendar seed data source:

- `experiments/data/emma/calendar.jsonl`
- `experiments/data/raj/calendar.jsonl`

## 5. Execution Steps (Performed)

1. Registered temp users and agents with SAGA user CLI.
2. Seeded temp calendar collections in MongoDB (`calendar` DB) for:
   - `emma.meeting.tmp@mail.com`
   - `raj.meeting.tmp@mail.com`
3. Started receiver:
   - `python schedule_meeting.py listen /private/tmp/raj_meeting_tmp.yaml`
4. Started initiator (timed):
   - `time -p python schedule_meeting.py query /private/tmp/emma_meeting_tmp.yaml /private/tmp/raj_meeting_tmp.yaml`

## 6. Observed Result

### Task Outcome

- Script verdict: `Success: True`
- End-to-end wall time (`query` command): **`real 25.66` seconds**

### Conversation/Behavior Highlights

- Agents negotiated a valid slot: **Tuesday, 2026-05-12, 09:00–09:30**
- Receiving agent created calendar event and returned `<TASK_FINISHED>`
- Token quota and invalidation flow executed as expected

### Overhead Signals (from logs)

- `agent:communication_proto_init`: `0.003549s`
- `agent:communication_proto_recv`: `0.004889s`
- `agent:llm_backend_init`: `6.611326s`
- `agent:llm_backend_recv`: `16.707615s`

Interpretation: protocol overhead remained very small relative to LLM runtime, consistent with the paper’s qualitative claim.

## 7. Post-Run Verification

Calendar DB checks confirmed the meeting record existed for both participants:

- `emma.meeting.tmp@mail.com`
- `raj.meeting.tmp@mail.com`

Meeting fields observed:

- `event`: `Meeting to discuss NDSS submission`
- `time_from`: `2026-05-12T09:00:00`
- `time_to`: `2026-05-12T09:30:00`

## 8. Comparison to Paper Table

This run reproduces the **calendar workflow behavior** and demonstrates low SAGA protocol overhead in practice with `gpt-4.1-mini`.  
It does **not** exactly reproduce the paper’s published numeric table values because:

- local code and environment differ from the original evaluation setup,
- temporary isolated users/ports were used,
- paper values were generated under a specific benchmark setup and geolocation configuration.

## 9. Artifacts

- Script: [schedule_meeting.py](/Users/deepesh/Desktop/saga/experiments/schedule_meeting.py)
- Overhead context: [measured_protocol_overhead.csv](/Users/deepesh/Desktop/saga/reports/measured_protocol_overhead.csv)
- Overhead comparison: [comparison_protocol_overhead.csv](/Users/deepesh/Desktop/saga/reports/comparison_protocol_overhead.csv)

