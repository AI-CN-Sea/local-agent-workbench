from datetime import UTC, datetime
from uuid import uuid4

from app.agents.service import get_agent_status
from app.database.crud import get_record
from app.database.models import ConversationRecord
from app.database.service import (
    create_conversation,
    create_memory_item,
    create_message,
    create_session,
    create_task_contract,
    ensure_default_project,
    ensure_project,
    start_agent_run,
)
from app.hybrid.service import build_task_contract_metadata
from app.orchestrator.local_master_agent import LocalMasterAgentResult, run_local_master_agent
from app.schemas.database import AgentRunStartRequest
from app.schemas.workbench import (
    ChatRequest,
    ChatResponse,
    ConversationSnapshot,
    Message,
    OutlineCard,
    RequirementCard,
)


def get_conversation_snapshot() -> ConversationSnapshot:
    return ConversationSnapshot(
        title="本地多 Agent 工作台 Demo",
        messages=[
            Message(
                id="msg-001",
                role="assistant",
                content="你好，我是本地主控 Agent。默认不调用模型；启用 active local provider 并通过审查后可调用本机 Ollama。",
                timestamp="2026-06-01T00:00:00Z",
            )
        ],
        requirement_card=get_requirement_card(),
        outline_card=get_outline_card(),
    )


def submit_user_message(request: ChatRequest) -> ChatResponse:
    if request.local_provider_id and request.local_model_name:
        return _submit_local_user_message(request)

    now = datetime.now(UTC).isoformat()
    reply_content = (
        f"已收到你的需求：{request.message}。"
        "已创建对话、消息和任务协议草案，当前等待需求确认。"
    )

    session = create_session()
    try:
        if request.conversation_id:
            conversation = get_record(session, ConversationRecord, request.conversation_id)
            if conversation is None:
                raise ValueError(f"Conversation not found: {request.conversation_id}")
            if request.project_id and conversation.project_id != request.project_id:
                raise ValueError("Conversation does not belong to the requested project.")
        else:
            project = ensure_project(session, request.project_id) if request.project_id else ensure_default_project(session)
            conversation = create_conversation(
                session,
                project_id=project.id,
                title=_conversation_title(request.message),
                current_state="waiting_requirement_confirmation",
            )
        create_message(
            session,
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            metadata={"source": "chat", "model_id": request.model_id},
        )
        metadata = build_task_contract_metadata(request.message, "mock_requirement_analysis")
        task_steps = _pipeline_task_steps(metadata)
        task_contract = create_task_contract(
            session,
            project_id=conversation.project_id,
            conversation_id=conversation.id,
            title="Mock Task Contract",
            objective=request.message.strip()[:500],
            inputs=["用户当前消息"],
            outputs=["需求确认卡片", "大纲确认卡片", "任务协议草案"],
            constraints=["默认不调用模型", "不联网搜索", "不调用外部 API"],
            acceptance_criteria=["生成可审核 mock 结果", "持久化 conversation/message/task_contract"],
            steps=task_steps or [
                {
                    "step_index": 1,
                    "agent": "Planner",
                    "skill_ids": ["skill-planning"],
                    "goal": request.message.strip()[:200],
                    "expected_output": "mock 执行计划",
                    "requires_approval": False,
                },
                {
                    "step_index": 2,
                    "agent": "Review Agent",
                    "skill_ids": ["skill-review"],
                    "goal": "审核 mock 执行计划是否满足任务协议",
                    "expected_output": "审核结果",
                    "requires_approval": False,
                }
            ],
            metadata=metadata,
        )
        create_memory_item(
            session,
            project_id=conversation.project_id,
            title="需求摘要建议",
            content=request.message.strip()[:500],
            sensitivity="normal",
        )
        create_message(
            session,
            conversation_id=conversation.id,
            role="assistant",
            content=reply_content,
            metadata={"source": "mock-orchestrator", "state": "waiting_requirement_confirmation"},
        )
        conversation_id = conversation.id
        conversation_project_id = conversation.project_id
        task_contract_id = task_contract.id
    finally:
        session.close()

    agent_run_id = start_agent_run(
        AgentRunStartRequest(
            conversation_id=conversation_id,
            project_id=conversation_project_id,
            task_contract_id=task_contract_id,
        )
    ).id

    return ChatResponse(
        project_id=conversation_project_id,
        conversation_id=conversation_id,
        agent_run_id=agent_run_id,
        reply=Message(
            id=f"msg-{uuid4().hex[:8]}",
            role="assistant",
            content=reply_content,
            timestamp=now,
        ),
        requirement_card=get_requirement_card(),
        outline_card=get_outline_card(),
        agent_status=get_agent_status(),
    )


def _submit_local_user_message(request: ChatRequest) -> ChatResponse:
    now = datetime.now(UTC).isoformat()
    session = create_session()
    try:
        if request.conversation_id:
            conversation = get_record(session, ConversationRecord, request.conversation_id)
            if conversation is None:
                raise ValueError(f"Conversation not found: {request.conversation_id}")
            if request.project_id and conversation.project_id != request.project_id:
                raise ValueError("Conversation does not belong to the requested project.")
        else:
            project = ensure_project(session, request.project_id) if request.project_id else ensure_default_project(session)
            conversation = create_conversation(
                session,
                project_id=project.id,
                title=_conversation_title(request.message),
                current_state="waiting_requirement_confirmation",
            )
        create_message(
            session,
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            metadata={
                "source": "chat",
                "model_id": request.model_id,
                "local_provider_id": request.local_provider_id,
                "local_model_name": request.local_model_name,
                "approval_retry": request.user_approved and bool(request.conversation_id),
            },
        )
        conversation_id = conversation.id
        conversation_project_id = conversation.project_id
    finally:
        session.close()

    try:
        result = run_local_master_agent(
            provider_id=request.local_provider_id or "",
            model_name=request.local_model_name or "",
            message=request.message,
            user_approved=request.user_approved,
            approval_id=request.approval_id,
        )
    except ValueError as exc:
        result = _local_error_result(request.message, str(exc))

    reply_content = result.response_summary
    if result.requires_user_approval:
        reply_content = "本地模型主控 Agent 需要用户确认后再调用。"
    elif result.blocked:
        reply_content = "本地模型主控 Agent 已因安全策略阻断。"
    contract_status = _task_contract_status(result)
    contract_title = f"{_task_contract_title_prefix(contract_status)}Local Master Task: {result.task_type}"

    session = create_session()
    try:
        metadata = build_task_contract_metadata(request.message, result.task_type)
        task_steps = _pipeline_task_steps(metadata, fallback_steps=result.task_contract_steps)
        task_contract = create_task_contract(
            session,
            project_id=conversation_project_id,
            conversation_id=conversation_id,
            title=contract_title,
            objective=request.message.strip()[:500],
            inputs=["用户当前 message"],
            outputs=["需求确认卡片", "初始大纲", "任务协议草稿"],
            constraints=["不读取上传文件内容", "不联网搜索", "不调用外部 API", "不接 MCP"],
            acceptance_criteria=result.requirement_card.items[:4] or ["生成可审核需求卡片"],
            steps=task_steps,
            metadata=metadata,
            status=contract_status,
        )
        create_message(
            session,
            conversation_id=conversation_id,
            role="assistant",
            content=reply_content,
            metadata={
                "source": "local-master-agent",
                "task_type": result.task_type,
                "missing_info": result.missing_info,
                "safety_notes": result.safety_notes,
                "requirement_card": result.requirement_card.model_dump(),
                "outline_card": result.outline_card.model_dump(),
                "blocked": result.blocked,
                "requires_user_approval": result.requires_user_approval,
                "fallback_used": result.fallback_used,
                "selected_skill": metadata.get("selected_skill"),
                "privacy_level": metadata.get("privacy_level"),
            },
        )
        task_contract_id = task_contract.id
    finally:
        session.close()

    agent_run_id = start_agent_run(
        AgentRunStartRequest(
            conversation_id=conversation_id,
            project_id=conversation_project_id,
            task_contract_id=task_contract_id,
            model_provider_id=request.local_provider_id,
            model_name=request.local_model_name,
        )
    ).id

    return ChatResponse(
        project_id=conversation_project_id,
        conversation_id=conversation_id,
        agent_run_id=agent_run_id,
        reply=Message(
            id=f"msg-{uuid4().hex[:8]}",
            role="assistant",
            content=reply_content,
            timestamp=now,
        ),
        requirement_card=result.requirement_card,
        outline_card=result.outline_card,
        agent_status=get_agent_status(),
        requires_user_approval=result.requires_user_approval,
        blocked=result.blocked,
        fallback_used=result.fallback_used,
        safety_message=result.safety_message,
        approval_id=result.approval_id,
        prompt_hash=result.prompt_hash,
    )


def get_requirement_card() -> RequirementCard:
    return RequirementCard(
        title="需求确认",
        status="waiting_requirement_confirmation",
        items=[
            "确认目标、输入、输出和约束",
            "识别是否需要文件、工具、Skill 或记忆",
            "执行前给出可审核的任务边界",
        ],
    )


def get_outline_card() -> OutlineCard:
    return OutlineCard(
        title="大纲确认",
        status="waiting_outline_confirmation",
        sections=[
            "任务拆解",
            "Agent 分工",
            "执行步骤",
            "审核与交付",
        ],
    )


def _local_error_result(message: str, error: str) -> LocalMasterAgentResult:
    return LocalMasterAgentResult(
        requirement_card=RequirementCard(
            title="需求确认",
            status="waiting_requirement_confirmation",
            items=[
                f"用户需求摘要：{message.strip()[:160]}",
                "本地模型暂不可用，请确认 provider 已启用且为 active。",
                "确认 Ollama 已启动，并且 endpoint 在本机白名单内。",
            ],
        ),
        outline_card=OutlineCard(
            title="初始大纲",
            status="waiting_outline_confirmation",
            sections=["检查本机模型连接", "确认需求边界", "生成任务协议", "审核输出"],
        ),
        task_type="local_master_agent_unavailable",
        missing_info=["需要启用 active 的本机 provider 并选择本地模型。"],
        safety_notes=["未调用外部 API，未联网搜索，未读取上传文件内容。"],
        task_contract_steps=[
            {
                "step_index": 1,
                "agent": "Planner",
                "skill_ids": ["skill-planning"],
                "goal": "检查本机模型 provider 状态",
                "expected_output": "可继续执行的本机模型配置",
                "requires_approval": False,
            }
        ],
        response_summary="本地模型主控 Agent 暂不可用，已返回 fallback 需求确认和大纲。",
        blocked=True,
        fallback_used=True,
        safety_message=error,
    )


def _conversation_title(message: str) -> str:
    normalized = " ".join(message.strip().split())
    if not normalized:
        return "未命名对话"
    return normalized[:60]


def _task_contract_status(result: LocalMasterAgentResult) -> str:
    if result.blocked:
        return "blocked"
    if result.requires_user_approval:
        return "pending_approval"
    return "draft"


def _task_contract_title_prefix(status: str) -> str:
    if status == "blocked":
        return "[blocked] "
    if status == "pending_approval":
        return "[pending_approval] "
    return ""


def _pipeline_task_steps(
    metadata: dict[str, object],
    *,
    fallback_steps: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    raw_steps = metadata.get("pipeline_steps")
    raw_recommendations = metadata.get("recommended_models")
    if not isinstance(raw_steps, list):
        return fallback_steps or []
    recommendations: dict[str, dict[str, object]] = {}
    if isinstance(raw_recommendations, list):
        recommendations = {
            str(item.get("step_type")): item
            for item in raw_recommendations
            if isinstance(item, dict)
        }
    selected_skill = str(metadata.get("selected_skill") or "requirement_analysis")
    risk_level = str(metadata.get("risk_level") or "normal").lower()
    global_requires_approval = risk_level in {"high", "critical"} or metadata.get("execution_allowed") is False
    steps: list[dict[str, object]] = []
    for index, step in enumerate(raw_steps, start=1):
        if not isinstance(step, dict):
            continue
        step_type = str(step.get("step_type") or step.get("step_id") or "agent_step")
        recommendation = recommendations.get(step_type, {})
        steps.append(
            {
                "step_index": index,
                "step_id": step.get("step_id") or step_type,
                "step_name": step.get("step_name") or step_type,
                "step_type": step_type,
                "model_role": step.get("model_role") or "worker",
                "agent": _agent_for_step(step_type, str(step.get("model_role") or "")),
                "skill_ids": _skill_ids_for_contract(selected_skill, step_type),
                "goal": f"{step.get('step_name') or step_type}: {step.get('model_role') or 'worker'}",
                "expected_output": f"Structured output for {step_type}",
                "requires_approval": bool(step.get("requires_user_confirmation", step.get("requires_approval", False))) or global_requires_approval,
                "recommended_provider_type": recommendation.get("recommended_provider_type") or step.get("default_provider_type"),
                "recommended_provider_id": recommendation.get("recommended_provider_id"),
                "recommended_model_id": recommendation.get("recommended_model_id"),
                "recommended_model": recommendation.get("recommended_model"),
                "final_score": recommendation.get("final_score"),
                "selected_reason": recommendation.get("reason"),
                "alternatives": recommendation.get("alternatives") if isinstance(recommendation.get("alternatives"), list) else [],
                "cost_limit": step.get("cost_limit") or metadata.get("estimated_cost_level") or "low",
            }
        )
    return steps or fallback_steps or []


def _agent_for_step(step_type: str, model_role: str) -> str:
    joined = f"{step_type} {model_role}".lower()
    if "review" in joined or "safety" in joined:
        return "Review Agent"
    if "code" in joined:
        return "Code Agent"
    if "write" in joined or "draft" in joined or "paper" in joined:
        return "Writer"
    if "research" in joined:
        return "Research Agent"
    if "format" in joined or "diagram" in joined or "desktop" in joined:
        return "Formatting Agent"
    return "Planner"


def _skill_ids_for_contract(selected_skill: str, step_type: str) -> list[str]:
    joined = f"{selected_skill} {step_type}"
    if "code" in joined:
        return ["skill-coding"]
    if "writing" in joined or "document" in joined or "paper" in joined:
        return ["skill-writing"]
    if "review" in joined or "safety" in joined:
        return ["skill-review"]
    if "diagram" in joined or "ppt" in joined:
        return ["skill-formatting"]
    return ["skill-planning"]
