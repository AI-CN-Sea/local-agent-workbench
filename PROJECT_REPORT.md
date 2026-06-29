# Local Agent Workbench 项目报告

更新时间：2026-06-08

## 当前状态

项目目录：

```text
local-agent-workbench
```

当前允许在用户启用 active local provider 后，经 Model Gateway 安全审查调用本机 Ollama；不允许外部 API、网页搜索、MCP，不读取上传文件内容。

## 已完成能力

- FastAPI 后端骨架。
- React + Vite + TypeScript 前端骨架。
- SQLite 表结构、数据库初始化函数和基础 CRUD service。
- 项目管理和当前项目选择。
- 对话持久化和消息读取。
- 文件上传 quarantine 隔离。
- 安全请求与 network audit logs。
- 任务协议、Agent 交付物、审核结果可视化。
- mock 主控 Agent 状态机。
- Skill 数据管理与冲突检测。
- Memory 数据管理、记忆建议保存与禁用。
- Model Gateway provider / prompt template 管理。
- Prompt preview、payload scanner、redactor。
- 本机 Ollama 受控调用 MVP。
- 本地模型驱动的主控 Agent MVP。
- Agent Run / Step 执行骨架。
- AgentExecutor 受控 fallback 基础版。
- Skill 注入执行链基础版：只注入 enabled + active 的 Skill。
- Memory 注入执行链基础版：只注入 active 且非 high/critical 的 project/global memory。
- 结构化 TaskContract steps。
- 默认 Skills seed。
- Memory active 检索。
- 文件 inspect 元数据接口。
- parse-preview 安全占位接口，当前不读取 quarantine 文件内容。
- 项目安全规范、Untrusted Context、工具权限模型、Prompt 模板保护。

## 数据库能力

已建立本地 SQLite 表结构：

- `projects`
- `conversations`
- `messages`
- `task_contracts`
- `agent_deliverables`
- `review_results`
- `agent_runs`
- `agent_steps`
- `skills`
- `memory_items`
- `security_requests`
- `network_audit_logs`
- `uploaded_files`
- `model_providers`
- `model_invocation_logs`
- `prompt_templates`

当前数据库仅使用本地 SQLite，不接入外部数据库。

## 文件上传隔离

已实现 `POST /api/files/upload`。

上传文件保存到：

```text
projects/<project_id>/uploads/quarantine/
```

安全边界：

- 限制文件大小。
- 限制扩展名。
- 上传后重命名为 UUID 文件名。
- 保存 sha256 和元数据。
- 不自动打开文件。
- 不自动解压 zip。
- 不自动解析 Word/PDF/PPT。
- 不把文件内容发送给 Agent。
- 不把上传文件内容写入 prompt、memory、skill 或日志。
- `POST /api/files/{file_id}/inspect` 仅返回元数据。
- `POST /api/files/{file_id}/parse-preview` 当前为安全占位并阻断，不读取文件内容。

## Agent Run / Step MVP

已实现：

- `POST /api/agent-runs/start`
- `GET /api/agent-runs?conversation_id=...`
- `GET /api/agent-runs/{run_id}/steps`
- `POST /api/agent-runs/{run_id}/step`
- `POST /api/agent-runs/{run_id}/pause`
- `POST /api/agent-runs/{run_id}/resume`
- `POST /api/agent-runs/{run_id}/cancel`

当前 step 执行为受控 fallback，不调用外部 API、不联网搜索、不接 MCP、不读取上传文件内容。执行完成后写入 `agent_deliverables`，Review Agent step 会写入 `review_results`。

AgentExecutor 当前会构造受控执行上下文：

- 当前 task contract 摘要。
- 当前 step goal / expected output。
- 当前 step 允许的 active Skill rules。
- 当前项目或 global 的低敏 active Memory。
- previous deliverables 摘要。

当前不直接调用外部 API、Web Search、MCP、shell、文件读取或上传文件解析。

## Skill / Memory MVP

- 启动数据库时 seed 8 个默认 active Skill。
- Skill permissions 只包含 `model_invoke`，不包含 Web Search 或 MCP。
- `GET /api/memory/search?q=&project_id=` 只返回 active memory，并支持项目/全局范围。

## Model Gateway

当前 Model Gateway 支持：

- mock provider。
- local provider，仅允许本机 Ollama endpoint。
- provider 连接检测。
- 本地模型列表读取。
- prompt preview。
- local-invoke 安全审查与受控调用。

本机模型 endpoint 白名单保持为：

- `http://127.0.0.1:11434`
- `http://localhost:11434`

调用要求：

- provider 必须 `enabled=true`。
- provider 必须 `status=active`。
- high / critical 风险直接阻断。
- medium 风险需要用户确认；当前为 MVP 临时 `user_approved` 方案，后续应改为 `approval_id + prompt_hash` 校验。
- 不保存完整 prompt。
- 不保存完整 response。

## 本地主控 Agent MVP

当 `/api/chat` 收到 `local_provider_id + local_model_name` 时，会走本地模型主控 Agent 流程：

- 只处理当前用户 message。
- 使用 `Master Requirement Analysis Prompt`。
- 要求模型输出 JSON。
- JSON 字段包括 `requirement_card`、`outline_card`、`task_type`、`missing_info`、`safety_notes`。
- JSON 解析失败时使用安全 fallback，不让接口崩溃。
- 不读取上传文件内容。
- 不联网搜索。
- 不调用 MCP。
- 不调用外部 API。

## 安全和审计

已实现：

- payload scan。
- payload redact。
- security request。
- network audit log 写入和查看。
- model invocation log。
- Untrusted Context 包装函数。
- 高危工具权限模型。
- Prompt template 字段保护。

`model_invocation_logs` 仅保存：

- provider/template/task ids
- mode
- prompt hash
- prompt length
- risk level
- blocked
- findings summary

不保存完整 prompt / response。

## 禁止事项

当前仍保持：

- 不允许外部 API。
- 不允许网页搜索。
- 不允许 MCP。
- 不自动解析上传文件。
- 不自动解压 zip。
- 不读取项目目录之外的文件。
- 不保存 API Key。
- 不把完整 prompt / response 写入日志。
- 不自动保存长期记忆。

## 启动命令

后端启动命令统一使用：

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Agent Run Hardening Update

- `agent_steps` now stores `requires_user_approval` and `execution_metadata_json`.
- TaskContract step `requires_approval` is copied into AgentStep records when a run starts.
- If a step requires approval, `advance_agent_step` marks it as `requires_approval` and does not call AgentExecutor, create deliverables, or create review results.
- No approval API is implemented in this pass.
- AgentExecutor now supports local-model-backed sub-agent steps when an Agent Run is bound to a local provider/model.
- Local-model-backed AgentExecutor calls only through Model Gateway and only for enabled active local providers on the Ollama localhost whitelist.
- If no model is selected, or the local provider/model call fails, AgentExecutor falls back safely.
- External APIs, Web Search, MCP, shell, browser automation, uploaded file parsing, parse-preview, and attach-context remain disabled.
- Step metadata records executor mode, injected Skill IDs, injected Memory IDs, previous deliverable IDs, prompt hash, and a truncated prompt preview. Full prompts and responses are not saved to logs.
- Step metadata also records `used_local_model`, provider/model IDs, risk level, and fallback reason.
- Deliverable artifacts store executor/context metadata only, not full prompts.
- Memory injection now requires active project/global memory, excludes high/critical sensitivity, and avoids injecting irrelevant zero-score memories for nonempty queries.

## Hybrid Workbench Recalibration

- The project is now aligned as a Hybrid Local-Controlled Multi-API Agent Workbench, not a plain chat tool and not an Ollama-only architecture.
- Provider types are reserved as `local_ollama`, `remote_api`, `desktop_tool`, and `mock`.
- Current real callable provider is only `local_ollama` on `http://127.0.0.1:11434` or `http://localhost:11434`.
- `remote_api` and `desktop_tool` are mock placeholders only. No external API, API key, desktop software execution, browser automation, shell execution, or file modification was added.
- ModelProfile and ModelCapabilityScore structures are reserved with built-in mock profiles and mock scores.
- Skill Registry and SkillPipeline/SkillStep are reserved for requirement analysis, privacy redaction, Codex instruction generation, code development, review planning, architecture analysis, documents, papers, PPT, diagrams, and desktop tool planning.
- TaskContract now stores hybrid metadata: selected skill, recommended executor, pipeline steps, model roles, recommended models, Privacy Gateway fields, cost level, confirmation requirement, risk, execution gate, and blocked reasons.
- Privacy Gateway currently uses mock/rule-based scanning and redaction to produce `privacy_level`, `external_allowed`, `requires_redaction`, `api_safe_context`, and `local_only_context`.
- AdaptiveModelRouter is currently rule/mock based and records recommendations without real remote calls.
- AgentStep records now reserve AgentRunStep fields such as step name/type, model role, selected provider/model, cost estimate, latency placeholder, quality placeholder, started_at, and finished_at.
- Desktop tools are visible as mock-only profiles; no local software is executed.

## Reference Architecture Absorption Update

This update inspected the provided reference zip archives in read-only mode. No code was run from those archives and no package was copied into this project.

Implemented or reserved structures inspired by the references:

- `SkillRegistryItem`, `SkillPackageMetadata`, `SkillPipeline`, and `SkillPipelineStep` for manifest-driven skill routing.
- `ModelProfile`, `ModelCapabilityScore`, `AdaptiveRoutingResult`, and routing alternatives for adaptive model routing.
- `ProviderDescriptor`, `ProviderFetchStrategy`, `ProviderUsageSnapshot`, `ProviderCostStats`, and `ProviderQuotaWindow` for provider profile, usage, cost, quota, and reset-window monitoring.
- `PrivacyGatewayResult` for local/privacy-first routing decisions.
- `AgentStepView` and `agent_steps.execution_metadata_json` for run-step monitoring, pipeline step display, route score, token estimate, and cost estimate.
- `ModelInvocationLogView` and extended `model_invocation_logs` fields for hash-only invocation audit logs.
- `ModelEvaluationLogView` for model judge/evaluation placeholders.
- `ArtifactCenterItem` for a future artifact center. Current items are mock metadata only.

Current provider boundary:

- `local_ollama` is the only real callable provider and is restricted to `http://127.0.0.1:11434` and `http://localhost:11434`.
- `remote_api` remains mock only. No external API, API key, OAuth, browser cookie, CLI credential, or remote dashboard fetch was added.
- `desktop_tool` remains mock only. No desktop application, shell command, browser automation, or file modification was added.

Skill package support:

- Current `skills/` packages use `SKILL.md`, `manifest.yaml`, `static/`, and `references/` directories.
- A collection-level `skills/_shared/` directory is reserved for shared fragments and policies.
- Skill package loading is read-only metadata loading; scripts are disabled.

## Follow-up Stability Build

This round completed the main unfinished scaffold items from the previous report:

- Added `model_invocation_approvals` for approval intent records.
- Added `POST /api/model-gateway/approval-intents`.
- `local-invoke` now prefers `approval_id + prompt_hash` for medium-risk local calls. The legacy `user_approved` flag remains only as a compatibility fallback.
- `ChatRequest` / `ChatResponse` can carry `approval_id` and `prompt_hash` for the local Master Agent flow.
- Provider usage and cost stats are now aggregated from local `model_invocation_logs` when logs exist; static placeholders are used only when no logs exist.
- Artifact Center now derives metadata items from `task_contracts`, `agent_runs`, and `agent_deliverables`; static mock items are used only when no artifacts exist.
- `GET /api/artifacts` now accepts optional `project_id` and `conversation_id`.
- Skill package registry now dynamically scans `skills/` directories instead of using a hard-coded package list.
- Skill package metadata reports `SKILL.md`, `manifest.yaml`, `static/`, `references/`, and collection-level `_shared/` support. It does not execute scripts or read static/reference file contents.

Security boundary remains unchanged:

- Only local Ollama whitelist endpoints are callable.
- `remote_api` remains mock-only.
- `desktop_tool` remains mock-only.
- No Web Search, MCP, external API, uploaded-file parsing, archive extraction, shell execution, or desktop automation was added.
