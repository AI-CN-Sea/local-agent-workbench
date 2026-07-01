from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.agents.service import get_agent_status
from app.database.service import (
    advance_agent_step,
    check_skill_conflict,
    create_memory_item_view,
    create_project_view,
    create_skill_db_view,
    confirm_outline,
    confirm_requirement,
    cancel_agent_run,
    disable_memory_item_view,
    disable_skill_db_view,
    inspect_uploaded_file,
    get_database_status,
    list_agent_run_views,
    list_agent_step_views,
    list_agent_deliverable_views,
    list_conversation_views,
    list_message_views,
    list_memory_item_views,
    list_network_audit_log_views,
    list_project_views,
    list_review_result_views,
    list_security_request_views,
    list_skill_db_views,
    list_task_contract_views,
    list_uploaded_file_views,
    parse_uploaded_file_preview,
    pause_agent_run,
    resume_agent_run,
    save_memory_suggestion_view,
    search_memory_item_views,
    start_agent_run,
    update_memory_item_view,
    update_skill_db_view,
)
from app.files.service import quarantine_upload
from app.hybrid.service import (
    architecture_state,
    list_artifact_center,
    list_capability_scores,
    list_desktop_tools,
    list_model_evaluation_logs,
    list_model_profiles,
    list_provider_cost_stats,
    list_provider_descriptors,
    list_provider_fetch_strategies,
    list_provider_quota_windows,
    list_provider_usage_snapshots,
    list_skill_packages,
    list_skill_pipelines,
    list_skill_registry,
)
from app.memory.service import get_memory_suggestions
from app.model_gateway.service import (
    check_model_provider,
    create_model_provider_view,
    create_model_invocation_approval_intent,
    create_prompt_template_view,
    disable_model_provider_view,
    get_available_models,
    invoke_local_model,
    list_model_invocation_log_views,
    list_local_model_views,
    list_model_provider_views,
    list_prompt_template_views,
    preview_prompt,
    review_model_invocation,
    test_model_provider,
    update_model_provider_view,
    update_prompt_template_view,
)
from app.orchestrator.service import get_conversation_snapshot, submit_user_message
from app.schemas.database import (
    AgentRunStartRequest,
    AgentRunView,
    AgentStepView,
    ConversationView,
    AgentDeliverableView,
    FileInspectResponse,
    FileParsePreviewResponse,
    MessageView,
    MemoryItemCreate,
    MemoryItemDbView,
    MemoryItemUpdate,
    MemorySuggestionSaveRequest,
    NetworkAuditLogView,
    ProjectCreate,
    ProjectView,
    ReviewResultView,
    SecurityRequestView,
    SkillConflictRequest,
    SkillConflictResponse,
    SkillDbCreate,
    SkillDbUpdate,
    SkillDbView,
    TaskContractView,
    UploadedFileView,
)
from app.schemas.hybrid import (
    ArtifactCenterItem,
    DesktopToolProfile,
    HybridArchitectureState,
    ModelCapabilityScore,
    ModelEvaluationLogView,
    ModelProfile,
    ProviderCostStats,
    ProviderDescriptor,
    ProviderFetchStrategy,
    ProviderQuotaWindow,
    ProviderUsageSnapshot,
    SkillPackageMetadata,
    SkillPipeline,
    SkillRegistryItem,
)
from app.schemas.security import (
    PayloadScanRequest,
    PayloadScanResponse,
    RedactRequest,
    RedactResponse,
    FileUploadResponse,
    NetworkAuditLog,
    NetworkAuditLogCreate,
    SecurityPolicy,
    SecurityRequest,
    SecurityRequestResponse,
)
from app.schemas.model_gateway import (
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
from app.schemas.workbench import ChatRequest, ChatResponse, WorkbenchState
from app.security.service import (
    create_security_request,
    get_policies,
    get_security_notice,
    redact_security_payload,
    scan_security_payload,
    write_network_audit,
)
from app.skills.service import get_current_skill, list_skills
from app.tools.service import list_mock_tools

router = APIRouter()

class DemoTaskRequest(BaseModel):
    message: str = Field(min_length=1)
    project_id: str | None = None
    conversation_id: str | None = None


class DemoPrivacyCheckRequest(BaseModel):
    text: str = Field(min_length=1)
    context: str | None = None


class DemoPrivacyCheckResponse(BaseModel):
    privacy_level: str
    risk_level: str
    findings: list[dict[str, object]]
    redacted_preview: str
    execution_allowed: bool


class DemoReviewRequest(BaseModel):
    task: str = Field(min_length=1)
    output: str = ""


class DemoReviewResponse(BaseModel):
    completion_score: int
    is_complete: bool
    missing_points: list[str]
    risk_notes: list[str]
    next_actions: list[str]


_PRIVACY_LEVEL_BY_RISK = {
    "normal": "P0",
    "low": "P1",
    "medium": "P3",
    "high": "P4",
    "critical": "P4",
}


@router.post("/tasks", response_model=TaskContractView)
def create_demo_task(request: DemoTaskRequest) -> TaskContractView:
    try:
        chat = submit_user_message(
            ChatRequest(
                message=request.message,
                model_id="mock-local-planner",
                project_id=request.project_id,
                conversation_id=request.conversation_id,
            )
        )
        contracts = list_task_contract_views(chat.conversation_id or "")
        if not contracts:
            raise ValueError("Task contract was not created.")
        return contracts[0]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/privacy/check", response_model=DemoPrivacyCheckResponse)
def create_demo_privacy_check(request: DemoPrivacyCheckRequest) -> DemoPrivacyCheckResponse:
    scan = scan_security_payload(PayloadScanRequest(text=request.text, context=request.context))
    redacted = redact_security_payload(RedactRequest(text=request.text))
    risk_level = scan.sensitivity
    return DemoPrivacyCheckResponse(
        privacy_level=_PRIVACY_LEVEL_BY_RISK.get(risk_level, "P3"),
        risk_level=risk_level,
        findings=[finding.model_dump() for finding in scan.findings],
        redacted_preview=redacted.redacted_text[:1200],
        execution_allowed=risk_level not in {"high", "critical"},
    )


@router.post("/review", response_model=DemoReviewResponse)
def create_demo_review(request: DemoReviewRequest) -> DemoReviewResponse:
    scan = scan_security_payload(PayloadScanRequest(text=request.output or request.task))
    missing_points: list[str] = []
    task_text = request.task.strip()
    output_text = request.output.strip()
    if not output_text:
        missing_points.append("No output was provided for review.")
    if len(output_text) < 80:
        missing_points.append("Output is too short for a complete task review.")
    if "test" in task_text.lower() and "test" not in output_text.lower():
        missing_points.append("Task mentions testing, but the output does not describe tests.")
    score = 45
    if output_text:
        score += 20
    if len(output_text) >= 80:
        score += 15
    if len(output_text) >= 240:
        score += 10
    if scan.sensitivity in {"high", "critical"}:
        score -= 30
    elif scan.sensitivity == "medium":
        score -= 10
    score = max(0, min(100, score - len(missing_points) * 8))
    risk_notes = [finding.label for finding in scan.findings] or ["No sensitive pattern detected by the local scanner."]
    next_actions = ["Address missing review points before marking complete."] if missing_points else ["Confirm acceptance criteria with the user."]
    return DemoReviewResponse(
        completion_score=score,
        is_complete=score >= 80 and not missing_points and scan.sensitivity not in {"high", "critical"},
        missing_points=missing_points,
        risk_notes=risk_notes,
        next_actions=next_actions,
    )


@router.get("/workbench/state", response_model=WorkbenchState)
def read_workbench_state() -> WorkbenchState:
    conversation = get_conversation_snapshot()
    return WorkbenchState(
        conversation=conversation,
        models=get_available_models(),
        agent_status=get_agent_status(),
        current_skill=get_current_skill(),
        security_notice=get_security_notice(),
        memory_suggestions=get_memory_suggestions(),
        tools=list_mock_tools(),
        skills=list_skills(),
        database=get_database_status(),
    )


@router.post("/chat", response_model=ChatResponse)
def create_chat(request: ChatRequest) -> ChatResponse:
    try:
        return submit_user_message(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects", response_model=list[ProjectView])
def read_projects() -> list[ProjectView]:
    return list_project_views()


@router.post("/projects", response_model=ProjectView)
def create_project(request: ProjectCreate) -> ProjectView:
    return create_project_view(name=request.name, description=request.description)


@router.get("/conversations", response_model=list[ConversationView])
def read_conversations(project_id: str) -> list[ConversationView]:
    return list_conversation_views(project_id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageView])
def read_conversation_messages(conversation_id: str) -> list[MessageView]:
    return list_message_views(conversation_id)


@router.get("/files", response_model=list[UploadedFileView])
def read_files(project_id: str) -> list[UploadedFileView]:
    return list_uploaded_file_views(project_id)


@router.get("/task-contracts", response_model=list[TaskContractView])
def read_task_contracts(conversation_id: str) -> list[TaskContractView]:
    return list_task_contract_views(conversation_id)


@router.get("/agent-deliverables", response_model=list[AgentDeliverableView])
def read_agent_deliverables(conversation_id: str) -> list[AgentDeliverableView]:
    return list_agent_deliverable_views(conversation_id)


@router.get("/review-results", response_model=list[ReviewResultView])
def read_review_results(conversation_id: str) -> list[ReviewResultView]:
    return list_review_result_views(conversation_id)


@router.post("/agent-runs/start", response_model=AgentRunView)
def start_agent_run_api(request: AgentRunStartRequest) -> AgentRunView:
    try:
        return start_agent_run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/agent-runs", response_model=list[AgentRunView])
def read_agent_runs(conversation_id: str) -> list[AgentRunView]:
    return list_agent_run_views(conversation_id)


@router.get("/agent-runs/{run_id}/steps", response_model=list[AgentStepView])
def read_agent_run_steps(run_id: str) -> list[AgentStepView]:
    return list_agent_step_views(run_id)


@router.post("/agent-runs/{run_id}/step", response_model=AgentStepView)
def advance_agent_run_step(run_id: str) -> AgentStepView:
    try:
        return advance_agent_step(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/agent-runs/{run_id}/pause", response_model=AgentRunView)
def pause_agent_run_api(run_id: str) -> AgentRunView:
    try:
        return pause_agent_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/agent-runs/{run_id}/resume", response_model=AgentRunView)
def resume_agent_run_api(run_id: str) -> AgentRunView:
    try:
        return resume_agent_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/agent-runs/{run_id}/cancel", response_model=AgentRunView)
def cancel_agent_run_api(run_id: str) -> AgentRunView:
    try:
        return cancel_agent_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/conversations/{conversation_id}/confirm-requirement", response_model=ConversationView)
def confirm_conversation_requirement(conversation_id: str) -> ConversationView:
    try:
        return confirm_requirement(conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/conversations/{conversation_id}/confirm-outline", response_model=ConversationView)
def confirm_conversation_outline(conversation_id: str) -> ConversationView:
    try:
        return confirm_outline(conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/models")
def read_models() -> dict[str, object]:
    return {"items": get_available_models()}


@router.get("/hybrid/architecture", response_model=HybridArchitectureState)
def read_hybrid_architecture() -> HybridArchitectureState:
    return architecture_state()


@router.get("/model-gateway/model-profiles", response_model=list[ModelProfile])
def read_model_profiles() -> list[ModelProfile]:
    return list_model_profiles()


@router.get("/model-gateway/capability-scores", response_model=list[ModelCapabilityScore])
def read_model_capability_scores() -> list[ModelCapabilityScore]:
    return list_capability_scores()


@router.get("/model-gateway/provider-descriptors", response_model=list[ProviderDescriptor])
def read_provider_descriptors() -> list[ProviderDescriptor]:
    return list_provider_descriptors()


@router.get("/model-gateway/provider-strategies", response_model=list[ProviderFetchStrategy])
def read_provider_fetch_strategies() -> list[ProviderFetchStrategy]:
    return list_provider_fetch_strategies()


@router.get("/model-gateway/provider-usage", response_model=list[ProviderUsageSnapshot])
def read_provider_usage_snapshots() -> list[ProviderUsageSnapshot]:
    return list_provider_usage_snapshots()


@router.get("/model-gateway/provider-costs", response_model=list[ProviderCostStats])
def read_provider_cost_stats() -> list[ProviderCostStats]:
    return list_provider_cost_stats()


@router.get("/model-gateway/provider-quotas", response_model=list[ProviderQuotaWindow])
def read_provider_quota_windows() -> list[ProviderQuotaWindow]:
    return list_provider_quota_windows()


@router.get("/model-gateway/evaluation-logs", response_model=list[ModelEvaluationLogView])
def read_model_gateway_evaluation_logs() -> list[ModelEvaluationLogView]:
    return list_model_evaluation_logs()


@router.get("/model-gateway/invocation-logs", response_model=list[ModelInvocationLogView])
def read_model_gateway_invocation_logs() -> list[ModelInvocationLogView]:
    return list_model_invocation_log_views()


@router.get("/skill-registry", response_model=list[SkillRegistryItem])
def read_skill_registry() -> list[SkillRegistryItem]:
    return list_skill_registry()


@router.get("/skill-pipelines", response_model=list[SkillPipeline])
def read_skill_pipelines() -> list[SkillPipeline]:
    return list_skill_pipelines()


@router.get("/skill-packages", response_model=list[SkillPackageMetadata])
def read_skill_packages() -> list[SkillPackageMetadata]:
    return list_skill_packages()


@router.get("/artifacts", response_model=list[ArtifactCenterItem])
def read_artifact_center(project_id: str | None = None, conversation_id: str | None = None) -> list[ArtifactCenterItem]:
    return list_artifact_center(project_id=project_id, conversation_id=conversation_id)


@router.get("/desktop-tools", response_model=list[DesktopToolProfile])
def read_desktop_tools() -> list[DesktopToolProfile]:
    return list_desktop_tools()


@router.get("/model-gateway/providers", response_model=list[ModelProviderView])
def read_model_gateway_providers() -> list[ModelProviderView]:
    return list_model_provider_views()


@router.post("/model-gateway/providers", response_model=ModelProviderView)
def create_model_gateway_provider(request: ModelProviderCreate) -> ModelProviderView:
    try:
        return create_model_provider_view(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/model-gateway/providers/{provider_id}", response_model=ModelProviderView)
def update_model_gateway_provider(provider_id: str, request: ModelProviderUpdate) -> ModelProviderView:
    try:
        return update_model_provider_view(provider_id, request)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/model-gateway/providers/{provider_id}/disable", response_model=ModelProviderView)
def disable_model_gateway_provider(provider_id: str) -> ModelProviderView:
    try:
        return disable_model_provider_view(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/model-gateway/providers/{provider_id}/check", response_model=ModelProviderCheckResult)
def check_model_gateway_provider(provider_id: str) -> ModelProviderCheckResult:
    try:
        return check_model_provider(provider_id)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/model-gateway/providers/{provider_id}/models", response_model=LocalModelListResponse)
def read_local_model_gateway_models(provider_id: str) -> LocalModelListResponse:
    try:
        return list_local_model_views(provider_id)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/model-gateway/providers/{provider_id}/test", response_model=LocalModelInvokeResponse)
def test_local_model_gateway_provider(provider_id: str, request: LocalModelProviderTestRequest) -> LocalModelInvokeResponse:
    try:
        return test_model_provider(provider_id, request)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/model-gateway/prompts", response_model=list[PromptTemplateView])
def read_model_gateway_prompts() -> list[PromptTemplateView]:
    return list_prompt_template_views()


@router.post("/model-gateway/prompts", response_model=PromptTemplateView)
def create_model_gateway_prompt(request: PromptTemplateCreate) -> PromptTemplateView:
    return create_prompt_template_view(request)


@router.patch("/model-gateway/prompts/{prompt_id}", response_model=PromptTemplateView)
def update_model_gateway_prompt(prompt_id: str, request: PromptTemplateUpdate) -> PromptTemplateView:
    try:
        return update_prompt_template_view(prompt_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/model-gateway/preview-prompt", response_model=ModelInvocationReview)
def preview_model_gateway_prompt(request: ModelInvocationRequest) -> ModelInvocationReview:
    try:
        return preview_prompt(request)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/model-gateway/invocation-review", response_model=ModelInvocationApprovalReview)
def review_model_gateway_invocation(request: ModelInvocationRequest) -> ModelInvocationApprovalReview:
    try:
        return review_model_invocation(request)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/model-gateway/approval-intents", response_model=ModelInvocationApprovalIntent)
def create_model_gateway_approval_intent(request: ModelInvocationRequest) -> ModelInvocationApprovalIntent:
    try:
        return create_model_invocation_approval_intent(request)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/model-gateway/local-invoke", response_model=LocalModelInvokeResponse)
def invoke_model_gateway_local_model(request: LocalModelInvokeRequest) -> LocalModelInvokeResponse:
    try:
        return invoke_local_model(request)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/skills")
def read_skills() -> dict[str, object]:
    return {"items": list_skills()}


@router.get("/skills/db", response_model=list[SkillDbView])
def read_db_skills() -> list[SkillDbView]:
    return list_skill_db_views()


@router.post("/skills/db", response_model=SkillDbView)
def create_db_skill(request: SkillDbCreate) -> SkillDbView:
    return create_skill_db_view(request)


@router.patch("/skills/db/{skill_id}", response_model=SkillDbView)
def update_db_skill(skill_id: str, request: SkillDbUpdate) -> SkillDbView:
    try:
        return update_skill_db_view(skill_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/skills/db/{skill_id}/disable", response_model=SkillDbView)
def disable_db_skill(skill_id: str) -> SkillDbView:
    try:
        return disable_skill_db_view(skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/skills/check-conflict", response_model=SkillConflictResponse)
def check_db_skill_conflict(request: SkillConflictRequest) -> SkillConflictResponse:
    return check_skill_conflict(request.name, request.category)


@router.get("/memory/suggestions")
def read_memory_suggestions() -> dict[str, object]:
    return {"items": get_memory_suggestions()}


@router.get("/memory/items", response_model=list[MemoryItemDbView])
def read_memory_items(project_id: str | None = None) -> list[MemoryItemDbView]:
    return list_memory_item_views(project_id)


@router.get("/memory/search", response_model=list[MemoryItemDbView])
def search_memory_items(q: str = "", project_id: str | None = None) -> list[MemoryItemDbView]:
    return search_memory_item_views(q, project_id)


@router.post("/memory/items", response_model=MemoryItemDbView)
def create_memory_item_api(request: MemoryItemCreate) -> MemoryItemDbView:
    return create_memory_item_view(request)


@router.patch("/memory/items/{memory_id}", response_model=MemoryItemDbView)
def update_memory_item_api(memory_id: str, request: MemoryItemUpdate) -> MemoryItemDbView:
    try:
        return update_memory_item_view(memory_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/memory/items/{memory_id}/disable", response_model=MemoryItemDbView)
def disable_memory_item_api(memory_id: str) -> MemoryItemDbView:
    try:
        return disable_memory_item_view(memory_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/memory/suggestions/{suggestion_id}/save", response_model=MemoryItemDbView)
def save_memory_suggestion_api(suggestion_id: str, request: MemorySuggestionSaveRequest) -> MemoryItemDbView:
    try:
        return save_memory_suggestion_view(suggestion_id, request.project_id, request.scope)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tools")
def read_tools() -> dict[str, object]:
    return {"items": list_mock_tools()}


@router.get("/security/policies", response_model=list[SecurityPolicy])
def read_security_policies() -> list[SecurityPolicy]:
    return get_policies()


@router.post("/security/scan", response_model=PayloadScanResponse)
def scan_payload_security(request: PayloadScanRequest) -> PayloadScanResponse:
    return scan_security_payload(request)


@router.post("/security/redact", response_model=RedactResponse)
def redact_payload_security(request: RedactRequest) -> RedactResponse:
    return redact_security_payload(request)


@router.post("/security/request", response_model=SecurityRequestResponse)
def request_security_review(request: SecurityRequest) -> SecurityRequestResponse:
    return create_security_request(request)


@router.post("/security/network-audit", response_model=NetworkAuditLog)
def create_network_audit(request: NetworkAuditLogCreate) -> NetworkAuditLog:
    return write_network_audit(request)


@router.get("/security/audit-logs", response_model=list[NetworkAuditLogView])
def read_network_audit_logs(project_id: str | None = None) -> list[NetworkAuditLogView]:
    return list_network_audit_log_views(project_id)


@router.get("/security/requests", response_model=list[SecurityRequestView])
def read_security_requests(project_id: str | None = None) -> list[SecurityRequestView]:
    return list_security_request_views(project_id)


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
) -> FileUploadResponse:
    return await quarantine_upload(file, project_id=project_id)


@router.post("/files/{file_id}/inspect", response_model=FileInspectResponse)
def inspect_file(file_id: str) -> FileInspectResponse:
    try:
        return inspect_uploaded_file(file_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/files/{file_id}/parse-preview", response_model=FileParsePreviewResponse)
def parse_file_preview(file_id: str) -> FileParsePreviewResponse:
    try:
        return parse_uploaded_file_preview(file_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
