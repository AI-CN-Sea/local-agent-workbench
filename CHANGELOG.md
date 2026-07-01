# Changelog

## v0.1.0 - Runnable cleanup

### Added

- MIT license and contribution guide.
- Architecture, privacy design, and roadmap docs.
- Seeded `Local Ollama` provider in Model Gateway as disabled draft metadata.
- Lightweight demo APIs for task creation, privacy checks, and review.
- Smoke coverage for non-approval Agent Run execution.
- MVP skill seed aliases for coding, writing, research summary, document helper, planning, and review.

### Changed

- README rewritten for local runnable OSS demonstration.
- Approval logic now uses per-step approval flags first and only applies global blocking for high privacy risk or disabled execution.

### Security

- External API, web search, MCP, desktop tools, and uploaded-file parsing remain disabled by default.
- Model invocation logs keep hashes, lengths, risk level, and findings only.