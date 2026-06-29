import json
from dataclasses import dataclass
from typing import Any

from app.model_gateway.service import MASTER_REQUIREMENT_PROMPT_ID, invoke_local_model
from app.schemas.model_gateway import LocalModelInvokeRequest
from app.schemas.workbench import OutlineCard, RequirementCard

MAX_CARD_ITEMS = 8
MAX_ITEM_CHARS = 200
MAX_STEPS = 8
ALLOWED_AGENTS = {"Planner", "Writer", "Code Agent", "Research Agent", "Formatting Agent", "Review Agent"}


@dataclass
class LocalMasterAgentResult:
    requirement_card: RequirementCard
    outline_card: OutlineCard
    task_type: str
    missing_info: list[str]
    safety_notes: list[str]
    task_contract_steps: list[dict[str, object]]
    response_summary: str
    blocked: bool = False
    requires_user_approval: bool = False
    fallback_used: bool = False
    safety_message: str | None = None
    approval_id: str | None = None
    prompt_hash: str | None = None


def run_local_master_agent(
    *,
    provider_id: str,
    model_name: str,
    message: str,
    user_approved: bool = False,
    approval_id: str | None = None,
) -> LocalMasterAgentResult:
    invocation = invoke_local_model(
        LocalModelInvokeRequest(
            provider_id=provider_id,
            model_name=model_name,
            prompt_template_id=MASTER_REQUIREMENT_PROMPT_ID,
            mock_task_contract={
                "objective": message,
                "inputs": ["current user message only"],
                "outputs": ["requirement_card", "outline_card", "task_contract", "missing_info", "safety_notes"],
                "constraints": ["no external API", "no web search", "no MCP", "no uploaded file content"],
                "acceptance_criteria": ["valid JSON only", "safe fallback on parse failure"],
            },
            user_approved=user_approved,
            approval_id=approval_id,
        )
    )

    if invocation.blocked and not invocation.requires_user_approval:
        fallback = _fallback_payload(message)
        return LocalMasterAgentResult(
            requirement_card=fallback.requirement_card,
            outline_card=fallback.outline_card,
            task_type=fallback.task_type,
            missing_info=fallback.missing_info,
            safety_notes=fallback.safety_notes,
            task_contract_steps=fallback.task_contract_steps,
            response_summary=invocation.message,
            blocked=True,
            requires_user_approval=False,
            fallback_used=True,
            safety_message=invocation.message,
            approval_id=invocation.approval_id,
            prompt_hash=invocation.prompt_hash,
        )

    if invocation.blocked and invocation.risk_level in {"high", "critical"}:
        fallback = _fallback_payload(message)
        return LocalMasterAgentResult(
            requirement_card=fallback.requirement_card,
            outline_card=fallback.outline_card,
            task_type=fallback.task_type,
            missing_info=fallback.missing_info,
            safety_notes=fallback.safety_notes,
            task_contract_steps=fallback.task_contract_steps,
            response_summary=invocation.message,
            blocked=True,
            requires_user_approval=False,
            fallback_used=True,
            safety_message=invocation.message,
            approval_id=invocation.approval_id,
            prompt_hash=invocation.prompt_hash,
        )

    if invocation.requires_user_approval:
        fallback = _fallback_payload(message)
        return LocalMasterAgentResult(
            requirement_card=fallback.requirement_card,
            outline_card=fallback.outline_card,
            task_type=fallback.task_type,
            missing_info=fallback.missing_info,
            safety_notes=fallback.safety_notes,
            task_contract_steps=fallback.task_contract_steps,
            response_summary=invocation.message,
            blocked=False,
            requires_user_approval=True,
            fallback_used=True,
            safety_message=invocation.message,
            approval_id=invocation.approval_id,
            prompt_hash=invocation.prompt_hash,
        )

    parsed = _parse_master_json(invocation.response_text)
    if parsed is None:
        fallback = _fallback_payload(message)
        fallback.safety_notes.append("模型输出 JSON 解析失败，已使用安全 fallback。")
        fallback.fallback_used = True
        fallback.safety_message = "模型输出 JSON 解析失败，已使用安全 fallback。"
        return fallback
    result = _result_from_payload(parsed)
    result.prompt_hash = invocation.prompt_hash
    return result


def _parse_master_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(_strip_code_fence(text.strip()))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
    return text


def _result_from_payload(payload: dict[str, Any]) -> LocalMasterAgentResult:
    requirement = payload.get("requirement_card") if isinstance(payload.get("requirement_card"), dict) else {}
    outline = payload.get("outline_card") if isinstance(payload.get("outline_card"), dict) else {}
    requirement_card = RequirementCard(
        title=str(requirement.get("title") or "需求确认"),
        status=str(requirement.get("status") or "waiting_requirement_confirmation"),
        items=_string_list(requirement.get("items"), ["确认目标、输入、输出和约束"]),
    )
    outline_card = OutlineCard(
        title=str(outline.get("title") or "大纲确认"),
        status=str(outline.get("status") or "waiting_outline_confirmation"),
        sections=_string_list(outline.get("sections"), ["任务拆解", "执行步骤", "审核交付"]),
    )
    missing_info = _string_list(payload.get("missing_info"), [])
    safety_notes = _string_list(payload.get("safety_notes"), ["本地模型输出已解析为结构化卡片。"])
    task_contract = payload.get("task_contract") if isinstance(payload.get("task_contract"), dict) else {}
    task_contract_steps = _task_steps(task_contract.get("steps"))
    task_type = str(payload.get("task_type") or "local_requirement_analysis")
    return LocalMasterAgentResult(
        requirement_card=requirement_card,
        outline_card=outline_card,
        task_type=task_type,
        missing_info=missing_info,
        safety_notes=safety_notes,
        task_contract_steps=task_contract_steps,
        response_summary="主控 Agent 使用本地模型生成需求确认和大纲。",
    )


def _fallback_payload(message: str) -> LocalMasterAgentResult:
    return LocalMasterAgentResult(
        requirement_card=RequirementCard(
            title="需求确认",
            status="waiting_requirement_confirmation",
            items=[
                f"用户需求摘要：{message.strip()[:160]}",
                "确认目标、输入、输出和约束。",
                "确认是否需要本地模型继续生成任务协议。",
            ],
        ),
        outline_card=OutlineCard(
            title="初始大纲",
            status="waiting_outline_confirmation",
            sections=["需求澄清", "任务拆解", "本地执行边界", "审核与交付"],
        ),
        task_type="fallback_requirement_analysis",
        missing_info=["请补充验收标准、输出格式和限制条件。"],
        safety_notes=["未读取上传文件内容，未联网，未调用外部 API。"],
        task_contract_steps=[
            {
                "step_index": 1,
                "agent": "Planner",
                "skill_ids": ["skill-planning"],
                "goal": _truncate_item(f"澄清并规划：{message.strip()}"),
                "expected_output": "可审核执行计划",
                "requires_approval": False,
            },
            {
                "step_index": 2,
                "agent": "Review Agent",
                "skill_ids": ["skill-review"],
                "goal": "审核任务边界与验收标准",
                "expected_output": "审核结果",
                "requires_approval": False,
            },
        ],
        response_summary="主控 Agent 使用 fallback 需求确认和大纲。",
    )


def _string_list(value: object, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        items = [_truncate_item(str(item).strip()) for item in value if str(item).strip()]
        items = items[:MAX_CARD_ITEMS]
        return items or fallback
    if isinstance(value, str) and value.strip():
        return [_truncate_item(value.strip())]
    return fallback


def _truncate_item(value: str) -> str:
    if len(value) <= MAX_ITEM_CHARS:
        return value
    return value[:MAX_ITEM_CHARS].rstrip()


def _task_steps(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return _fallback_payload("").task_contract_steps
    steps: list[dict[str, object]] = []
    for index, raw_step in enumerate(value[:MAX_STEPS], start=1):
        if not isinstance(raw_step, dict):
            continue
        agent = str(raw_step.get("agent") or raw_step.get("agent_name") or "Planner")
        if agent not in ALLOWED_AGENTS:
            agent = "Planner"
        skill_ids = raw_step.get("skill_ids")
        safe_skill_ids = []
        if isinstance(skill_ids, list):
            safe_skill_ids = [str(item)[:80] for item in skill_ids if isinstance(item, str) and item.startswith("skill-")][:8]
        steps.append(
            {
                "step_index": int(raw_step.get("step_index") or index),
                "agent": agent,
                "skill_ids": safe_skill_ids,
                "goal": _truncate_item(str(raw_step.get("goal") or "")),
                "expected_output": _truncate_item(str(raw_step.get("expected_output") or "")),
                "requires_approval": bool(raw_step.get("requires_approval", False)),
            }
        )
    return steps or _fallback_payload("").task_contract_steps
