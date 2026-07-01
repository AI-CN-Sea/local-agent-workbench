# UI Redesign Notes

## App Shell

The frontend now uses a fixed app shell:

- `TopStatusBar`: database, project, conversation, model policy, and security badges.
- `Sidebar`: fixed-width navigation and project/conversation selectors.
- `MainWorkspace`: central task, conversation, artifact preview, action bar, and composer.
- `RightInspector`: fixed-width tabbed inspector.

Each region owns its scroll area. Long inspector content scrolls inside the right panel and no longer pushes the chat workspace down.

## Left Nav View Switching

The sidebar uses `activeView`:

- `workbench`
- `skills`
- `providers`
- `artifacts`
- `privacy`
- `settings`

Every item opens a real central view. Incomplete functions use explicit placeholder or metadata-only panels.

## MainWorkspace Structure

Workbench view:

- current task header
- conversation feed
- quarantine file list
- task contract strip
- artifact preview
- action bar
- sticky bottom composer

The composer remains visible at the bottom of `MainWorkspace`.

## RightInspector Tabs

Right inspector tabs:

- `Task`
- `Pipeline`
- `Models`
- `Safety`
- `Artifacts`

Tabs group summaries first and put longer content in details or compact lists. The UI avoids raw JSON dumps.

## StatusBadge Rules

`StatusBadge` centralizes visible execution state:

- `REAL_LOCAL`: controlled localhost Ollama provider is active.
- `MOCK_ONLY`: mock-only provider or placeholder.
- `RESERVED_DISABLED`: reserved but disabled capability.
- `NO_EXTERNAL_CALL`: external API and web search are off.
- `NO_DESKTOP_EXECUTION`: desktop tool execution is not enabled.
- `REQUIRES_APPROVAL`: gated action or quarantine status.
- `BLOCKED`: safety block.
- `RUNNING`, `COMPLETED`, `FAILED`, `PAUSED`: run state.
- `LOW_RISK`, `MEDIUM_RISK`, `HIGH_RISK`: privacy/model risk.

## Mock / Real / Disabled Display

- Local Ollama is the only real model path, and only through active local provider review.
- `remote_api` is displayed as `MOCK_ONLY` or `RESERVED_DISABLED`.
- `desktop_tool` is displayed as `NO_DESKTOP_EXECUTION`.
- OAuth, cookie, CLI token, Web Search, and MCP remain disabled.
- Uploads are shown as quarantine files: not parsed, not sent to Agent.

## Settings Placeholder Design

Settings is now a real route-like view with:

- Local runtime and endpoint whitelist.
- Context preset placeholders.
- Remote API reserved-disabled state.
- Desktop tool mock-only state.
- Security disabled capabilities.
- Build/system placeholders.

## Local Preview

No browser preview or screenshot tool was used during this pass. Verification was planned through TypeScript and production build commands only.
