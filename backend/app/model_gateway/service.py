from dataclasses import dataclass
import hashlib
import json
from datetime import UTC, datetime, timedelta
from string import Formatter
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

from sqlalchemy import select

from app.database.crud import create_record, get_record, update_record
from app.database.models import (
    ModelInvocationApprovalRecord,
    ModelInvocationLogRecord,
    ModelProviderRecord,
    PromptTemplateRecord,
    TaskContractRecord,
)
from app.database.service import from_json_list
from app.database.session import create_session
from app.schemas.model_gateway import (
    LocalModelInfo,
    LocalModelInvokeRequest,
    LocalModelInvokeResponse,
    LocalModelListResponse,
    LocalModelProviderTestRequest,
    ModelInvocationApprovalIntent,
    ModelInvocationApprovalReview,
    ModelInvocationLogView,
    ModelInvocationRequest,
    ModelInvocationReview,
    ModelProviderCheckResult,
    ModelProviderCreate,
    ModelProviderUpdate,
    ModelProviderView,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateView,
)
from app.schemas.security import PayloadFinding
from app.schemas.workbench import ModelOption
from app.security.payload_scanner import scan_payload
from app.security.privacy_classifier import classify_privacy
from app.security.query_redactor import redact_query

ALLOWED_PROVIDER_TYPES = {"mock", "local", "local_ollama", "remote_api", "desktop_tool", "external_disabled"}
ALLOWED_PROVIDER_STATUS = {"draft", "active", "disabled"}
ALLOWED_PROMPT_STATUS = {"draft", "active", "disabled"}
ALLOWED_LOCAL_ENDPOINTS = {
    "http://127.0.0.1:11434",
    "http://localhost:11434",
}
BLOCKING_RISK_LEVELS = {"high", "critical"}
MEDIUM_RISK_LEVELS = {"medium"}
DEFAULT_PROVIDER_ID = "provider-mock-local"
DEFAULT_PROMPT_ID = "prompt-task-contract-default"
MASTER_REQUIREMENT_PROMPT_ID = "prompt-master-requirement-analysis"
ALLOWED_TEMPLATE_FIELDS = {"title", "objective", "inputs", "outputs", "constraints", "acceptance_criteria"}
LOCAL_TIMEOUT_SECONDS = 8
MAX_LOCAL_RESPONSE_BYTES = 1024 * 1024
OLLAMA_CONTEXT_PRESETS = {
    "fallback_4096": 4096,
    "default_8192": 8192,
    "experimental_16384": 16384,
}
MASTER_REQUIREMENT_TEMPLATE = (
    "You are the master agent of a local-only workbench. "
    "Do not use external APIs, web search, MCP, tools, or uploaded file contents.\n"
    "Convert the user request into strict JSON only. Do not wrap it in markdown.\n"
    "User request: {objective}\n"
    "The JSON object must include exactly these top-level fields: "
    "requirement_card, outline_card, task_type, task_contract, missing_info, safety_notes.\n"
    "requirement_card must include title, status, items.\n"
    "outline_card must include title, status, sections.\n"
    "task_contract must include objective, inputs, outputs, constraints, acceptance_criteria, steps.\n"
    "Each task_contract.steps item must include step_index, agent, skill_ids, goal, expected_output, requires_approval.\n"
    "Allowed agent values are only: Planner, Writer, Code Agent, Research Agent, Formatting Agent, Review Agent.\n"
    "skill_ids must be an array of local skill id strings. missing_info and safety_notes must be arrays."
)


@dataclass
class AgentLocalModelInvokeResult:
    blocked: bool
    risk_level: str
    requires_user_approval: bool
    provider_id: str | None
    model_name: str | None
    response_text: str
    redacted_prompt_preview: str
    findings: list[str]
    message: str
    prompt_hash: str
    prompt_length: int
    used_local_model: bool


def get_available_models() -> list[ModelOption]:
    return [
        ModelOption(
            id="mock-local-planner",
            name="Mock Local Planner",
            provider="mock",
            enabled=True,
            description="本地 mock 模型选项，仅用于界面和状态机演示。",
        ),
        ModelOption(
            id="mock-local-coder",
            name="Mock Local Coder",
            provider="mock",
            enabled=True,
            description="本地 mock 代码模型选项，不执行真实推理。",
        ),
        ModelOption(
            id="local-provider-placeholder",
            name="Local Ollama",
            provider="local_ollama",
            enabled=False,
            description="Only local Ollama is currently callable; remote_api and desktop_tool are mock placeholders.",
        ),
    ]


def list_model_provider_views() -> list[ModelProviderView]:
    session = create_session()
    try:
        ensure_default_model_gateway_records(session)
        records = session.scalars(select(ModelProviderRecord).order_by(ModelProviderRecord.created_at.desc()))
        return [_model_provider_view(record) for record in records]
    finally:
        session.close()


def list_model_invocation_log_views(limit: int = 50) -> list[ModelInvocationLogView]:
    session = create_session()
    try:
        statement = select(ModelInvocationLogRecord).order_by(ModelInvocationLogRecord.created_at.desc()).limit(limit)
        return [_model_invocation_log_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def create_model_provider_view(request: ModelProviderCreate) -> ModelProviderView:
    session = create_session()
    try:
        provider_type = _normalize_provider_type(request.provider_type)
        endpoint = _clean_endpoint(request.endpoint, provider_type)
        record = create_record(
            session,
            ModelProviderRecord(
                name=request.name,
                provider_type=provider_type,
                endpoint=endpoint,
                enabled=_provider_enabled(provider_type, request.enabled),
                privacy_mode=request.privacy_mode or "local_only",
                status=_normalize_provider_status(request.status, provider_type),
            ),
        )
        return _model_provider_view(record)
    finally:
        session.close()


def update_model_provider_view(provider_id: str, request: ModelProviderUpdate) -> ModelProviderView:
    session = create_session()
    try:
        record = get_record(session, ModelProviderRecord, provider_id)
        if record is None:
            raise ValueError(f"Model provider not found: {provider_id}")

        provider_type = _normalize_provider_type(request.provider_type or record.provider_type)
        values: dict[str, object] = {"provider_type": provider_type}
        if request.name is not None:
            values["name"] = request.name
        if request.endpoint is not None:
            values["endpoint"] = _clean_endpoint(request.endpoint, provider_type)
        if request.enabled is not None:
            values["enabled"] = _provider_enabled(provider_type, request.enabled)
        if request.privacy_mode is not None:
            values["privacy_mode"] = request.privacy_mode or "local_only"
        if request.status is not None:
            values["status"] = _normalize_provider_status(request.status, provider_type)
        if provider_type == "external_disabled":
            values["endpoint"] = None
            values["enabled"] = False
            values["status"] = "disabled"
        return _model_provider_view(update_record(session, record, values))
    finally:
        session.close()


def disable_model_provider_view(provider_id: str) -> ModelProviderView:
    return update_model_provider_view(provider_id, ModelProviderUpdate(enabled=False, status="disabled"))


def check_model_provider(provider_id: str) -> ModelProviderCheckResult:
    provider = _load_local_provider(provider_id)
    provider_kind = _provider_kind(provider.endpoint or "")
    path = _detection_path(provider_kind)
    ok, data, message = _local_json_request(provider.endpoint or "", path, method="GET")
    return ModelProviderCheckResult(
        provider_id=provider_id,
        reachable=ok,
        message="Local model provider is reachable." if ok else message,
        provider_kind=provider_kind,
    )


def list_local_model_views(provider_id: str) -> LocalModelListResponse:
    provider = _load_local_provider(provider_id)
    provider_kind = _provider_kind(provider.endpoint or "")
    path = _detection_path(provider_kind)
    ok, data, message = _local_json_request(provider.endpoint or "", path, method="GET")
    if not ok:
        return LocalModelListResponse(provider_id=provider_id, reachable=False, models=[], message=message)
    return LocalModelListResponse(
        provider_id=provider_id,
        reachable=True,
        models=_extract_models(provider_kind, data),
        message="Local model list loaded.",
    )


def test_model_provider(provider_id: str, request: LocalModelProviderTestRequest) -> LocalModelInvokeResponse:
    provider = _load_local_provider(provider_id)
    if not provider.enabled or provider.status != "active":
        raise ValueError("Local provider must be enabled and active before invocation.")
    provider_kind = _provider_kind(provider.endpoint or "")
    prompt = "Respond with exactly: ok"
    findings = scan_payload(prompt)
    risk_level = classify_privacy(findings)
    if risk_level in BLOCKING_RISK_LEVELS:
        raise ValueError("Local provider test prompt was blocked by safety review.")
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    ok, data, message = _invoke_provider(
        provider.endpoint or "",
        provider_kind,
        request.model_name,
        prompt,
        options=_default_ollama_options(),
    )
    _write_invocation_log(
        provider_id=provider_id,
        prompt_template_id=None,
        task_contract_id=None,
        model_id=request.model_name,
        provider_type=provider.provider_type,
        mode="local_test",
        prompt_hash=prompt_hash,
        prompt_length=len(prompt),
        risk_level=risk_level,
        blocked=not ok,
        findings=findings,
        input_tokens=_estimate_tokens(prompt),
        output_tokens=_estimate_tokens(_extract_response_text(provider_kind, data) if ok else ""),
        output_hash=_hash_text(_extract_response_text(provider_kind, data)) if ok else None,
        success=ok,
        schema_valid=ok,
        sanitized_input_hash=prompt_hash,
        error_code=None if ok else "local_test_failed",
        blocked_reason=None if ok else message,
    )
    return LocalModelInvokeResponse(
        blocked=not ok,
        risk_level=risk_level,
        requires_user_approval=False,
        provider_id=provider_id,
        model_name=request.model_name,
        response_text=_extract_response_text(provider_kind, data) if ok else "",
        redacted_prompt_preview=prompt,
        findings=[_finding_label(finding) for finding in findings],
        message="Local provider test completed." if ok else message,
    )


def list_prompt_template_views() -> list[PromptTemplateView]:
    session = create_session()
    try:
        ensure_default_model_gateway_records(session)
        records = session.scalars(select(PromptTemplateRecord).order_by(PromptTemplateRecord.created_at.desc()))
        return [_prompt_template_view(record) for record in records]
    finally:
        session.close()


def create_prompt_template_view(request: PromptTemplateCreate) -> PromptTemplateView:
    session = create_session()
    try:
        record = create_record(
            session,
            PromptTemplateRecord(
                name=request.name,
                task_type=request.task_type,
                template_text=request.template_text,
                safety_notes=request.safety_notes,
                status=_normalize_prompt_status(request.status),
            ),
        )
        return _prompt_template_view(record)
    finally:
        session.close()


def update_prompt_template_view(prompt_id: str, request: PromptTemplateUpdate) -> PromptTemplateView:
    session = create_session()
    try:
        record = get_record(session, PromptTemplateRecord, prompt_id)
        if record is None:
            raise ValueError(f"Prompt template not found: {prompt_id}")
        values = request.model_dump(exclude_unset=True)
        if "status" in values:
            values["status"] = _normalize_prompt_status(str(values["status"]))
        return _prompt_template_view(update_record(session, record, values))
    finally:
        session.close()


def preview_prompt(request: ModelInvocationRequest) -> ModelInvocationReview:
    context = _build_prompt_context(request)
    _write_invocation_log(
        provider_id=context["provider_id"],
        prompt_template_id=context["prompt_template_id"],
        task_contract_id=request.task_contract_id,
        mode="mock_preview",
        prompt_hash=context["prompt_hash"],
        prompt_length=context["prompt_length"],
        risk_level=context["risk_level"],
        blocked=context["blocked"],
        findings=context["findings"],
    )
    return ModelInvocationReview(
        blocked=context["blocked"],
        risk_level=context["risk_level"],
        prompt_preview=context["redacted_preview"],
        raw_preview_available=not context["blocked"],
        redacted_prompt_preview=context["redacted_preview"],
        prompt_hash=context["prompt_hash"],
        prompt_length=context["prompt_length"],
        findings=[_finding_label(finding) for finding in context["findings"]],
        message=(
            "Prompt preview blocked by local payload scanner; no model call was made."
            if context["blocked"]
            else "Mock prompt preview generated locally; no model call was made."
        ),
    )


def review_model_invocation(request: ModelInvocationRequest) -> ModelInvocationApprovalReview:
    context = _build_prompt_context(request)
    requires_user_approval = context["risk_level"] in {"medium", "high", "critical"}
    if context["blocked"]:
        recommendation = "Blocked. Remove high-risk or critical content before any local model invocation."
    elif requires_user_approval:
        recommendation = "Requires explicit user approval before local model invocation."
    else:
        recommendation = "Low-risk review. Local invocation can proceed if provider is local and reachable."
    return ModelInvocationApprovalReview(
        risk_level=context["risk_level"],
        blocked=context["blocked"],
        requires_user_approval=requires_user_approval,
        redacted_preview=context["redacted_preview"],
        findings=[_finding_label(finding) for finding in context["findings"]],
        recommendation=recommendation,
    )


def create_model_invocation_approval_intent(request: ModelInvocationRequest) -> ModelInvocationApprovalIntent:
    context = _build_prompt_context(request)
    findings = [_finding_label(finding) for finding in context["findings"]]
    blocked = bool(context["blocked"])
    requires_user_approval = context["risk_level"] in MEDIUM_RISK_LEVELS and not blocked
    status = "blocked" if blocked else "pending" if requires_user_approval else "not_required"
    expires_at = datetime.now(UTC) + timedelta(minutes=15) if requires_user_approval else None
    approval_id: str | None = None
    if requires_user_approval and expires_at is not None:
        session = create_session()
        try:
            record = create_record(
                session,
                ModelInvocationApprovalRecord(
                    provider_id=context["provider_id"],
                    prompt_template_id=context["prompt_template_id"],
                    task_contract_id=request.task_contract_id,
                    prompt_hash=context["prompt_hash"],
                    prompt_length=context["prompt_length"],
                    risk_level=context["risk_level"],
                    findings_json=_finding_summary_json(context["findings"]),
                    redacted_preview=_truncate_preview(str(context["redacted_preview"]), limit=2000),
                    status="pending",
                    expires_at=expires_at,
                ),
            )
            approval_id = record.id
        finally:
            session.close()
    if blocked:
        message = "Approval intent was blocked by safety review; no model call is allowed."
    elif requires_user_approval:
        message = "Approval intent created. Use approval_id with the unchanged prompt hash for this invocation only."
    else:
        message = "Approval is not required for this risk level."
    return ModelInvocationApprovalIntent(
        approval_id=approval_id,
        provider_id=context["provider_id"],
        prompt_template_id=context["prompt_template_id"],
        task_contract_id=request.task_contract_id,
        prompt_hash=context["prompt_hash"],
        prompt_length=context["prompt_length"],
        risk_level=context["risk_level"],
        blocked=blocked,
        requires_user_approval=requires_user_approval,
        redacted_preview=str(context["redacted_preview"]),
        findings=findings,
        status=status,
        expires_at=expires_at,
        message=message,
    )


def invoke_local_model(request: LocalModelInvokeRequest) -> LocalModelInvokeResponse:
    if not request.provider_id:
        raise ValueError("provider_id is required for local invocation")
    provider = _load_local_provider(request.provider_id)
    if not provider.enabled or provider.status != "active":
        raise ValueError("Local provider must be enabled and active before invocation.")
    provider_kind = _provider_kind(provider.endpoint or "")
    context = _build_prompt_context(request)
    review = review_model_invocation(request)

    if review.blocked:
        _write_invocation_log_from_context(
            context,
            request.task_contract_id,
            mode="local_invoke",
            blocked=True,
            model_id=request.model_name,
            provider_type=provider.provider_type,
            success=False,
            blocked_reason="safety_review_blocked",
        )
        return _blocked_local_response(request, context, review, "Blocked by local invocation review.")

    approval_used = False
    if review.risk_level in MEDIUM_RISK_LEVELS and request.approval_id:
        _validate_and_consume_approval(request.approval_id, context)
        approval_used = True

    if review.risk_level in MEDIUM_RISK_LEVELS and not request.user_approved and not approval_used:
        approval = create_model_invocation_approval_intent(request)
        _write_invocation_log_from_context(
            context,
            request.task_contract_id,
            mode="local_invoke",
            blocked=True,
            model_id=request.model_name,
            provider_type=provider.provider_type,
            success=False,
            blocked_reason="medium_requires_user_approval",
        )
        return _blocked_local_response(
            request,
            context,
            review,
            "Medium-risk prompt requires explicit approval_id before local invocation.",
            requires_user_approval=True,
            approval_id=approval.approval_id,
        )

    # MVP temporary approval gate: user_approved is a UI flag only.
    # Next stage should replace this with approval_id plus prompt_hash validation.
    medium_approved = review.risk_level in MEDIUM_RISK_LEVELS and (approval_used or request.user_approved)
    ok, data, message = _invoke_provider(
        provider.endpoint or "",
        provider_kind,
        request.model_name,
        str(context["prompt"]),
        options=_ollama_options_from_request(request),
    )
    response_text = _extract_response_text(provider_kind, data) if ok else ""
    _write_invocation_log_from_context(
        context,
        request.task_contract_id,
        mode="local_invoke",
        blocked=not ok,
        model_id=request.model_name,
        provider_type=provider.provider_type,
        output_text=response_text,
        success=ok,
        error_code=None if ok else "local_invoke_failed",
        blocked_reason=None if ok else message,
    )
    response_message = "Local model invocation completed." if ok else message
    if approval_used:
        response_message = f"{response_message} approved by approval_id + prompt_hash."
    elif medium_approved:
        response_message = f"{response_message} approved by explicit user flag."
    return LocalModelInvokeResponse(
        blocked=not ok,
        risk_level=str(context["risk_level"]),
        requires_user_approval=False,
        provider_id=request.provider_id,
        model_name=request.model_name,
        response_text=response_text,
        redacted_prompt_preview=str(context["redacted_preview"]),
        findings=[_finding_label(finding) for finding in context["findings"]],
        message=response_message,
        approval_id=request.approval_id,
        prompt_hash=str(context["prompt_hash"]),
    )


def invoke_local_model_for_agent(
    *,
    provider_id: str,
    model_name: str,
    prompt: str,
    task_contract_id: str | None = None,
    purpose: str = "agent_step",
) -> AgentLocalModelInvokeResult:
    provider = _load_local_provider(provider_id)
    if not provider.enabled or provider.status != "active":
        raise ValueError("Local provider must be enabled and active before invocation.")

    provider_kind = _provider_kind(provider.endpoint or "")
    findings = scan_payload(prompt)
    redacted_prompt, redaction_findings = redact_query(prompt)
    combined_findings = _merge_findings(findings, redaction_findings)
    risk_level = classify_privacy(combined_findings)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    prompt_length = len(prompt)
    blocked = risk_level in BLOCKING_RISK_LEVELS
    finding_labels = [_finding_label(finding) for finding in combined_findings]

    if blocked:
        _write_invocation_log(
            provider_id=provider_id,
            prompt_template_id=None,
            task_contract_id=task_contract_id,
            model_id=model_name,
            provider_type=provider.provider_type,
            mode=purpose,
            prompt_hash=prompt_hash,
            prompt_length=prompt_length,
            risk_level=risk_level,
            blocked=True,
            findings=combined_findings,
            input_tokens=_estimate_tokens(prompt),
            success=False,
            schema_valid=False,
            sanitized_input_hash=_hash_text(redacted_prompt),
            blocked_reason="safety_review_blocked",
        )
        return AgentLocalModelInvokeResult(
            blocked=True,
            risk_level=risk_level,
            requires_user_approval=False,
            provider_id=provider_id,
            model_name=model_name,
            response_text="",
            redacted_prompt_preview=_truncate_preview(redacted_prompt, limit=1000),
            findings=finding_labels,
            message="Blocked by Model Gateway safety review.",
            prompt_hash=prompt_hash,
            prompt_length=prompt_length,
            used_local_model=False,
        )

    if risk_level in MEDIUM_RISK_LEVELS:
        _write_invocation_log(
            provider_id=provider_id,
            prompt_template_id=None,
            task_contract_id=task_contract_id,
            model_id=model_name,
            provider_type=provider.provider_type,
            mode=purpose,
            prompt_hash=prompt_hash,
            prompt_length=prompt_length,
            risk_level=risk_level,
            blocked=True,
            findings=combined_findings,
            input_tokens=_estimate_tokens(prompt),
            success=False,
            schema_valid=False,
            sanitized_input_hash=_hash_text(redacted_prompt),
            blocked_reason="medium_requires_user_approval",
        )
        return AgentLocalModelInvokeResult(
            blocked=True,
            risk_level=risk_level,
            requires_user_approval=True,
            provider_id=provider_id,
            model_name=model_name,
            response_text="",
            redacted_prompt_preview=_truncate_preview(redacted_prompt, limit=1000),
            findings=finding_labels,
            message="Medium-risk agent step prompt requires approval; model was not called.",
            prompt_hash=prompt_hash,
            prompt_length=prompt_length,
            used_local_model=False,
        )

    ok, data, message = _invoke_provider(
        provider.endpoint or "",
        provider_kind,
        model_name,
        prompt,
        options=_default_ollama_options(),
    )
    response_text = _extract_response_text(provider_kind, data) if ok else ""
    _write_invocation_log(
        provider_id=provider_id,
        prompt_template_id=None,
        task_contract_id=task_contract_id,
        model_id=model_name,
        provider_type=provider.provider_type,
        mode=purpose,
        prompt_hash=prompt_hash,
        prompt_length=prompt_length,
        risk_level=risk_level,
        blocked=not ok,
        findings=combined_findings,
        input_tokens=_estimate_tokens(prompt),
        output_tokens=_estimate_tokens(response_text),
        output_hash=_hash_text(response_text) if response_text else None,
        success=ok,
        schema_valid=ok,
        sanitized_input_hash=_hash_text(redacted_prompt),
        error_code=None if ok else "local_agent_invoke_failed",
        blocked_reason=None if ok else message,
    )
    return AgentLocalModelInvokeResult(
        blocked=not ok,
        risk_level=risk_level,
        requires_user_approval=False,
        provider_id=provider_id,
        model_name=model_name,
        response_text=response_text,
        redacted_prompt_preview=_truncate_preview(redacted_prompt, limit=1000),
        findings=finding_labels,
        message="Local model agent step invocation completed." if ok else message,
        prompt_hash=prompt_hash,
        prompt_length=prompt_length,
        used_local_model=ok,
    )


def ensure_default_model_gateway_records(session) -> None:
    if get_record(session, ModelProviderRecord, DEFAULT_PROVIDER_ID) is None:
        create_record(
            session,
            ModelProviderRecord(
                id=DEFAULT_PROVIDER_ID,
                name="Mock Local Provider",
                provider_type="mock",
                endpoint=None,
                enabled=True,
                privacy_mode="local_only",
                status="active",
            ),
        )
    if get_record(session, PromptTemplateRecord, DEFAULT_PROMPT_ID) is None:
        create_record(
            session,
            PromptTemplateRecord(
                id=DEFAULT_PROMPT_ID,
                name="Default Task Contract Prompt",
                task_type="task_contract",
                template_text=(
                    "You are a local agent. Do not call external tools.\n"
                    "Objective: {objective}\n"
                    "Inputs: {inputs}\n"
                    "Outputs: {outputs}\n"
                    "Constraints: {constraints}\n"
                    "Acceptance Criteria: {acceptance_criteria}"
                ),
                safety_notes="本模板只用于本机模型调用或 prompt preview，不包含上传文件内容。",
                status="active",
            ),
        )
    master_prompt = get_record(session, PromptTemplateRecord, MASTER_REQUIREMENT_PROMPT_ID)
    if master_prompt is None:
        create_record(
            session,
            PromptTemplateRecord(
                id=MASTER_REQUIREMENT_PROMPT_ID,
                name="Master Requirement Analysis Prompt",
                task_type="master_requirement_analysis",
                template_text=MASTER_REQUIREMENT_TEMPLATE,
                safety_notes="主控 Agent 本地需求分析模板，只使用当前用户 message。",
                status="active",
            ),
        )
    else:
        update_record(
            session,
            master_prompt,
            {
                "name": "Master Requirement Analysis Prompt",
                "task_type": "master_requirement_analysis",
                "template_text": MASTER_REQUIREMENT_TEMPLATE,
                "safety_notes": "主控 Agent 本地需求分析模板，只使用当前用户 message。",
                "status": "active",
            },
        )


def _build_prompt_context(request: ModelInvocationRequest) -> dict[str, object]:
    session = create_session()
    try:
        ensure_default_model_gateway_records(session)
        provider = _get_provider_for_preview(session, request.provider_id)
        prompt_template = _get_prompt_template_for_preview(session, request.prompt_template_id)
        task_contract = _task_contract_payload(session, request.task_contract_id, request.mock_task_contract)
        prompt = _render_prompt(prompt_template.template_text, task_contract)
        findings = scan_payload(prompt)
        redacted_prompt, redaction_findings = redact_query(prompt)
        combined_findings = _merge_findings(findings, redaction_findings)
        risk_level = classify_privacy(combined_findings)
        blocked = risk_level in BLOCKING_RISK_LEVELS
        return {
            "provider_id": provider.id if provider else None,
            "prompt_template_id": prompt_template.id,
            "prompt": prompt,
            "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "prompt_length": len(prompt),
            "risk_level": risk_level,
            "blocked": blocked,
            "findings": combined_findings,
            "redacted_preview": _truncate_preview(redacted_prompt),
        }
    finally:
        session.close()


def _write_invocation_log_from_context(
    context: dict[str, object],
    task_contract_id: str | None,
    *,
    mode: str,
    blocked: bool,
    model_id: str | None = None,
    provider_type: str | None = None,
    output_text: str = "",
    success: bool | None = None,
    error_code: str | None = None,
    blocked_reason: str | None = None,
) -> None:
    _write_invocation_log(
        provider_id=context["provider_id"],
        prompt_template_id=context["prompt_template_id"],
        task_contract_id=task_contract_id,
        model_id=model_id,
        provider_type=provider_type,
        mode=mode,
        prompt_hash=context["prompt_hash"],
        prompt_length=context["prompt_length"],
        risk_level=context["risk_level"],
        blocked=blocked,
        findings=context["findings"],
        input_tokens=_estimate_tokens(str(context.get("prompt", ""))),
        output_tokens=_estimate_tokens(output_text),
        output_hash=_hash_text(output_text) if output_text else None,
        success=(not blocked) if success is None else success,
        schema_valid=not blocked,
        sanitized_input_hash=_hash_text(str(context.get("redacted_preview", ""))),
        error_code=error_code,
        blocked_reason=blocked_reason,
    )


def _write_invocation_log(
    *,
    provider_id: str | None,
    prompt_template_id: str | None,
    task_contract_id: str | None,
    model_id: str | None = None,
    skill_id: str | None = None,
    step_id: str | None = None,
    pipeline_step_id: str | None = None,
    provider_type: str | None = None,
    mode: str,
    prompt_hash: str,
    prompt_length: int,
    risk_level: str,
    blocked: bool,
    findings: list[PayloadFinding],
    input_tokens: int | None = None,
    output_tokens: int = 0,
    estimated_cost: float = 0.0,
    latency_ms: int | None = None,
    success: bool = False,
    error_code: str | None = None,
    retry_count: int = 0,
    schema_valid: bool = False,
    sanitized_input_hash: str | None = None,
    output_hash: str | None = None,
    blocked_reason: str | None = None,
) -> None:
    session = create_session()
    try:
        create_record(
            session,
            ModelInvocationLogRecord(
                provider_id=provider_id,
                prompt_template_id=prompt_template_id,
                task_contract_id=task_contract_id,
                model_id=model_id,
                skill_id=skill_id,
                step_id=step_id,
                pipeline_step_id=pipeline_step_id,
                provider_type=provider_type,
                mode=mode,
                prompt_hash=prompt_hash,
                prompt_length=prompt_length,
                input_tokens=input_tokens if input_tokens is not None else _estimate_tokens_by_length(prompt_length),
                output_tokens=output_tokens,
                estimated_cost=estimated_cost,
                latency_ms=latency_ms,
                success=success,
                error_code=error_code,
                retry_count=retry_count,
                schema_valid=schema_valid,
                sanitized_input_hash=sanitized_input_hash,
                output_hash=output_hash,
                blocked_reason=blocked_reason,
                risk_level=risk_level,
                blocked=blocked,
                findings_json=_finding_summary_json(findings),
            ),
        )
    finally:
        session.close()


def _load_local_provider(provider_id: str) -> ModelProviderRecord:
    session = create_session()
    try:
        provider = get_record(session, ModelProviderRecord, provider_id)
        if provider is None:
            raise ValueError(f"Model provider not found: {provider_id}")
        if provider.provider_type not in {"local", "local_ollama"}:
            raise ValueError("Only local_ollama providers can use this operation")
        _assert_allowed_local_endpoint(provider.endpoint)
        return provider
    finally:
        session.close()


def _get_provider_for_preview(session, provider_id: str | None) -> ModelProviderRecord | None:
    if provider_id:
        provider = get_record(session, ModelProviderRecord, provider_id)
        if provider is None:
            raise ValueError(f"Model provider not found: {provider_id}")
        return provider
    return get_record(session, ModelProviderRecord, DEFAULT_PROVIDER_ID)


def _get_prompt_template_for_preview(session, prompt_id: str | None) -> PromptTemplateRecord:
    record = get_record(session, PromptTemplateRecord, prompt_id or DEFAULT_PROMPT_ID)
    if record is None:
        raise ValueError(f"Prompt template not found: {prompt_id or DEFAULT_PROMPT_ID}")
    return record


def _validate_and_consume_approval(approval_id: str, context: dict[str, object]) -> None:
    session = create_session()
    try:
        record = get_record(session, ModelInvocationApprovalRecord, approval_id)
        if record is None:
            raise ValueError("Approval id was not found.")
        if record.status != "pending":
            raise ValueError("Approval id is not pending.")
        now = datetime.now(UTC)
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < now:
            update_record(session, record, {"status": "expired"})
            raise ValueError("Approval id has expired.")
        if record.prompt_hash != context["prompt_hash"]:
            raise ValueError("Approval id does not match current prompt hash.")
        if (record.provider_id or "") != str(context["provider_id"] or ""):
            raise ValueError("Approval id does not match current provider.")
        if (record.prompt_template_id or "") != str(context["prompt_template_id"] or ""):
            raise ValueError("Approval id does not match current prompt template.")
        update_record(session, record, {"status": "used", "used_at": now})
    finally:
        session.close()


def _task_contract_payload(
    session,
    task_contract_id: str | None,
    mock_task_contract: dict[str, object] | None,
) -> dict[str, object]:
    if task_contract_id:
        record = get_record(session, TaskContractRecord, task_contract_id)
        if record is None:
            raise ValueError(f"Task contract not found: {task_contract_id}")
        return {
            "title": record.title,
            "objective": record.objective,
            "inputs": from_json_list(record.inputs_json),
            "outputs": from_json_list(record.outputs_json),
            "constraints": from_json_list(record.constraints_json),
            "acceptance_criteria": from_json_list(record.acceptance_criteria_json),
        }
    if mock_task_contract:
        return dict(mock_task_contract)
    return {
        "title": "Mock task contract",
        "objective": "Generate a local-only response.",
        "inputs": ["user message metadata only"],
        "outputs": ["local model response"],
        "constraints": ["no external API", "no web search", "no uploaded file content"],
        "acceptance_criteria": ["prompt is scanned and audit log stores hash only"],
    }


def _render_prompt(template_text: str, task_contract: dict[str, object]) -> str:
    try:
        values: dict[str, str] = {}
        for _, field_name, _, _ in Formatter().parse(template_text):
            if not field_name:
                continue
            if (
                "." in field_name
                or "[" in field_name
                or "]" in field_name
                or "__" in field_name
                or field_name not in ALLOWED_TEMPLATE_FIELDS
            ):
                raise ValueError(f"Invalid prompt template field: {field_name}")
            values[field_name] = _format_prompt_value(task_contract.get(field_name, ""))
        return template_text.format(**values)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Prompt template rendering failed: {exc}") from exc


def _format_prompt_value(value: object) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _local_json_request(
    endpoint: str,
    path: str,
    *,
    method: str,
    payload: dict[str, object] | None = None,
) -> tuple[bool, dict[str, object], str]:
    try:
        _assert_allowed_local_endpoint(endpoint)
        url = f"{endpoint.rstrip('/')}{path}"
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            url,
            data=body,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        opener = build_opener(ProxyHandler({}))
        with opener.open(request, timeout=LOCAL_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_LOCAL_RESPONSE_BYTES + 1)
        if len(raw) > MAX_LOCAL_RESPONSE_BYTES:
            return False, {}, "Local model response exceeded safety limit."
        parsed = json.loads(raw.decode("utf-8") or "{}")
        if not isinstance(parsed, dict):
            return False, {}, "Local model response was not a JSON object."
        return True, parsed, "ok"
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return False, {}, f"Local provider request failed safely: {exc.__class__.__name__}"


def _invoke_provider(
    endpoint: str,
    provider_kind: str,
    model_name: str,
    prompt: str,
    *,
    options: dict[str, object] | None = None,
) -> tuple[bool, dict[str, object], str]:
    if provider_kind == "ollama":
        payload: dict[str, object] = {"model": model_name, "prompt": prompt, "stream": False}
        if options:
            payload["options"] = options
        return _local_json_request(
            endpoint,
            "/api/generate",
            method="POST",
            payload=payload,
        )
    return False, {}, "Only local Ollama provider kind is enabled."


def _ollama_options_from_request(request: LocalModelInvokeRequest) -> dict[str, object]:
    options = _default_ollama_options(request.context_preset)
    if request.num_ctx is not None:
        options["num_ctx"] = request.num_ctx
    if request.num_predict is not None:
        options["num_predict"] = request.num_predict
    if request.temperature is not None:
        options["temperature"] = request.temperature
    if request.top_p is not None:
        options["top_p"] = request.top_p
    return options


def _default_ollama_options(context_preset: str | None = "default_8192") -> dict[str, object]:
    preset = context_preset or "default_8192"
    if preset not in OLLAMA_CONTEXT_PRESETS:
        raise ValueError("Unsupported Ollama context preset.")
    return {"num_ctx": OLLAMA_CONTEXT_PRESETS[preset]}


def _extract_models(provider_kind: str, data: dict[str, object]) -> list[LocalModelInfo]:
    if provider_kind == "ollama":
        raw_models = data.get("models", [])
        if not isinstance(raw_models, list):
            return []
        names = [item.get("name") for item in raw_models if isinstance(item, dict)]
        return [LocalModelInfo(name=str(name), provider_kind=provider_kind) for name in names if name]

    raw_models = data.get("data", [])
    if not isinstance(raw_models, list):
        return []
    names = [item.get("id") for item in raw_models if isinstance(item, dict)]
    return [LocalModelInfo(name=str(name), provider_kind=provider_kind) for name in names if name]


def _extract_response_text(provider_kind: str, data: dict[str, object]) -> str:
    if provider_kind == "ollama":
        value = data.get("response", "")
        return str(value)
    choices = data.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message", {})
    if not isinstance(message, dict):
        return ""
    return str(message.get("content", ""))


def _blocked_local_response(
    request: LocalModelInvokeRequest,
    context: dict[str, object],
    review: ModelInvocationApprovalReview,
    message: str,
    *,
    requires_user_approval: bool | None = None,
    approval_id: str | None = None,
) -> LocalModelInvokeResponse:
    return LocalModelInvokeResponse(
        blocked=True,
        risk_level=str(context["risk_level"]),
        requires_user_approval=review.requires_user_approval if requires_user_approval is None else requires_user_approval,
        provider_id=request.provider_id or "",
        model_name=request.model_name,
        response_text="",
        redacted_prompt_preview=review.redacted_preview,
        findings=review.findings,
        message=message,
        approval_id=approval_id,
        prompt_hash=str(context["prompt_hash"]),
    )


def _detection_path(provider_kind: str) -> str:
    return "/api/tags"


def _provider_kind(endpoint: str) -> str:
    return "ollama"


def _assert_allowed_local_endpoint(endpoint: str | None) -> None:
    normalized = (endpoint or "").rstrip("/")
    if normalized not in ALLOWED_LOCAL_ENDPOINTS:
        raise ValueError("Endpoint is not in the local model whitelist")
    parsed = urlparse(normalized)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.port != 11434:
        raise ValueError("Endpoint is not an allowed local Ollama endpoint")


def _finding_summary_json(findings: list[PayloadFinding]) -> str:
    return json.dumps(
        [{"type": item.type, "severity": item.severity, "start": item.start, "end": item.end} for item in findings],
        ensure_ascii=False,
    )


def _finding_label(finding: PayloadFinding) -> str:
    return f"{finding.type}:{finding.severity}"


def _merge_findings(primary: list[PayloadFinding], secondary: list[PayloadFinding]) -> list[PayloadFinding]:
    merged: dict[tuple[str, int, int], PayloadFinding] = {}
    for finding in [*primary, *secondary]:
        merged[(finding.type, finding.start, finding.end)] = finding
    return sorted(merged.values(), key=lambda item: (item.start, item.end, item.type))


def _truncate_preview(prompt: str, limit: int = 2400) -> str:
    if len(prompt) <= limit:
        return prompt
    return f"{prompt[:limit]}\n...[truncated; length={len(prompt)}]"


def _estimate_tokens(text: str) -> int:
    return _estimate_tokens_by_length(len(text))


def _estimate_tokens_by_length(length: int) -> int:
    if length <= 0:
        return 0
    return max(1, length // 4)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _model_provider_view(record: ModelProviderRecord) -> ModelProviderView:
    return ModelProviderView(
        id=record.id,
        name=record.name,
        provider_type=record.provider_type,
        endpoint=record.endpoint,
        enabled=record.enabled,
        privacy_mode=record.privacy_mode,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _model_invocation_log_view(record: ModelInvocationLogRecord) -> ModelInvocationLogView:
    return ModelInvocationLogView(
        id=record.id,
        provider_id=record.provider_id,
        prompt_template_id=record.prompt_template_id,
        task_contract_id=record.task_contract_id,
        model_id=record.model_id,
        skill_id=record.skill_id,
        step_id=record.step_id,
        pipeline_step_id=record.pipeline_step_id,
        provider_type=record.provider_type,
        mode=record.mode,
        prompt_hash=record.prompt_hash,
        prompt_length=record.prompt_length,
        input_tokens=record.input_tokens,
        output_tokens=record.output_tokens,
        estimated_cost=record.estimated_cost,
        latency_ms=record.latency_ms,
        success=record.success,
        error_code=record.error_code,
        retry_count=record.retry_count,
        schema_valid=record.schema_valid,
        sanitized_input_hash=record.sanitized_input_hash,
        output_hash=record.output_hash,
        blocked_reason=record.blocked_reason,
        risk_level=record.risk_level,
        blocked=record.blocked,
        findings=from_json_list(record.findings_json),
        created_at=record.created_at,
    )


def _prompt_template_view(record: PromptTemplateRecord) -> PromptTemplateView:
    return PromptTemplateView(
        id=record.id,
        name=record.name,
        task_type=record.task_type,
        template_text=record.template_text,
        safety_notes=record.safety_notes,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _normalize_provider_type(provider_type: str) -> str:
    if provider_type == "local":
        return "local_ollama"
    if provider_type not in ALLOWED_PROVIDER_TYPES:
        raise ValueError("Unsupported provider type. Allowed values: local_ollama, remote_api, desktop_tool, mock")
    return provider_type


def _normalize_provider_status(status: str, provider_type: str) -> str:
    if provider_type == "external_disabled":
        return "disabled"
    return status if status in ALLOWED_PROVIDER_STATUS else "draft"


def _normalize_prompt_status(status: str) -> str:
    return status if status in ALLOWED_PROMPT_STATUS else "draft"


def _provider_enabled(provider_type: str, requested: bool) -> bool:
    if provider_type == "external_disabled":
        return False
    return bool(requested)


def _clean_endpoint(endpoint: str | None, provider_type: str) -> str | None:
    if provider_type in {"mock", "remote_api", "desktop_tool", "external_disabled"}:
        return None
    if provider_type not in {"local", "local_ollama"}:
        raise ValueError(f"Unsupported provider type: {provider_type}")
    normalized_endpoint = (endpoint or "").rstrip("/")
    _assert_allowed_local_endpoint(normalized_endpoint)
    if any(finding.type in {"api_key", "token"} for finding in scan_payload(normalized_endpoint)):
        return None
    return normalized_endpoint
