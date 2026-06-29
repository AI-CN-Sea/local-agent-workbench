from datetime import datetime

from pydantic import BaseModel, Field


class ModelProvider(BaseModel):
    id: str
    name: str
    provider_type: str
    endpoint: str | None = None
    enabled: bool = False
    privacy_mode: str = "local_only"
    status: str = "disabled"
    created_at: datetime
    updated_at: datetime


class ModelProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    provider_type: str = "mock"
    endpoint: str | None = None
    enabled: bool = False
    privacy_mode: str = "local_only"
    status: str = "draft"


class ModelProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    provider_type: str | None = None
    endpoint: str | None = None
    enabled: bool | None = None
    privacy_mode: str | None = None
    status: str | None = None


class ModelProviderView(ModelProvider):
    pass


class PromptTemplate(BaseModel):
    id: str
    name: str
    task_type: str
    template_text: str
    safety_notes: str
    status: str = "draft"
    created_at: datetime
    updated_at: datetime


class PromptTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    task_type: str = "task_contract"
    template_text: str = (
        "Task: {objective}\n"
        "Inputs: {inputs}\n"
        "Outputs: {outputs}\n"
        "Constraints: {constraints}\n"
        "Acceptance: {acceptance_criteria}"
    )
    safety_notes: str = "不调用外部模型，不联网搜索，不包含上传文件内容。"
    status: str = "draft"


class PromptTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    task_type: str | None = None
    template_text: str | None = None
    safety_notes: str | None = None
    status: str | None = None


class PromptTemplateView(PromptTemplate):
    pass


class ModelInvocationRequest(BaseModel):
    provider_id: str | None = None
    prompt_template_id: str | None = None
    task_contract_id: str | None = None
    mock_task_contract: dict[str, object] | None = None


class ModelInvocationReview(BaseModel):
    blocked: bool
    risk_level: str
    prompt_preview: str
    raw_preview_available: bool
    redacted_prompt_preview: str
    prompt_hash: str
    prompt_length: int
    findings: list[str]
    message: str


class ModelInvocationApprovalReview(BaseModel):
    risk_level: str
    blocked: bool
    requires_user_approval: bool
    redacted_preview: str
    findings: list[str]
    recommendation: str


class ModelInvocationApprovalIntent(BaseModel):
    approval_id: str | None = None
    provider_id: str | None = None
    prompt_template_id: str | None = None
    task_contract_id: str | None = None
    prompt_hash: str
    prompt_length: int
    risk_level: str
    blocked: bool
    requires_user_approval: bool
    redacted_preview: str
    findings: list[str]
    status: str
    expires_at: datetime | None = None
    message: str


class ModelInvocationLogView(BaseModel):
    id: str
    provider_id: str | None = None
    prompt_template_id: str | None = None
    task_contract_id: str | None = None
    model_id: str | None = None
    skill_id: str | None = None
    step_id: str | None = None
    pipeline_step_id: str | None = None
    provider_type: str | None = None
    mode: str
    prompt_hash: str
    prompt_length: int
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: int | None = None
    success: bool = False
    error_code: str | None = None
    retry_count: int = 0
    schema_valid: bool = False
    sanitized_input_hash: str | None = None
    output_hash: str | None = None
    blocked_reason: str | None = None
    risk_level: str
    blocked: bool
    findings: list[str] = Field(default_factory=list)
    created_at: datetime


class ModelProviderCheckResult(BaseModel):
    provider_id: str
    reachable: bool = False
    message: str
    provider_kind: str | None = None


class LocalModelInfo(BaseModel):
    name: str
    provider_kind: str


class LocalModelListResponse(BaseModel):
    provider_id: str
    reachable: bool
    models: list[LocalModelInfo] = Field(default_factory=list)
    message: str


class LocalModelInvokeRequest(ModelInvocationRequest):
    model_name: str = Field(min_length=1, max_length=200)
    user_approved: bool = False
    approval_id: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    num_ctx: int | None = Field(default=None, ge=512, le=32768)
    num_predict: int | None = Field(default=None, ge=1, le=8192)
    context_preset: str | None = "default_8192"


class LocalModelProviderTestRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=200)


class LocalModelInvokeResponse(BaseModel):
    blocked: bool
    risk_level: str
    requires_user_approval: bool
    provider_id: str
    model_name: str
    response_text: str = ""
    redacted_prompt_preview: str
    findings: list[str]
    message: str
    approval_id: str | None = None
    prompt_hash: str | None = None
