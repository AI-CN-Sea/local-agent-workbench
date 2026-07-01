# AGENTS.md

This project is a privacy-first local multi-agent workbench.

## Default Boundaries

- External APIs are disabled by default.
- Web search is disabled by default.
- MCP is disabled by default.
- Automatic file parsing is disabled by default.
- Uploaded file contents must not be read, parsed, copied into prompts, written to memory, written to skills, or logged.
- All model calls must go through the Model Gateway.
- All network behavior must go through the Network Gateway.
- Full prompts and full model responses must never be saved to logs.

## Required Reporting

After every development round, report:

- Modified files.
- Test commands.
- Whether dependencies were added.
- Whether any real network behavior exists.

## File Safety

Do not delete user files, database backups, virtual environments, uploads, logs, or generated artifacts unless the user explicitly confirms the deletion.

Do not delete `agentwork/`.

Do not commit or include:

- `.env`
- databases or journals
- logs
- caches
- virtual environments
- `node_modules`
- `dist`
- uploads

## Local Model Rule

Only local Ollama endpoints on `127.0.0.1` or `localhost` are allowed, and only through the Model Gateway. External model providers such as OpenAI, DeepSeek, Claude, Gemini, or other remote APIs are not allowed.

## Hybrid Provider Rule

The workbench may reserve metadata for `remote_api` and `desktop_tool`, but those provider types must remain mock-only until the user explicitly approves a later implementation phase.

Do not add credential storage, OAuth, browser-cookie reading, CLI-token reading, remote dashboard fetching, desktop software execution, shell execution, or automatic file modification while working under the current security boundary.
