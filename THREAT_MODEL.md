# Threat Model

## Trust Boundaries

- User input: untrusted text that may contain prompt injection or secrets.
- Uploaded files: untrusted content; currently quarantined and not parsed automatically.
- Local models: local-only but still untrusted outputs.
- Skills: configurable behavior that may introduce unsafe rules.
- Memory: persisted context that may leak sensitive content if not reviewed.
- MCP: disabled; future MCP integrations are high risk.
- Search: disabled; future search integrations are high risk.
- File system: protected boundary; the app must not read outside intended project storage.

## High-Risk Areas

- Prompt injection.
- Uploaded file content leakage.
- Full prompt or response leakage into logs.
- External API access.
- SSRF through provider endpoints or network gateway.
- MCP tool execution.
- Automatic file parsing or archive extraction.
- Memory or Skill poisoning.

## Current Defenses

- Local model endpoint whitelist.
- Payload scanner.
- Query redactor.
- Local-only Model Gateway.
- Quarantine upload storage.
- Log minimization for model invocation records.
- External API, web search, and MCP disabled by default.
- Uploaded file contents are not sent to agents.
- Agent Run / Step MVP uses controlled fallback execution and does not call external tools.
- File inspect returns metadata only; parse-preview is currently blocked and does not read file contents.

## Future Work

- `approval_id` / approval token with prompt hash binding.
- Untrusted context propagation throughout prompts.
- Tool permission enforcement at runtime.
- File parsing sandbox.
- Full explicit file parsing approval flow.
- Per-project security policy profiles.
- Network Gateway approval workflow.

## Reserved Hybrid Workbench Risks

- `remote_api` provider metadata can create a false sense that external calls are enabled. Current implementation must keep it mock-only until a later explicit approval phase.
- Provider usage/cost/quota fetch strategies such as OAuth, browser cookies, CLI tokens, and web dashboards are high risk and currently disabled.
- `desktop_tool` provider metadata can create a false sense that desktop automation is enabled. Current implementation must keep it mock-only and must not execute desktop software, shell commands, browser automation, or file modification.
- Skill packages may include `SKILL.md`, `manifest.yaml`, `static/`, `references/`, and `_shared/`, but current loading is metadata-only. Scripts and external retrieval remain disabled.
- Artifact Center items are metadata placeholders. They must not point to or expose sensitive local file contents without explicit future approval.
