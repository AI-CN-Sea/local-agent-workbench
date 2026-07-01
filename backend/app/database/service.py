import json
import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from collections.abc import Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.crud import create_record, get_record, list_records, update_record
from app.database.models import (
    AgentDeliverableRecord,
    AgentRunRecord,
    AgentStepRecord,
    ConversationRecord,
    MemoryItemRecord,
    MessageRecord,
    NetworkAuditLogRecord,
    ProjectRecord,
    ReviewResultRecord,
    SecurityRequestRecord,
    SkillRecord,
    TaskContractRecord,
    UploadedFileRecord,
)
from app.database.session import create_session, init_db
from app.schemas.database import (
    AgentRunStartRequest,
    AgentRunView,
    AgentStepView,
    ConversationView,
    AgentDeliverableView,
    FileInspectResponse,
    FileParsePreviewResponse,
    MessageView,
    NetworkAuditLogView,
    ProjectView,
    ReviewResultView,
    SecurityRequestView,
    SkillConflictResponse,
    SkillDbCreate,
    SkillDbUpdate,
    SkillDbView,
    TaskContractView,
    UploadedFileView,
    MemoryItemCreate,
    MemoryItemDbView,
    MemoryItemUpdate,
)
from app.memory.service import get_memory_suggestion
from app.orchestrator.agent_executor import AgentExecutionContext, execute_agent_step
from app.schemas.security import NetworkAuditLog
from app.schemas.workbench import DatabaseStatus
from app.security.payload_scanner import scan_payload
from app.security.privacy_classifier import classify_privacy

DEFAULT_PROJECT_ID = "project-local-default"


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def from_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def from_json_object_list(value: str) -> list[dict[str, object]]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def from_json_value_list(value: str) -> list[object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def from_json_dict(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def get_database_status() -> DatabaseStatus:
    init_db()
    return DatabaseStatus(
        engine="SQLite",
        path=settings.database_url,
        status="initialized",
    )


def ensure_default_project(session: Session) -> ProjectRecord:
    project = get_record(session, ProjectRecord, DEFAULT_PROJECT_ID)
    if project:
        return project
    return create_record(
        session,
        ProjectRecord(
            id=DEFAULT_PROJECT_ID,
            name="Local Workbench",
            description="Default local project for mock agent workflows.",
        ),
    )


def ensure_project(session: Session, project_id: str | None = None) -> ProjectRecord:
    if not project_id:
        return ensure_default_project(session)
    project = get_record(session, ProjectRecord, project_id)
    if project:
        return project
    return create_record(
        session,
        ProjectRecord(
            id=project_id,
            name=project_id,
            description="Project placeholder created for local upload isolation.",
        ),
    )


def create_project(session: Session, name: str, description: str | None = None) -> ProjectRecord:
    return create_record(session, ProjectRecord(name=name, description=description))


def list_projects(session: Session, limit: int = 50) -> list[ProjectRecord]:
    return list_records(session, ProjectRecord, limit=limit)


def list_project_views(limit: int = 50) -> list[ProjectView]:
    session = create_session()
    try:
        ensure_default_project(session)
        projects = list_projects(session, limit=limit)
        return [_project_view(project) for project in projects]
    finally:
        session.close()


def create_project_view(name: str, description: str | None = None) -> ProjectView:
    session = create_session()
    try:
        project = create_project(session, name=name, description=description)
        return _project_view(project)
    finally:
        session.close()


def create_conversation(
    session: Session,
    *,
    project_id: str,
    title: str,
    current_state: str = "idle",
) -> ConversationRecord:
    return create_record(
        session,
        ConversationRecord(project_id=project_id, title=title, current_state=current_state),
    )


def update_conversation_state(session: Session, conversation: ConversationRecord, state: str) -> ConversationRecord:
    return update_record(session, conversation, {"current_state": state})


def update_conversation_state_by_id(conversation_id: str, state: str) -> ConversationView:
    session = create_session()
    try:
        conversation = get_record(session, ConversationRecord, conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")
        updated = update_conversation_state(session, conversation, state)
        return _conversation_view(updated)
    finally:
        session.close()


def create_message(
    session: Session,
    *,
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict[str, object] | None = None,
) -> MessageRecord:
    return create_record(
        session,
        MessageRecord(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=to_json(metadata or {}),
        ),
    )


def list_conversation_views(project_id: str) -> list[ConversationView]:
    session = create_session()
    try:
        statement = (
            select(ConversationRecord)
            .where(ConversationRecord.project_id == project_id)
            .order_by(ConversationRecord.updated_at.desc())
        )
        return [_conversation_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def list_message_views(conversation_id: str) -> list[MessageView]:
    session = create_session()
    try:
        statement = (
            select(MessageRecord)
            .where(MessageRecord.conversation_id == conversation_id)
            .order_by(MessageRecord.created_at.asc())
        )
        return [_message_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def create_task_contract(
    session: Session,
    *,
    project_id: str,
    conversation_id: str,
    title: str,
    objective: str,
    inputs: Sequence[str],
    outputs: Sequence[str],
    constraints: Sequence[str],
    acceptance_criteria: Sequence[str],
    steps: Sequence[dict[str, object]] = (),
    metadata: dict[str, object] | None = None,
    status: str = "draft",
) -> TaskContractRecord:
    return create_record(
        session,
        TaskContractRecord(
            project_id=project_id,
            conversation_id=conversation_id,
            title=title,
            objective=objective,
            inputs_json=to_json(inputs),
            outputs_json=to_json(outputs),
            constraints_json=to_json(constraints),
            acceptance_criteria_json=to_json(acceptance_criteria),
            task_steps_json=json.dumps(list(steps), ensure_ascii=False),
            metadata_json=to_json(metadata or {}),
            status=status,
        ),
    )


def create_agent_deliverable(
    session: Session,
    *,
    project_id: str,
    conversation_id: str,
    task_contract_id: str | None,
    agent_name: str,
    summary: str,
    artifacts: Sequence[object] = (),
    risks: Sequence[str] = (),
    status: str = "generated",
) -> AgentDeliverableRecord:
    return create_record(
        session,
        AgentDeliverableRecord(
            project_id=project_id,
            conversation_id=conversation_id,
            task_contract_id=task_contract_id,
            agent_name=agent_name,
            summary=summary,
            artifacts_json=to_json(artifacts),
            risks_json=to_json(risks),
            status=status,
        ),
    )


def ensure_mock_agent_deliverables(
    session: Session,
    *,
    project_id: str,
    conversation_id: str,
    task_contract_id: str | None,
) -> None:
    existing = session.scalars(
        select(AgentDeliverableRecord).where(AgentDeliverableRecord.conversation_id == conversation_id).limit(1)
    ).first()
    if existing:
        return

    for agent_name, summary in [
        ("Planner", "已完成 mock 任务拆解和执行顺序规划。"),
        ("Writer", "已生成 mock 写作/说明输出占位结果。"),
        ("Code Agent", "已生成 mock 代码执行计划，不执行上传文件。"),
        ("Review Agent", "已完成 mock 审核，等待人工确认。"),
    ]:
        create_agent_deliverable(
            session,
            project_id=project_id,
            conversation_id=conversation_id,
            task_contract_id=task_contract_id,
            agent_name=agent_name,
            summary=summary,
            artifacts=["mock-only"],
            risks=["未调用真实 Agent", "未读取上传文件内容"],
        )


def create_review_result(
    session: Session,
    *,
    project_id: str,
    target_id: str,
    approved: bool,
    findings: Sequence[str],
    recommendations: Sequence[str],
    reviewer: str = "mock-reviewer",
    severity: str = "info",
) -> ReviewResultRecord:
    return create_record(
        session,
        ReviewResultRecord(
            project_id=project_id,
            target_id=target_id,
            reviewer=reviewer,
            approved=approved,
            severity=severity,
            findings_json=to_json(findings),
            recommendations_json=to_json(recommendations),
        ),
    )


def ensure_mock_review_result(
    session: Session,
    *,
    project_id: str,
    conversation_id: str,
    target_id: str,
) -> None:
    existing = session.scalars(
        select(ReviewResultRecord).where(ReviewResultRecord.target_id == target_id).limit(1)
    ).first()
    if existing:
        return
    create_review_result(
        session,
        project_id=project_id,
        target_id=target_id,
        approved=False,
        findings=["mock 审核完成，仍需人工确认", "未调用真实模型或外部服务"],
        recommendations=["确认任务协议后再进入真实执行设计", "保持文件隔离，不自动解析上传文件"],
        reviewer="Review Agent",
        severity="info",
    )


DEFAULT_AGENT_STEPS = [
    {"step_index": 1, "agent": "Planner", "skill_ids": ["skill-planning"], "goal": "整理执行计划", "expected_output": "可审核执行步骤", "requires_approval": False},
    {"step_index": 2, "agent": "Writer", "skill_ids": ["skill-writing"], "goal": "生成阶段性内容", "expected_output": "文字交付物", "requires_approval": False},
    {"step_index": 3, "agent": "Code Agent", "skill_ids": ["skill-coding"], "goal": "生成代码建议", "expected_output": "代码建议或补丁说明", "requires_approval": False},
    {"step_index": 4, "agent": "Review Agent", "skill_ids": ["skill-review"], "goal": "审核交付物", "expected_output": "审核结果", "requires_approval": False},
]

DEFAULT_AGENT_SKILL_IDS = {
    "Planner": ["skill-planning", "skill-requirement-analysis"],
    "Writer": ["skill-writing"],
    "Code Agent": ["skill-coding"],
    "Research Agent": ["skill-research-verification"],
    "Formatting Agent": ["skill-formatting"],
    "Review Agent": ["skill-review"],
}


def start_agent_run(request: AgentRunStartRequest) -> AgentRunView:
    session = create_session()
    try:
        conversation = get_record(session, ConversationRecord, request.conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation not found: {request.conversation_id}")
        if request.project_id and conversation.project_id != request.project_id:
            raise ValueError("Conversation does not belong to the requested project.")
        task_contract = _resolve_task_contract(session, request.conversation_id, request.task_contract_id)
        existing_active_run = session.scalars(
            select(AgentRunRecord)
            .where(
                AgentRunRecord.conversation_id == conversation.id,
                AgentRunRecord.task_contract_id == task_contract.id,
                AgentRunRecord.status.in_(["created", "running", "paused"]),
            )
            .order_by(AgentRunRecord.created_at.desc())
            .limit(1)
        ).first()
        if existing_active_run is not None:
            return _agent_run_view(existing_active_run)
        run = create_record(
            session,
            AgentRunRecord(
                project_id=conversation.project_id,
                conversation_id=conversation.id,
                task_contract_id=task_contract.id,
                model_provider_id=request.model_provider_id,
                model_name=request.model_name,
                status="running",
                current_step_index=0,
            ),
        )
        steps = from_json_object_list(task_contract.task_steps_json) or DEFAULT_AGENT_STEPS
        for index, step in enumerate(steps[:12], start=1):
            routing_metadata = {
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost": 0.0,
                "final_score": _safe_float(step.get("final_score")),
                "selected_reason": str(step.get("selected_reason") or step.get("reason") or "")[:500],
                "alternatives": _safe_object_list(step.get("alternatives"))[:3],
                "evaluation_status": "pending",
            }
            create_record(
                session,
                AgentStepRecord(
                    run_id=run.id,
                    step_index=int(step.get("step_index") or index),
                    pipeline_step_id=str(step.get("step_id") or step.get("pipeline_step_id") or "")[:120] or None,
                    step_name=str(step.get("step_name") or step.get("step_id") or step.get("goal") or f"Step {index}")[:160],
                    step_type=str(step.get("step_type") or step.get("step_id") or "agent_step")[:80],
                    model_role=str(step.get("model_role") or step.get("agent") or step.get("agent_name") or "Planner")[:120],
                    agent_name=str(step.get("agent") or step.get("agent_name") or "Planner")[:120],
                    skill_ids_json=to_json(_safe_skill_ids(step.get("skill_ids"))),
                    selected_provider_id=str(
                        step.get("selected_provider_id")
                        or step.get("recommended_provider_id")
                        or step.get("recommended_provider_type")
                        or ""
                    )[:80] or None,
                    selected_model_id=str(step.get("selected_model_id") or step.get("recommended_model_id") or "")[:120] or None,
                    status="pending",
                    requires_user_approval=bool(step.get("requires_approval", False)),
                    input_summary=str(step.get("goal") or task_contract.objective)[:500],
                    output_summary=str(step.get("expected_output") or "")[:500],
                    cost_estimate=str(step.get("cost_limit") or step.get("cost_estimate") or "low")[:40],
                    execution_metadata_json=to_json(routing_metadata),
                ),
            )
        return _agent_run_view(run)
    finally:
        session.close()


def list_agent_run_views(conversation_id: str) -> list[AgentRunView]:
    session = create_session()
    try:
        statement = (
            select(AgentRunRecord)
            .where(AgentRunRecord.conversation_id == conversation_id)
            .order_by(AgentRunRecord.created_at.desc())
        )
        return [_agent_run_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def list_agent_step_views(run_id: str) -> list[AgentStepView]:
    session = create_session()
    try:
        statement = select(AgentStepRecord).where(AgentStepRecord.run_id == run_id).order_by(AgentStepRecord.step_index.asc())
        return [_agent_step_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def advance_agent_step(run_id: str) -> AgentStepView:
    session = create_session()
    try:
        run = get_record(session, AgentRunRecord, run_id)
        if run is None:
            raise ValueError(f"Agent run not found: {run_id}")
        if run.status in {"paused", "cancelled", "completed", "failed"}:
            raise ValueError(f"Agent run is {run.status}; cannot advance step.")
        if run.status == "created":
            run = update_record(session, run, {"status": "running"})
        if run.status != "running":
            raise ValueError(f"Agent run is {run.status}; cannot advance step.")
        waiting_for_approval = session.scalars(
            select(AgentStepRecord)
            .where(AgentStepRecord.run_id == run_id, AgentStepRecord.status == "requires_approval")
            .order_by(AgentStepRecord.step_index.asc())
            .limit(1)
        ).first()
        if waiting_for_approval is not None:
            return _agent_step_view(waiting_for_approval)
        step = session.scalars(
            select(AgentStepRecord)
            .where(AgentStepRecord.run_id == run_id, AgentStepRecord.status == "pending")
            .order_by(AgentStepRecord.step_index.asc())
            .limit(1)
        ).first()
        if step is None:
            updated_run = update_record(session, run, {"status": "completed"})
            return AgentStepView(
                id="step-none",
                run_id=updated_run.id,
                step_index=updated_run.current_step_index,
                agent_name="Run",
                skill_ids=[],
                status="completed",
                input_summary="No pending steps.",
                output_summary="Agent run completed.",
                risk_level="normal",
                created_at=updated_run.updated_at,
                updated_at=updated_run.updated_at,
            )
        if step.requires_user_approval:
            metadata = {
                "approval_required": True,
                "executor_mode": "not_started",
                "reason": "step_requires_user_approval",
            }
            blocked_step = update_record(
                session,
                step,
                {
                    "status": "requires_approval",
                    "output_summary": "该步骤需要用户确认后继续执行。",
                    "execution_metadata_json": to_json(metadata),
                },
            )
            return _agent_step_view(blocked_step)
        running_step = update_record(session, step, {"status": "running", "started_at": utc_now()})
        try:
            context = _agent_execution_context(session, run, running_step)
            result = execute_agent_step(context)
        except Exception as exc:
            failed_step = update_record(
                session,
                running_step,
                {
                    "status": "failed",
                    "error_message": str(exc)[:1000],
                    "risk_level": "medium",
                    "execution_metadata_json": to_json({"executor_mode": "fallback", "error": str(exc)[:500]}),
                    "finished_at": utc_now(),
                },
            )
            update_record(session, run, {"status": "failed"})
            return _agent_step_view(failed_step)
        updated = update_record(
            session,
            running_step,
            {
                "status": "completed",
                "output_summary": result.summary,
                "risk_level": result.severity,
                "execution_metadata_json": to_json(
                    {
                        **from_json_dict(running_step.execution_metadata_json),
                        **result.execution_metadata,
                        "input_tokens": _estimate_tokens(result.execution_metadata.get("prompt_preview", "")),
                        "output_tokens": _estimate_tokens(result.summary),
                        "estimated_cost": 0.0,
                        "evaluation_status": "completed",
                    }
                ),
                "quality_score": 70 if result.used_local_model else 50,
                "finished_at": utc_now(),
            },
        )
        update_record(session, run, {"current_step_index": updated.step_index})
        _write_step_artifacts(session, run, updated, result)
        remaining = session.scalars(
            select(AgentStepRecord).where(AgentStepRecord.run_id == run_id, AgentStepRecord.status == "pending").limit(1)
        ).first()
        if remaining is None:
            update_record(session, run, {"status": "completed"})
        return _agent_step_view(updated)
    finally:
        session.close()


def pause_agent_run(run_id: str) -> AgentRunView:
    return _update_agent_run_status(run_id, "paused", allowed_from={"running"})


def resume_agent_run(run_id: str) -> AgentRunView:
    return _update_agent_run_status(run_id, "running", allowed_from={"paused"})


def cancel_agent_run(run_id: str) -> AgentRunView:
    session = create_session()
    try:
        run = get_record(session, AgentRunRecord, run_id)
        if run is None:
            raise ValueError(f"Agent run not found: {run_id}")
        if run.status in {"completed", "failed", "cancelled"}:
            raise ValueError(f"Agent run is {run.status}; cannot cancel.")
        return _agent_run_view(update_record(session, run, {"status": "cancelled", "cancel_requested": True}))
    finally:
        session.close()


def _update_agent_run_status(run_id: str, status: str, *, allowed_from: set[str]) -> AgentRunView:
    session = create_session()
    try:
        run = get_record(session, AgentRunRecord, run_id)
        if run is None:
            raise ValueError(f"Agent run not found: {run_id}")
        if run.status not in allowed_from:
            raise ValueError(f"Agent run is {run.status}; cannot transition to {status}.")
        return _agent_run_view(update_record(session, run, {"status": status}))
    finally:
        session.close()


def _resolve_task_contract(session: Session, conversation_id: str, task_contract_id: str | None) -> TaskContractRecord:
    if task_contract_id:
        task_contract = get_record(session, TaskContractRecord, task_contract_id)
        if task_contract is None or task_contract.conversation_id != conversation_id:
            raise ValueError(f"Task contract not found for conversation: {task_contract_id}")
        return task_contract
    task_contract = session.scalars(
        select(TaskContractRecord)
        .where(TaskContractRecord.conversation_id == conversation_id)
        .order_by(TaskContractRecord.created_at.desc())
        .limit(1)
    ).first()
    if task_contract is None:
        raise ValueError(f"No task contract found for conversation: {conversation_id}")
    return task_contract


def _safe_skill_ids(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item)[:80] for item in value if isinstance(item, str) and item.startswith("skill-")][:8]


def _safe_object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _estimate_tokens(value: object) -> int:
    text = str(value or "")
    if not text:
        return 0
    return max(1, len(text) // 4)


def _mock_step_output(step: AgentStepRecord) -> str:
    return (
        f"{step.agent_name} completed controlled local MVP step {step.step_index}. "
        "No external API, web search, MCP, uploaded file parsing, or file execution was performed."
    )


def _agent_execution_context(session: Session, run: AgentRunRecord, step: AgentStepRecord) -> AgentExecutionContext:
    task_contract = get_record(session, TaskContractRecord, run.task_contract_id)
    if task_contract is None:
        raise ValueError(f"Task contract not found: {run.task_contract_id}")
    requested_skill_ids = from_json_list(step.skill_ids_json) or DEFAULT_AGENT_SKILL_IDS.get(step.agent_name, [])
    skills = _active_skill_context(session, requested_skill_ids)
    memories = _memory_context(session, run.project_id, f"{task_contract.objective} {step.input_summary} {step.agent_name}")
    previous_deliverables = _previous_deliverable_context(session, run.conversation_id)
    return AgentExecutionContext(
        project_id=run.project_id,
        conversation_id=run.conversation_id,
        task_contract_id=run.task_contract_id,
        model_provider_id=run.model_provider_id,
        model_name=run.model_name,
        run_id=run.id,
        step_id=step.id,
        step_index=step.step_index,
        agent=step.agent_name,
        goal=step.input_summary,
        expected_output=step.output_summary,
        task_contract={
            "title": task_contract.title,
            "objective": task_contract.objective,
            "inputs": from_json_list(task_contract.inputs_json),
            "outputs": from_json_list(task_contract.outputs_json),
            "constraints": from_json_list(task_contract.constraints_json),
            "acceptance_criteria": from_json_list(task_contract.acceptance_criteria_json),
            "steps": from_json_object_list(task_contract.task_steps_json),
        },
        skills=skills,
        memories=memories,
        previous_deliverables=previous_deliverables,
    )


def _active_skill_context(session: Session, skill_ids: Sequence[str]) -> list[dict[str, str]]:
    if not skill_ids:
        return []
    records = session.scalars(
        select(SkillRecord).where(
            SkillRecord.id.in_(list(skill_ids)),
            SkillRecord.status == "active",
            SkillRecord.enabled == True,  # noqa: E712
        )
    )
    by_id = {record.id: record for record in records}
    context: list[dict[str, str]] = []
    for skill_id in skill_ids:
        record = by_id.get(skill_id)
        if record is None:
            continue
        context.append(
            {
                "id": record.id,
                "name": record.name,
                "description": record.description[:500],
                "rules": record.rules[:800],
            }
        )
    return context[:6]


def _memory_context(session: Session, project_id: str, query: str) -> list[dict[str, str]]:
    normalized_query, query_tokens = _memory_query_terms(query)
    records = session.scalars(
        select(MemoryItemRecord)
        .where(
            MemoryItemRecord.status == "active",
            (MemoryItemRecord.project_id == project_id) | (MemoryItemRecord.scope == "global"),
            MemoryItemRecord.sensitivity.notin_(["high", "critical"]),
        )
        .order_by(MemoryItemRecord.created_at.desc())
    )
    scored: list[tuple[int, MemoryItemRecord]] = []
    for record in records:
        haystack = f"{record.title} {record.content} {record.scope}".lower()
        score = sum(1 for token in query_tokens if token in haystack)
        if normalized_query and normalized_query in haystack:
            score += 3
        if normalized_query and score <= 0:
            continue
        scored.append((score, record))
    scored.sort(key=lambda item: item[0], reverse=True)
    context = []
    for _, record in scored[:5]:
        context.append(
            {
                "id": record.id,
                "scope": record.scope,
                "title": record.title[:160],
                "content": record.content[:800],
                "sensitivity": record.sensitivity,
            }
        )
    return context


def _memory_query_terms(query: str) -> tuple[str, set[str]]:
    normalized = " ".join(query.strip().lower().split())
    latin_terms = set(re.findall(r"[a-z0-9_\-]{2,}", normalized))
    cjk_terms: set[str] = set()
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        cjk_terms.add(chunk)
        cjk_terms.update(chunk[index : index + 2] for index in range(max(len(chunk) - 1, 0)))
    return normalized, latin_terms | cjk_terms


def _previous_deliverable_context(session: Session, conversation_id: str) -> list[dict[str, str]]:
    records = session.scalars(
        select(AgentDeliverableRecord)
        .where(AgentDeliverableRecord.conversation_id == conversation_id)
        .order_by(AgentDeliverableRecord.created_at.desc())
        .limit(5)
    )
    return [
        {
            "id": record.id,
            "agent_name": record.agent_name,
            "summary": record.summary[:800],
        }
        for record in records
    ]


def _write_step_artifacts(session: Session, run: AgentRunRecord, step: AgentStepRecord, result) -> None:
    deliverable = create_agent_deliverable(
        session,
        project_id=run.project_id,
        conversation_id=run.conversation_id,
        task_contract_id=run.task_contract_id,
        agent_name=step.agent_name,
        summary=result.summary,
        artifacts=result.artifacts,
        risks=result.risks,
        status="local_model_generated" if result.used_local_model else "fallback_generated",
    )
    if step.agent_name == "Review Agent":
        create_review_result(
            session,
            project_id=run.project_id,
            target_id=deliverable.id,
            approved=result.approved,
            findings=result.review_findings or ["Review Agent fallback checked the controlled step output."],
            recommendations=result.review_recommendations or ["人工确认输出是否满足验收标准"],
            reviewer="Review Agent",
            severity=result.severity,
        )


def upsert_skill(session: Session, *, skill_id: str, name: str, description: str, enabled: bool) -> SkillRecord:
    existing = get_record(session, SkillRecord, skill_id)
    if existing:
        return update_record(
            session,
            existing,
            {
                "name": name,
                "description": description,
                "enabled": enabled,
                "status": "active" if enabled else "disabled",
            },
        )
    return create_record(
        session,
        SkillRecord(
            id=skill_id,
            name=name,
            description=description,
            enabled=enabled,
            status="active" if enabled else "disabled",
        ),
    )


def list_skill_db_views() -> list[SkillDbView]:
    session = create_session()
    try:
        statement = select(SkillRecord).order_by(SkillRecord.created_at.desc())
        return [_skill_db_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def create_skill_db_view(request: SkillDbCreate) -> SkillDbView:
    session = create_session()
    try:
        findings = scan_payload(f"{request.description}\n{request.rules}")
        safety_level = classify_privacy(findings)
        status = _normalize_skill_status(request.status)
        if safety_level in {"high", "critical"}:
            status = "draft"
        record = create_record(
            session,
            SkillRecord(
                id=f"skill-{uuid4().hex[:12]}",
                name=request.name,
                category=_normalize_skill_category(request.category),
                description=request.description,
                rules=request.rules,
                status=status,
                enabled=status == "active",
            ),
        )
        return _skill_db_view(record)
    finally:
        session.close()


def update_skill_db_view(skill_id: str, request: SkillDbUpdate) -> SkillDbView:
    session = create_session()
    try:
        record = get_record(session, SkillRecord, skill_id)
        if record is None:
            raise ValueError(f"Skill not found: {skill_id}")
        values: dict[str, object] = {}
        if request.name is not None:
            values["name"] = request.name
        if request.category is not None:
            values["category"] = _normalize_skill_category(request.category)
        if request.description is not None:
            values["description"] = request.description
        if request.rules is not None:
            values["rules"] = request.rules
        if request.status is not None:
            status = _normalize_skill_status(request.status)
            values["status"] = status
            values["enabled"] = status == "active"
        preview_description = str(values.get("description", record.description))
        preview_rules = str(values.get("rules", record.rules))
        safety_level = classify_privacy(scan_payload(f"{preview_description}\n{preview_rules}"))
        if safety_level in {"high", "critical"} and values.get("status") == "active":
            values["status"] = "draft"
            values["enabled"] = False
        updated = update_record(session, record, values)
        return _skill_db_view(updated)
    finally:
        session.close()


def disable_skill_db_view(skill_id: str) -> SkillDbView:
    return update_skill_db_view(skill_id, SkillDbUpdate(status="disabled"))


def check_skill_conflict(name: str, category: str) -> SkillConflictResponse:
    normalized_category = _normalize_skill_category(category)
    normalized_name = _normalize_name(name)
    matches: list[SkillDbView] = []

    for skill in list_skill_db_views():
        if skill.category != normalized_category:
            continue
        score = SequenceMatcher(None, normalized_name, _normalize_name(skill.name)).ratio()
        if score >= 0.72 or normalized_name in _normalize_name(skill.name) or _normalize_name(skill.name) in normalized_name:
            matches.append(skill)

    return SkillConflictResponse(
        result="possible_conflict" if matches else "no_conflict",
        matches=matches,
        reason="同 category 且名称相似，mock 规则判定为可能冲突。" if matches else "未发现同类相似名称 Skill。",
    )


def create_memory_item(
    session: Session,
    *,
    project_id: str,
    title: str,
    content: str,
    sensitivity: str = "normal",
    status: str = "pending",
    source: str = "mock-orchestrator",
) -> MemoryItemRecord:
    return create_record(
        session,
        MemoryItemRecord(
            project_id=project_id,
            title=title,
            content=content,
            sensitivity=sensitivity,
            status=status,
            source=source,
        ),
    )


def list_memory_item_views(project_id: str | None = None) -> list[MemoryItemDbView]:
    session = create_session()
    try:
        statement = select(MemoryItemRecord).order_by(MemoryItemRecord.created_at.desc())
        if project_id:
            statement = (
                select(MemoryItemRecord)
                .where((MemoryItemRecord.project_id == project_id) | (MemoryItemRecord.scope == "global"))
                .order_by(MemoryItemRecord.created_at.desc())
            )
        return [_memory_item_db_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def search_memory_item_views(query: str, project_id: str | None = None) -> list[MemoryItemDbView]:
    normalized = query.strip().lower()
    session = create_session()
    try:
        statement = select(MemoryItemRecord).where(MemoryItemRecord.status == "active").order_by(MemoryItemRecord.created_at.desc())
        if project_id:
            statement = statement.where((MemoryItemRecord.project_id == project_id) | (MemoryItemRecord.scope == "global"))
        records = list(session.scalars(statement))
        if normalized:
            records = [
                record
                for record in records
                if normalized in record.title.lower() or normalized in record.content.lower() or normalized in record.scope.lower()
            ]
        return [_memory_item_db_view(record) for record in records[:20]]
    finally:
        session.close()


def create_memory_item_view(request: MemoryItemCreate) -> MemoryItemDbView:
    session = create_session()
    try:
        findings = scan_payload(f"{request.title}\n{request.content}")
        safety_level = classify_privacy(findings)
        sensitivity = request.sensitivity
        status = _normalize_memory_status(request.status)
        if safety_level in {"high", "critical"}:
            sensitivity = safety_level
            status = "pending"
        elif safety_level not in {"normal", "low"}:
            sensitivity = safety_level
        record = create_record(
            session,
            MemoryItemRecord(
                project_id=request.project_id,
                scope=_normalize_memory_scope(request.scope),
                title=request.title,
                content=request.content,
                sensitivity=sensitivity,
                status=status,
                source=request.source,
            ),
        )
        return _memory_item_db_view(record)
    finally:
        session.close()


def update_memory_item_view(memory_id: str, request: MemoryItemUpdate) -> MemoryItemDbView:
    session = create_session()
    try:
        record = get_record(session, MemoryItemRecord, memory_id)
        if record is None:
            raise ValueError(f"Memory item not found: {memory_id}")
        values: dict[str, object] = {}
        if request.scope is not None:
            values["scope"] = _normalize_memory_scope(request.scope)
        if request.title is not None:
            values["title"] = request.title
        if request.content is not None:
            values["content"] = request.content
        if request.sensitivity is not None:
            values["sensitivity"] = request.sensitivity
        if request.status is not None:
            values["status"] = _normalize_memory_status(request.status)
        updated = update_record(session, record, values)
        return _memory_item_db_view(updated)
    finally:
        session.close()


def disable_memory_item_view(memory_id: str) -> MemoryItemDbView:
    return update_memory_item_view(memory_id, MemoryItemUpdate(status="disabled"))


def save_memory_suggestion_view(suggestion_id: str, project_id: str | None, scope: str) -> MemoryItemDbView:
    suggestion = get_memory_suggestion(suggestion_id)
    if suggestion is None:
        raise ValueError(f"Memory suggestion not found: {suggestion_id}")
    return create_memory_item_view(
        MemoryItemCreate(
            project_id=project_id if scope != "global" else None,
            scope=_normalize_memory_scope(scope),
            title=suggestion.title,
            content=suggestion.detail,
            sensitivity="normal",
            status="active",
            source=f"suggestion:{suggestion_id}",
        )
    )


def create_security_request_record(
    session: Session,
    *,
    project_id: str | None,
    action: str,
    reason: str,
    resource: str | None = None,
    payload_preview: str | None = None,
) -> SecurityRequestRecord:
    return create_record(
        session,
        SecurityRequestRecord(
            project_id=project_id,
            action=action,
            reason=reason,
            resource=resource,
            payload_preview=payload_preview,
        ),
    )


def create_network_audit_log(
    session: Session,
    *,
    action: str,
    destination: str,
    reason: str,
    project_id: str | None = None,
) -> NetworkAuditLogRecord:
    return create_record(
        session,
        NetworkAuditLogRecord(
            project_id=project_id,
            action=action,
            destination=destination,
            allowed=False,
            reason=reason,
            mode="mock",
        ),
    )


def create_uploaded_file_record(
    session: Session,
    *,
    project_id: str,
    original_filename: str,
    stored_filename: str,
    size_bytes: int,
    extension: str,
    relative_path: str,
    sha256: str,
    scanner_findings: Sequence[str],
) -> UploadedFileRecord:
    return create_record(
        session,
        UploadedFileRecord(
            project_id=project_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            size_bytes=size_bytes,
            extension=extension,
            relative_path=relative_path,
            sha256=sha256,
            scanner_findings_json=to_json(scanner_findings),
        ),
    )


def list_uploaded_file_views(project_id: str) -> list[UploadedFileView]:
    session = create_session()
    try:
        statement = (
            select(UploadedFileRecord)
            .where(UploadedFileRecord.project_id == project_id)
            .order_by(UploadedFileRecord.created_at.desc())
        )
        return [_uploaded_file_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def inspect_uploaded_file(file_id: str) -> FileInspectResponse:
    session = create_session()
    try:
        record = get_record(session, UploadedFileRecord, file_id)
        if record is None:
            raise ValueError(f"Uploaded file not found: {file_id}")
        can_parse = record.extension.lower() in {".txt", ".md", ".csv", ".py", ".cpp", ".java", ".tex", ".bib"}
        return FileInspectResponse(
            file_id=record.id,
            original_filename=record.original_filename,
            size_bytes=record.size_bytes,
            extension=record.extension,
            sha256=record.sha256,
            status=record.status,
            can_parse_preview=can_parse,
            parse_preview_enabled=False,
            message="文件仍处于 quarantine；本轮仅返回元数据，不读取文件内容。",
        )
    finally:
        session.close()


def parse_uploaded_file_preview(file_id: str) -> FileParsePreviewResponse:
    session = create_session()
    try:
        record = get_record(session, UploadedFileRecord, file_id)
        if record is None:
            raise ValueError(f"Uploaded file not found: {file_id}")
        return FileParsePreviewResponse(
            file_id=record.id,
            blocked=True,
            summary="parse-preview 当前为安全占位接口，未读取上传文件内容。",
            redacted_preview="",
            message="根据当前项目安全边界，本轮不读取 quarantine 文件内容；后续可加入显式 approval_id 后启用受限解析。",
        )
    finally:
        session.close()


def list_task_contract_views(conversation_id: str) -> list[TaskContractView]:
    session = create_session()
    try:
        statement = (
            select(TaskContractRecord)
            .where(TaskContractRecord.conversation_id == conversation_id)
            .order_by(TaskContractRecord.created_at.desc())
        )
        return [_task_contract_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def list_agent_deliverable_views(conversation_id: str) -> list[AgentDeliverableView]:
    session = create_session()
    try:
        statement = (
            select(AgentDeliverableRecord)
            .where(AgentDeliverableRecord.conversation_id == conversation_id)
            .order_by(AgentDeliverableRecord.created_at.desc())
        )
        return [_agent_deliverable_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def list_review_result_views(conversation_id: str) -> list[ReviewResultView]:
    session = create_session()
    try:
        task_ids = list(
            session.scalars(select(TaskContractRecord.id).where(TaskContractRecord.conversation_id == conversation_id))
        )
        deliverable_ids = list(
            session.scalars(
                select(AgentDeliverableRecord.id).where(AgentDeliverableRecord.conversation_id == conversation_id)
            )
        )
        target_ids = task_ids + deliverable_ids
        if not target_ids:
            return []
        statement = (
            select(ReviewResultRecord)
            .where(ReviewResultRecord.target_id.in_(target_ids))
            .order_by(ReviewResultRecord.created_at.desc())
        )
        return [_review_result_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def confirm_requirement(conversation_id: str) -> ConversationView:
    return update_conversation_state_by_id(conversation_id, "waiting_outline_confirmation")


def confirm_outline(conversation_id: str) -> ConversationView:
    session = create_session()
    try:
        conversation = get_record(session, ConversationRecord, conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")
        update_conversation_state(session, conversation, "ready_for_agent_run")
        session.refresh(conversation)
        return _conversation_view(conversation)
    finally:
        session.close()


def list_security_request_views(project_id: str | None = None, limit: int = 20) -> list[SecurityRequestView]:
    session = create_session()
    try:
        statement = select(SecurityRequestRecord).order_by(SecurityRequestRecord.created_at.desc()).limit(limit)
        if project_id:
            statement = (
                select(SecurityRequestRecord)
                .where(SecurityRequestRecord.project_id == project_id)
                .order_by(SecurityRequestRecord.created_at.desc())
                .limit(limit)
            )
        return [_security_request_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def list_network_audit_log_views(project_id: str | None = None, limit: int = 20) -> list[NetworkAuditLogView]:
    session = create_session()
    try:
        statement = select(NetworkAuditLogRecord).order_by(NetworkAuditLogRecord.created_at.desc()).limit(limit)
        if project_id:
            statement = (
                select(NetworkAuditLogRecord)
                .where(NetworkAuditLogRecord.project_id == project_id)
                .order_by(NetworkAuditLogRecord.created_at.desc())
                .limit(limit)
            )
        return [_network_audit_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def get_latest_conversation(session: Session, project_id: str) -> ConversationRecord | None:
    statement = (
        select(ConversationRecord)
        .where(ConversationRecord.project_id == project_id)
        .order_by(ConversationRecord.created_at.desc())
        .limit(1)
    )
    return session.scalars(statement).first()


def write_network_audit_log(log: NetworkAuditLog) -> NetworkAuditLogRecord:
    session = create_session()
    try:
        return create_network_audit_log(
            session,
            project_id=log.project_id,
            action=log.action,
            destination=log.destination,
            reason=log.reason,
        )
    finally:
        session.close()


def _project_view(record: ProjectRecord) -> ProjectView:
    return ProjectView(
        id=record.id,
        name=record.name,
        description=record.description,
        owner=record.owner,
        status=record.status,
        created_at=record.created_at,
    )


def _conversation_view(record: ConversationRecord) -> ConversationView:
    return ConversationView(
        id=record.id,
        project_id=record.project_id,
        title=record.title,
        status=record.status,
        current_state=record.current_state,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _message_view(record: MessageRecord) -> MessageView:
    return MessageView(
        id=record.id,
        conversation_id=record.conversation_id,
        role=record.role,
        content=record.content,
        created_at=record.created_at,
    )


def _uploaded_file_view(record: UploadedFileRecord) -> UploadedFileView:
    return UploadedFileView(
        id=record.id,
        project_id=record.project_id,
        original_filename=record.original_filename,
        size_bytes=record.size_bytes,
        extension=record.extension,
        relative_path=record.relative_path,
        sha256=record.sha256,
        status=record.status,
        created_at=record.created_at,
    )


def _security_request_view(record: SecurityRequestRecord) -> SecurityRequestView:
    return SecurityRequestView(
        id=record.id,
        project_id=record.project_id,
        action=record.action,
        reason=record.reason,
        requested_by=record.requested_by,
        resource=record.resource,
        status=record.status,
        created_at=record.created_at,
    )


def _network_audit_view(record: NetworkAuditLogRecord) -> NetworkAuditLogView:
    return NetworkAuditLogView(
        id=record.id,
        project_id=record.project_id,
        action=record.action,
        destination=record.destination,
        allowed=record.allowed,
        reason=record.reason,
        mode=record.mode,
        created_at=record.created_at,
    )


def _task_contract_view(record: TaskContractRecord) -> TaskContractView:
    metadata = from_json_dict(record.metadata_json)
    return TaskContractView(
        id=record.id,
        project_id=record.project_id,
        conversation_id=record.conversation_id,
        title=record.title,
        objective=record.objective,
        inputs=from_json_list(record.inputs_json),
        outputs=from_json_list(record.outputs_json),
        constraints=from_json_list(record.constraints_json),
        acceptance_criteria=from_json_list(record.acceptance_criteria_json),
        steps=from_json_object_list(record.task_steps_json),
        metadata=metadata,
        selected_skill=_metadata_str(metadata, "selected_skill"),
        recommended_executor=_metadata_str(metadata, "recommended_executor"),
        pipeline_steps=_metadata_object_list(metadata, "pipeline_steps"),
        model_roles=_metadata_str_list(metadata, "model_roles"),
        recommended_models=_metadata_object_list(metadata, "recommended_models"),
        privacy_level=_metadata_str(metadata, "privacy_level"),
        external_allowed=bool(metadata.get("external_allowed", False)),
        requires_redaction=bool(metadata.get("requires_redaction", False)),
        sanitized_prompt=_metadata_str(metadata, "sanitized_prompt") or "",
        redaction_notes=_metadata_str_list(metadata, "redaction_notes"),
        api_safe_context=_metadata_str(metadata, "api_safe_context") or "",
        local_only_context=bool(metadata.get("local_only_context", True)),
        estimated_cost_level=_metadata_str(metadata, "estimated_cost_level"),
        requires_user_confirmation=bool(metadata.get("requires_user_confirmation", False)),
        risk_level=_metadata_str(metadata, "risk_level") or "normal",
        execution_allowed=bool(metadata.get("execution_allowed", True)),
        blocked_reasons=_metadata_str_list(metadata, "blocked_reasons"),
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _agent_deliverable_view(record: AgentDeliverableRecord) -> AgentDeliverableView:
    return AgentDeliverableView(
        id=record.id,
        project_id=record.project_id,
        conversation_id=record.conversation_id,
        task_contract_id=record.task_contract_id,
        agent_name=record.agent_name,
        summary=record.summary,
        artifacts=from_json_value_list(record.artifacts_json),
        risks=from_json_list(record.risks_json),
        status=record.status,
        created_at=record.created_at,
    )


def _review_result_view(record: ReviewResultRecord) -> ReviewResultView:
    return ReviewResultView(
        id=record.id,
        project_id=record.project_id,
        target_id=record.target_id,
        reviewer=record.reviewer,
        approved=record.approved,
        severity=record.severity,
        findings=from_json_list(record.findings_json),
        recommendations=from_json_list(record.recommendations_json),
        created_at=record.created_at,
    )


def _skill_db_view(record: SkillRecord) -> SkillDbView:
    return SkillDbView(
        id=record.id,
        name=record.name,
        category=record.category,
        description=record.description,
        rules=record.rules,
        status=record.status,
        enabled=record.enabled,
        safety_warnings=_safety_warning_labels(scan_payload(f"{record.description}\n{record.rules}")),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _agent_run_view(record: AgentRunRecord) -> AgentRunView:
    return AgentRunView(
        id=record.id,
        project_id=record.project_id,
        conversation_id=record.conversation_id,
        task_contract_id=record.task_contract_id,
        model_provider_id=record.model_provider_id,
        model_name=record.model_name,
        status=record.status,
        current_step_index=record.current_step_index,
        cancel_requested=record.cancel_requested,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _agent_step_view(record: AgentStepRecord) -> AgentStepView:
    execution_metadata = from_json_dict(record.execution_metadata_json)
    return AgentStepView(
        id=record.id,
        run_id=record.run_id,
        step_index=record.step_index,
        pipeline_step_id=record.pipeline_step_id,
        step_name=record.step_name,
        step_type=record.step_type,
        model_role=record.model_role,
        agent_name=record.agent_name,
        skill_ids=from_json_list(record.skill_ids_json),
        selected_provider_id=record.selected_provider_id,
        selected_model_id=record.selected_model_id,
        status=record.status,
        requires_user_approval=record.requires_user_approval,
        input_summary=record.input_summary,
        output_summary=record.output_summary,
        risk_level=record.risk_level,
        cost_estimate=record.cost_estimate,
        input_tokens=int(_safe_float(execution_metadata.get("input_tokens"), 0.0)),
        output_tokens=int(_safe_float(execution_metadata.get("output_tokens"), 0.0)),
        estimated_cost=_safe_float(execution_metadata.get("estimated_cost"), 0.0),
        latency_ms=record.latency_ms,
        quality_score=record.quality_score,
        final_score=_safe_float(execution_metadata.get("final_score"), 0.0),
        selected_reason=_metadata_str(execution_metadata, "selected_reason"),
        alternatives=_metadata_object_list(execution_metadata, "alternatives"),
        evaluation_status=_metadata_str(execution_metadata, "evaluation_status") or "pending",
        error_message=record.error_message,
        execution_metadata=execution_metadata,
        started_at=record.started_at,
        finished_at=record.finished_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _metadata_str(metadata: dict[str, object], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) else None


def _metadata_str_list(metadata: dict[str, object], key: str) -> list[str]:
    value = metadata.get(key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _metadata_object_list(metadata: dict[str, object], key: str) -> list[dict[str, object]]:
    value = metadata.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _memory_item_db_view(record: MemoryItemRecord) -> MemoryItemDbView:
    return MemoryItemDbView(
        id=record.id,
        project_id=record.project_id,
        scope=record.scope,
        title=record.title,
        content=record.content,
        sensitivity=record.sensitivity,
        status=record.status,
        source=record.source,
        safety_warnings=_safety_warning_labels(scan_payload(f"{record.title}\n{record.content}")),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _normalize_skill_category(category: str) -> str:
    allowed = {"code", "writing", "drawing", "research", "others"}
    return category if category in allowed else "others"


def _normalize_skill_status(status: str) -> str:
    allowed = {"active", "disabled", "draft"}
    return status if status in allowed else "draft"


def _normalize_memory_scope(scope: str) -> str:
    allowed = {"global", "project", "writing_style", "output_format", "skill"}
    return scope if scope in allowed else "project"


def _normalize_memory_status(status: str) -> str:
    allowed = {"pending", "active", "disabled"}
    return status if status in allowed else "pending"


def _normalize_name(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _safety_warning_labels(findings) -> list[str]:
    sensitive_types = {"api_key", "token", "local_path", "url", "email"}
    warnings: list[str] = []
    for finding in findings:
        if finding.type in sensitive_types or finding.severity in {"high", "critical"}:
            label = f"{finding.type}:{finding.severity}"
            if label not in warnings:
                warnings.append(label)
    return warnings
