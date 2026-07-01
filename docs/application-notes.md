# Application Notes

Local Agent Workbench v0.1.0 is suitable as an open-source local Agent Workbench foundation because it demonstrates a useful privacy-first pattern without requiring cloud credentials or external services.

## Current v0.1.0 Capability

- Runnable FastAPI backend with SQLite persistence.
- React + Vite + TypeScript frontend.
- Simple Workbench for entering tasks and reviewing final output.
- Local Ollama provider flow with `qwen2.5:7b` as the recommended default model.
- TaskContract generation and Agent Run step tracking.
- Review Summary and Advanced Developer Inspector.
- Privacy Guard, payload scanner, redaction, quarantine upload metadata, and local-only model gateway boundaries.
- Metadata-only skill registry and skill routing foundations.

## Open Source Maintenance Value

For a Codex for Open Source application, this project can emphasize:

- A reproducible local-first AI agent architecture.
- Clear privacy and threat-model documentation.
- A small but runnable MVP instead of a large cloud-dependent prototype.
- Defensive defaults around external APIs, MCP, desktop tools, shell execution, and uploaded files.
- A path for community contributions around skills, local model routing, review workflows, and artifact management.

## Future Work

- Stronger approval tokens bound to prompt hashes.
- Better local model capability evaluation.
- More robust Agent Run retry and recovery.
- Optional sandboxed file parsing with explicit approval.
- Richer skill package validation and documentation tooling.