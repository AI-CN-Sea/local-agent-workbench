from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectView(BaseModel):
    id: str
    name: str
    description: str | None = None
    owner: str
    status: str
    created_at: datetime


class ConversationView(BaseModel):
    id: str
    project_id: str
    title: str
    status: str
    current_state: str
    created_at: datetime
    updated_at: datetime


class MessageView(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime


class UploadedFileView(BaseModel):
    id: str
    project_id: str
    original_filename: str
    size_bytes: int
    extension: str
    relative_path: str
    sha256: str
    status: str
    created_at: datetime


class FileInspectResponse(BaseModel):
    file_id: str
    original_filename: str
    size_bytes: int
    extension: str
    sha256: str
    status: str
    can_parse_preview: bool
    parse_preview_enabled: bool
    message: str


class FileParsePreviewResponse(BaseModel):
    file_id: str
    blocked: bool = True
    summary: str
    redacted_preview: str = ""
    message: str


class SecurityRequestView(BaseModel):
    id: str
    project_id: str | None = None
    action: str
    reason: str
    requested_by: str
    resource: str | None = None
    status: str
    created_at: datetime


class NetworkAuditLogView(BaseModel):
    id: str
    project_id: str | None = None
    action: str
    destination: str
    allowed: bool
    reason: str
    mode: str
    created_at: datetime


class TaskContractView(BaseModel):
    id: str
    project_id: str
    conversation_id: str
    title: str
    objective: str
    inputs: list[str]
    outputs: list[str]
    constraints: list[str]
    acceptance_criteria: list[str]
    steps: list[dict[str, object]] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    selected_skill: str | None = None
    recommended_executor: str | None = None
    pipeline_steps: list[dict[str, object]] = Field(default_factory=list)
    model_roles: list[str] = Field(default_factory=list)
    recommended_models: list[dict[str, object]] = Field(default_factory=list)
    privacy_level: str | None = None
    external_allowed: bool = False
    requires_redaction: bool = False
    sanitized_prompt: str = ""
    redaction_notes: list[str] = Field(default_factory=list)
    api_safe_context: str = ""
    local_only_context: bool = True
    estimated_cost_level: str | None = None
    requires_user_confirmation: bool = False
    risk_level: str = "normal"
    execution_allowed: bool = True
    blocked_reasons: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime


class AgentDeliverableView(BaseModel):
    id: str
    project_id: str
    conversation_id: str | None = None
    task_contract_id: str | None = None
    agent_name: str
    summary: str
    artifacts: list[object]
    risks: list[str]
    status: str
    created_at: datetime


class ReviewResultView(BaseModel):
    id: str
    project_id: str
    target_id: str
    reviewer: str
    approved: bool
    severity: str
    findings: list[str]
    recommendations: list[str]
    created_at: datetime


class AgentRunStartRequest(BaseModel):
    project_id: str | None = None
    conversation_id: str
    task_contract_id: str | None = None
    model_provider_id: str | None = None
    model_name: str | None = None


class AgentRunView(BaseModel):
    id: str
    project_id: str
    conversation_id: str
    task_contract_id: str
    model_provider_id: str | None = None
    model_name: str | None = None
    status: str
    current_step_index: int
    cancel_requested: bool
    created_at: datetime
    updated_at: datetime


class AgentStepView(BaseModel):
    id: str
    run_id: str
    step_index: int
    pipeline_step_id: str | None = None
    step_name: str | None = None
    step_type: str | None = None
    model_role: str | None = None
    agent_name: str
    skill_ids: list[str]
    selected_provider_id: str | None = None
    selected_model_id: str | None = None
    status: str
    requires_user_approval: bool = False
    input_summary: str
    output_summary: str
    risk_level: str
    cost_estimate: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: int | None = None
    quality_score: int | None = None
    final_score: float = 0.0
    selected_reason: str | None = None
    alternatives: list[dict[str, object]] = Field(default_factory=list)
    evaluation_status: str = "pending"
    error_message: str | None = None
    execution_metadata: dict[str, object] = Field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SkillDbCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category: str = "others"
    description: str = ""
    rules: str = ""
    status: str = "draft"


class SkillDbUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = None
    description: str | None = None
    rules: str | None = None
    status: str | None = None


class SkillDbView(BaseModel):
    id: str
    name: str
    category: str
    description: str
    rules: str
    status: str
    enabled: bool = False
    safety_warnings: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SkillConflictRequest(BaseModel):
    name: str = Field(min_length=1)
    category: str = "others"


class SkillConflictResponse(BaseModel):
    result: str
    matches: list[SkillDbView]
    reason: str
    safety_warnings: list[str] = Field(default_factory=list)


class MemoryItemCreate(BaseModel):
    project_id: str | None = None
    scope: str = "project"
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    sensitivity: str = "normal"
    status: str = "pending"
    source: str = "user"


class MemoryItemUpdate(BaseModel):
    scope: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    sensitivity: str | None = None
    status: str | None = None


class MemoryItemDbView(BaseModel):
    id: str
    project_id: str | None = None
    scope: str
    title: str
    content: str
    sensitivity: str
    status: str
    source: str
    safety_warnings: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MemorySuggestionSaveRequest(BaseModel):
    project_id: str | None = None
    scope: str = "project"
