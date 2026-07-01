# Contributing

Thanks for considering a contribution to Local Agent Workbench.

## Project boundaries

This repository is a privacy-first local multi-agent workbench. Contributions must keep these defaults intact:

- No external model API calls by default.
- No web search by default.
- No MCP integration by default.
- No desktop automation execution by default.
- No automatic parsing of uploaded files.
- No full prompt or response logging.
- Local model calls are limited to the localhost Ollama allowlist.

## Local setup

Use the repository-local frontend dependencies and the repository-root Python virtual environment named `agentwork`.

Backend import check from `backend/`:

```powershell
..\agentwork\Scripts\python.exe -B -c "from app.main import app; print('ok')"
```

Smoke test from `backend/`:

```powershell
..\agentwork\Scripts\python.exe -B scripts\smoke_test.py
```

Frontend checks from `frontend/`:

```powershell
npm ci
npm run build
```

## Pull request checklist

- Explain changed files and behavior.
- State whether dependencies were added.
- State whether any real network access was introduced.
- Run backend import, smoke test, and frontend build when possible.
- Do not commit virtual environments, SQLite databases, logs, uploads, cache, `node_modules`, or `dist`.