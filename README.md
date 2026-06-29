# Local Agent Workbench

Local Agent Workbench 是一个隐私优先的本地多 Agent 智能工作台。后端使用 Python FastAPI，前端使用 React + Vite + TypeScript，数据库使用本地 SQLite。

当前状态：支持本机 Ollama 的受控调用 MVP。所有本地模型调用必须经过 Model Gateway 安全审查；仍然禁止外部 API、网页搜索、MCP、自动文件解析和自动解压。

当前一周 MVP 压缩版还包含：

- Agent Run / Step 执行骨架。
- 结构化 TaskContract steps。
- 默认 Skill seed 和启用/禁用管理。
- Memory active 检索。
- 文件 inspect 元数据检查。
- 文件 parse-preview 安全占位接口，当前不读取 quarantine 文件内容。

## 安全边界

- 只允许后端绑定 `127.0.0.1`。
- 不要使用 `--host 0.0.0.0`。
- 本地模型仅允许 Ollama 的 localhost endpoint。
- 不允许 OpenAI、DeepSeek、Claude、Gemini 等外部模型 API。
- 不允许网页搜索。
- 不允许 MCP。
- 不读取上传文件内容。
- 不把上传文件内容写入 prompt、memory、skill 或日志。
- 不保存完整 prompt / response 到日志。
- 不自动保存长期记忆。

## 项目结构

```text
local-agent-workbench/
  AGENTS.md
  SECURITY.md
  THREAT_MODEL.md
  agentwork/              # 后端 Python 虚拟环境，不提交
  backend/
    app/
      api/                # FastAPI 路由
      agents/             # Agent 状态和分工
      database/           # SQLite 表结构、初始化和 CRUD
      files/              # 文件上传隔离
      memory/             # 记忆建议与记忆数据
      model_gateway/      # Model Gateway，本机模型受控调用
      orchestrator/       # mock 状态机和本地主控 Agent
      scripts/            # smoke test
      schemas/            # API 数据结构
      security/           # 扫描、脱敏、权限模型、安全策略
      skills/             # Skill 管理
      tools/              # 工具注册占位
    requirements.txt
  frontend/
    src/
      App.tsx
      api.ts
      types.ts
      styles.css
    package.json
```

## 后端安装与启动

后端统一使用项目根目录下的 `agentwork` 虚拟环境。

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后可访问：

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/api/workbench/state`

## 前端安装与启动

```powershell
cd frontend
npm install
npm run dev
```

启动后访问：

```text
http://127.0.0.1:5173
```

Vite 代理：

- `/api` -> `http://127.0.0.1:8000`
- `/health` -> `http://127.0.0.1:8000`

## 常用验证命令

```powershell
cd backend
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -c "from app.main import app; print('ok')"
python -B scripts\smoke_test.py
```

```powershell
cd frontend
.\node_modules\.bin\tsc.cmd -b
```

## Hybrid Workbench Update

Current positioning: Hybrid Local-Controlled Multi-API Agent Workbench. The system is not a plain chat tool and is not an Ollama-only architecture.

Current real-call boundary:

- Only local Ollama on `http://127.0.0.1:11434` and `http://localhost:11434` can be called, and only through Model Gateway.
- `remote_api` is reserved as a mock provider type. It does not request external APIs, store API keys, use OAuth, read browser cookies, or fetch usage from remote dashboards.
- `desktop_tool` is reserved as a mock provider type. It does not execute desktop software, shell commands, browser automation, or file modifications.
- Web Search, MCP, automatic upload parsing, automatic zip extraction, and uploaded-file prompt injection remain disabled.

Reference projects were inspected read-only and used only as architecture inspiration:

- CCG Gateway: provider profile, model mapping, blacklist, request logs, token usage, cost statistics, and provider management UI ideas.
- EdgeClaw: cost-aware routing, privacy routing, context compaction, tool governance, sandbox, skill discovery, and model judge ideas.
- RetainPDF: job/stage/event/artifact center, retry/resume/cancel, and pipeline monitor ideas.
- Academic Research Skills: router skill, multi-stage workflow, integrity gate, checkpoint, data access level, material passport, and adapter ideas.
- Nature Skills: `SKILL.md`, `manifest.yaml`, `static/`, `references/`, and `_shared/` skill organization ideas.
- CodexBar: provider usage, cost, quota, reset window, and status monitor ideas.

No reference project code is executed or copied into this project.

## Current Follow-up APIs

- `POST /api/model-gateway/approval-intents`: creates a local approval intent for medium-risk prompts and binds it to `prompt_hash`.
- `POST /api/model-gateway/local-invoke`: accepts `approval_id` for medium-risk local Ollama calls; full prompt/response is not logged.
- `GET /api/model-gateway/provider-usage`: returns local usage snapshots aggregated from invocation logs when available.
- `GET /api/model-gateway/provider-costs`: returns local cost/token stats aggregated from invocation logs when available.
- `GET /api/artifacts?project_id=...&conversation_id=...`: returns Artifact Center metadata from task contracts, runs, and deliverables.
- `GET /api/skill-packages`: returns read-only metadata for `SKILL.md`, `manifest.yaml`, `static/`, `references/`, and `_shared/` layout.
