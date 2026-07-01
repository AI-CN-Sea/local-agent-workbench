# Local Agent Workbench MVP Acceptance

## Scope

This MVP is a privacy-first local Agent workbench. External APIs, Web Search, MCP, automatic file parsing, automatic zip extraction, API key storage, and uploaded-file-content injection remain disabled.

Local model calls are allowed only when a local provider is enabled and active, the endpoint is on the Ollama / LM Studio localhost whitelist, and Model Gateway review allows the prompt.

## Acceptance Flow

1. Start backend on `127.0.0.1`.
2. Start frontend with Vite.
3. Open the workbench and create or select a project.
4. Create a local provider using one of the four whitelist endpoints.
5. Enable the provider and set it active.
6. Detect local provider and list local models.
7. Send a mock chat request and confirm messages persist.
8. Select a local model and send a local master request.
9. Confirm requirement and outline.
10. Verify the TaskContract shows structured steps.
11. Start an Agent Run.
12. Execute next step and verify AgentStep status changes.
13. Verify agent deliverables appear after step execution.
14. Execute Review Agent step and verify review results appear.
15. Upload a file and verify it stays quarantine.
16. Click Inspect and verify only metadata is shown.
17. Click Parse preview and verify it is blocked without reading file contents.
18. Save a memory item manually.
19. Search active memory and verify only active items are returned.

## Smoke Commands

```powershell
cd E:\codex\local-agent-workbench\backend
..\agentwork\Scripts\python.exe -B -c "from app.main import app; print('ok')"
..\agentwork\Scripts\python.exe -B scripts\smoke_test.py
```

```powershell
cd E:\codex\local-agent-workbench\frontend
.\node_modules\.bin\tsc.cmd -b
```

## Remaining Non-MVP Items

- External API providers.
- Web Search.
- MCP.
- Desktop packaging.
- Automatic skill learning.
- Approval token binding with `approval_id + prompt_hash`.
- Sandboxed full file parsing after explicit approval.

## Current AgentExecutor Behavior

The MVP AgentExecutor builds a controlled execution context from:

- TaskContract objective, constraints, acceptance criteria, and steps.
- Enabled and active Skill rules selected by the current step.
- Active project/global Memory that is not high or critical sensitivity.
- Previous deliverable summaries.

It currently emits fallback deliverables and review results without external APIs, Web Search, MCP, shell execution, or uploaded file content reads.

## Agent Run Metadata Acceptance

- Agent steps expose whether user approval is required.
- Steps with `requires_approval=true` stop at `requires_approval` and do not execute automatically.
- There is no approval API in this pass.
- Executed fallback steps expose execution metadata: executor mode, injected Skill IDs, injected Memory IDs, previous deliverable IDs, and prompt hash.
- Agent Runs may bind `model_provider_id` and `model_name`.
- If a run has a valid enabled active local provider/model, AgentExecutor invokes the local model only through Model Gateway.
- If no model is selected or the local invocation fails, AgentExecutor uses fallback output and records `fallback_reason`.
- Metadata records `executor_mode`, `used_local_model`, provider/model, prompt hash, and fallback reason.
- The frontend may show metadata summaries, but must not show full prompts or memory contents.
- Review Agent steps still create review results against the generated Review Agent deliverable.
- External APIs, Web Search, MCP, shell execution, browser automation, automatic file parsing, parse-preview, and attach-context remain disabled.

## Hybrid Architecture Acceptance

- The workbench reserves `local_ollama`, `remote_api`, `desktop_tool`, and `mock` provider types.
- Only `local_ollama` is currently callable, and only on localhost Ollama endpoint `:11434`.
- `remote_api` and `desktop_tool` must display as mock placeholders and must not make real calls.
- ModelProfile, ModelCapabilityScore, Skill Registry, SkillPipeline, Privacy Gateway, AdaptiveModelRouter, DesktopToolProfile, and AgentRunStep fields are present.
- TaskContract views expose selected skill, pipeline steps, privacy level, recommended models, estimated cost, and confirmation requirement.
- `/api/chat` returns project id, conversation id, and agent run id after creating the task contract loop.
- Frontend right-side panels show Task Contract, Skill Pipeline, Model Routing, Privacy Gateway, Safety & Execution, and Desktop Tools Mock.
