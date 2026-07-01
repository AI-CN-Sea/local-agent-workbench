# Privacy Design

Local Agent Workbench is designed around a local-only default security model.

## Principles

- Local first: the backend, frontend, SQLite database, and model gateway run on the user's machine.
- Explicit model access: model calls must pass provider allowlists and safety review.
- Minimal retention: logs store hashes, lengths, risk levels, and findings instead of full sensitive prompts or responses.
- Quarantine uploads: uploaded files are stored separately and are not opened, executed, decompressed, or parsed automatically.
- Untrusted context: user input, filenames, local model output, memory, and skill metadata are treated as untrusted.

## Local Model Boundary

Allowed local model endpoints in v0.1.0:

- `http://127.0.0.1:11434`
- `http://localhost:11434`

The seeded `Local Ollama` provider starts disabled and draft. The user must enable it and set it active before invocation.

## Disabled Surfaces

- External model APIs are not enabled.
- Web search is not enabled.
- MCP execution is not enabled.
- Desktop tools are mock only and never execute.
- Shell execution is not exposed by the workbench.
- Uploaded file execution is not allowed.
- Uploaded file parsing is not automatic.

## Data Handling

- Task and conversation metadata are stored in SQLite.
- Uploaded files remain in quarantine storage, and UI messaging states that they are not parsed or sent to agents automatically.
- Model invocation logs keep prompt hash, length, risk level, blocked status, and findings only.
- Memory and skill creation paths are scanned before activation.

## Current Gaps

- Prompt-hash-bound approval tokens should be strengthened in future releases.
- File parsing sandbox is not implemented.
- Per-tool runtime permission enforcement is still metadata-only.
- Memory review and export controls need a deeper workflow.