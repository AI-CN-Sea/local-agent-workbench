from datetime import datetime

from pydantic import BaseModel, Field


class ModelProfile(BaseModel):
    model_id: str
    provider_id: str
    provider_type: str
    model_name: str
    display_name: str
    supports_code: bool = False
    supports_reasoning: bool = False
    supports_writing: bool = False
    supports_vision: bool = False
    supports_diagram: bool = False
    supports_json: bool = False
    supports_tools: bool = False
    context_window: int = 4096
    cost_level: str = "low"
    latency_level: str = "medium"
    reliability_level: str = "medium"
    initial_rank: int = 100
    enabled: bool = True
    notes: str = ""


class ModelCapabilityScore(BaseModel):
    model_id: str
    skill_id: str
    step_type: str
    capability_score: float = 0.5
    quality_score: float = 0.5
    cost_efficiency_score: float = 0.5
    latency_score: float = 0.5
    reliability_score: float = 0.5
    privacy_score: float = 0.5
    schema_following_score: float = 0.5
    user_acceptance_score: float = 0.5
    sample_count: int = 0
    last_updated: str = "mock"


class ProviderDescriptor(BaseModel):
    provider_id: str
    provider_type: str
    display_name: str
    description: str
    base_url: str | None = None
    enabled: bool = False
    status: str = "disabled"
    privacy_mode: str = "local_only"
    auth_policy: str = "none"
    quota_policy: str = "mock"
    pricing_policy: str = "mock"
    health_policy: str = "mock"
    allowed_fetch_strategies: list[str] = Field(default_factory=list)
    supports_invoke: bool = False
    supports_usage_fetch: bool = False
    supports_cost_fetch: bool = False
    supports_quota_fetch: bool = False
    supports_status_fetch: bool = False
    supports_local_probe: bool = False
    supports_api_key: bool = False
    supports_oauth: bool = False
    supports_cli: bool = False
    supports_cookie: bool = False
    notes: str = ""


class ProviderFetchStrategy(BaseModel):
    strategy_id: str
    provider_id: str
    strategy_kind: str
    enabled: bool = False
    available: bool = False
    priority: int = 100
    safety_level: str = "reserved"
    requires_user_permission: bool = True
    last_error: str | None = None
    last_checked_at: datetime | None = None
    disabled_reason: str | None = None


class ProviderUsageSnapshot(BaseModel):
    provider_id: str
    model_id: str | None = None
    date: str
    request_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    success_count: int = 0
    failure_count: int = 0
    blocked_count: int = 0
    avg_latency_ms: int = 0
    created_at: datetime


class ProviderCostStats(BaseModel):
    provider_id: str
    model_id: str | None = None
    skill_id: str | None = None
    step_type: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    cost_level: str = "mock"
    currency: str = "USD"
    period: str = "mock"
    created_at: datetime


class ProviderQuotaWindow(BaseModel):
    provider_id: str
    window_type: str = "unknown"
    quota_limit: int = 0
    quota_used: int = 0
    quota_remaining: int = 0
    reset_at: datetime | None = None
    status: str = "mock"
    source: str = "mock"


class AdaptiveRoutingAlternative(BaseModel):
    model_id: str
    provider_id: str
    provider_type: str
    score: float
    reason: str


class AdaptiveRoutingResult(BaseModel):
    recommended_model_id: str
    recommended_provider_id: str
    final_score: float
    reason: str
    alternatives: list[AdaptiveRoutingAlternative] = Field(default_factory=list)


class SkillRegistryItem(BaseModel):
    skill_id: str
    skill_name: str
    task_type: str
    description: str
    input_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] = Field(default_factory=dict)
    allowed_provider_types: list[str] = Field(default_factory=list)
    allow_remote_api: bool = False
    allow_desktop_tool: bool = False
    requires_redaction: bool = True
    requires_user_confirmation: bool = False
    safety_rules: list[str] = Field(default_factory=list)


class SkillPipelineStep(BaseModel):
    step_id: str
    step_name: str
    step_type: str
    model_role: str
    depends_on: list[str] = Field(default_factory=list)
    allow_parallel: bool = False
    input_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] = Field(default_factory=dict)
    privacy_policy: str = "local_first"
    cost_limit: str = "low"
    requires_review: bool = False
    requires_user_confirmation: bool = False
    default_provider_type: str = "mock"
    candidate_model_roles: list[str] = Field(default_factory=list)


class SkillPipeline(BaseModel):
    skill_id: str
    skill_name: str
    steps: list[SkillPipelineStep]


class PrivacyGatewayResult(BaseModel):
    privacy_level: str
    external_allowed: bool
    requires_redaction: bool
    sanitized_prompt: str
    redaction_notes: list[str] = Field(default_factory=list)
    api_safe_context: str
    local_only_context: bool
    risk_level: str
    execution_allowed: bool
    blocked_reasons: list[str] = Field(default_factory=list)


class ModelRoutingRecommendation(BaseModel):
    selected_skill: str
    step_type: str
    model_role: str
    recommended_provider_type: str
    recommended_provider_id: str
    recommended_model: str
    recommended_model_id: str
    reason: str
    cost_level: str
    historical_quality_score: float
    latency_level: str
    final_score: float = 0.0
    alternatives: list[dict[str, object]] = Field(default_factory=list)


class DesktopToolProfile(BaseModel):
    tool_id: str
    name: str
    installed: bool = False
    executable_path: str | None = None
    enabled: bool = False
    allowed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    requires_user_confirmation: bool = True


class ModelEvaluationLogView(BaseModel):
    id: str
    invocation_id: str | None = None
    model_id: str
    skill_id: str | None = None
    step_type: str | None = None
    reviewer_model_id: str | None = None
    quality_score: float = 0.0
    schema_score: float = 0.0
    safety_score: float = 0.0
    cost_score: float = 0.0
    latency_score: float = 0.0
    user_accepted: bool = False
    final_used: bool = False
    reviewer_notes: str = ""
    created_at: datetime


class SkillPackageMetadata(BaseModel):
    package_id: str
    name: str
    path: str
    skill_md_found: bool = False
    manifest_found: bool = False
    static_found: bool = False
    references_found: bool = False
    shared_found: bool = False
    static_files: list[str] = Field(default_factory=list)
    reference_files: list[str] = Field(default_factory=list)
    manifest: dict[str, object] = Field(default_factory=dict)
    description: str = ""
    rules_preview: str = ""
    allowed_tools_effective: list[str] = Field(default_factory=list)
    scripts_enabled: bool = False
    load_status: str = "mock"
    safety_notes: list[str] = Field(default_factory=list)


class ArtifactCenterItem(BaseModel):
    artifact_id: str
    project_id: str | None = None
    conversation_id: str | None = None
    agent_run_id: str | None = None
    step_id: str | None = None
    artifact_type: str
    title: str
    summary: str
    content_preview: str = ""
    file_path: str | None = None
    status: str = "mock"
    created_at: datetime


class HybridArchitectureState(BaseModel):
    provider_types: list[str]
    provider_descriptors: list[ProviderDescriptor] = Field(default_factory=list)
    provider_fetch_strategies: list[ProviderFetchStrategy] = Field(default_factory=list)
    provider_usage_snapshots: list[ProviderUsageSnapshot] = Field(default_factory=list)
    provider_cost_stats: list[ProviderCostStats] = Field(default_factory=list)
    provider_quota_windows: list[ProviderQuotaWindow] = Field(default_factory=list)
    model_profiles: list[ModelProfile]
    capability_scores: list[ModelCapabilityScore]
    model_evaluation_logs: list[ModelEvaluationLogView] = Field(default_factory=list)
    skill_registry: list[SkillRegistryItem]
    skill_pipelines: list[SkillPipeline]
    skill_packages: list[SkillPackageMetadata] = Field(default_factory=list)
    artifact_center: list[ArtifactCenterItem] = Field(default_factory=list)
    desktop_tools: list[DesktopToolProfile]
