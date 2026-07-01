# Security

Local Agent Workbench is designed to run as a local-only, privacy-first application.

## Server Binding

Bind the backend to `127.0.0.1`.

Do not use:

```powershell
--host 0.0.0.0
```

Recommended backend startup:

```powershell
cd E:\codex\local-agent-workbench\backend
..\agentwork\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Do Not Commit

Do not commit:

- `.env`
- SQLite databases or journal files
- logs
- uploads
- `node_modules`
- `dist`
- `agentwork`
- `__pycache__`
- `*.pyc*`

## Local Model Boundary

Local model access is restricted to Ollama on localhost endpoints:

- `http://127.0.0.1:11434`
- `http://localhost:11434`

External APIs, web search, and MCP are currently disabled by default.

All model calls must go through Model Gateway. Agent Run / Step execution in the MVP is controlled and must not bypass Model Gateway or call tools directly.

## Logging

Do not log complete prompts or complete model responses. Model invocation logs may store only hashes, lengths, risk levels, blocked status, and findings summaries.

## Uploads

Uploaded files are quarantined. The application must not automatically parse uploaded files, unzip archives, execute files, or add uploaded file contents to prompts, memory, skills, or logs.

`/api/files/{file_id}/inspect` returns metadata only. `/api/files/{file_id}/parse-preview` is currently a blocked safety placeholder and does not read file contents.

## Reserved Provider And Tool Ideas

Provider profile, quota, usage, cost, OAuth, CLI-token, browser-cookie, and dashboard-fetch concepts are reserved as metadata only.

Current implementation does not:

- Store API keys.
- Start OAuth flows.
- Read browser cookies.
- Read CLI credentials.
- Fetch remote quota, cost, or usage dashboards.
- Call external model APIs.
- Execute desktop tools.
- Execute shell commands.
- Modify user files automatically.

## Approval Intents

Medium-risk local model calls should use `approval_id` bound to the current `prompt_hash`.

Approval records store only:

- provider/template/task ids
- prompt hash
- prompt length
- risk level
- findings summary
- redacted preview
- status and expiry timestamps

Approval records must not store full prompts or full model responses.
