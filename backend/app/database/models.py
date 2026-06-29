from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("project"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(120), default="local-user")
    status: Mapped[str] = mapped_column(String(40), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ConversationRecord(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("conversation"))
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active")
    current_state: Mapped[str] = mapped_column(String(80), default="idle")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class MessageRecord(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("message"))
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TaskContractRecord(Base):
    __tablename__ = "task_contracts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("task"))
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("conversations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    inputs_json: Mapped[str] = mapped_column(Text, default="[]")
    outputs_json: Mapped[str] = mapped_column(Text, default="[]")
    constraints_json: Mapped[str] = mapped_column(Text, default="[]")
    acceptance_criteria_json: Mapped[str] = mapped_column(Text, default="[]")
    task_steps_json: Mapped[str] = mapped_column(Text, default="[]")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AgentDeliverableRecord(Base):
    __tablename__ = "agent_deliverables"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("deliverable"))
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("conversations.id"))
    task_contract_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("task_contracts.id"))
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    artifacts_json: Mapped[str] = mapped_column(Text, default="[]")
    risks_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(40), default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReviewResultRecord(Base):
    __tablename__ = "review_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("review"))
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(120), default="mock-reviewer")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    severity: Mapped[str] = mapped_column(String(40), default="info")
    findings_json: Mapped[str] = mapped_column(Text, default="[]")
    recommendations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AgentRunRecord(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("run"))
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("conversations.id"), nullable=False)
    task_contract_id: Mapped[str] = mapped_column(String(64), ForeignKey("task_contracts.id"), nullable=False)
    model_provider_id: Mapped[str | None] = mapped_column(String(80))
    model_name: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="running")
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AgentStepRecord(Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("step"))
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_runs.id"), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    pipeline_step_id: Mapped[str | None] = mapped_column(String(120))
    step_name: Mapped[str | None] = mapped_column(String(160))
    step_type: Mapped[str | None] = mapped_column(String(80))
    model_role: Mapped[str | None] = mapped_column(String(120))
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    skill_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    selected_provider_id: Mapped[str | None] = mapped_column(String(80))
    selected_model_id: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="pending")
    requires_user_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    risk_level: Mapped[str] = mapped_column(String(40), default="normal")
    cost_estimate: Mapped[str | None] = mapped_column(String(40))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    quality_score: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    execution_metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SkillRecord(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="others")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rules: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    permissions_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class MemoryItemRecord(Base):
    __tablename__ = "memory_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("memory"))
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("projects.id"))
    scope: Mapped[str] = mapped_column(String(40), default="project")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(40), default="normal")
    status: Mapped[str] = mapped_column(String(40), default="pending")
    source: Mapped[str] = mapped_column(String(80), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SecurityRequestRecord(Base):
    __tablename__ = "security_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("security-request"))
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("projects.id"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(120), default="local-user")
    resource: Mapped[str | None] = mapped_column(Text)
    payload_preview: Mapped[str | None] = mapped_column(Text)
    requires_user_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class NetworkAuditLogRecord(Base):
    __tablename__ = "network_audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("network-audit"))
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("projects.id"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    destination: Mapped[str] = mapped_column(Text, nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String(40), default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UploadedFileRecord(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("file"))
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(260), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(260), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    extension: Mapped[str] = mapped_column(String(24), nullable=False)
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="quarantine")
    scanner_findings_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ModelProviderRecord(Base):
    __tablename__ = "model_providers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("provider"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(40), default="mock")
    endpoint: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    privacy_mode: Mapped[str] = mapped_column(String(80), default="local_only")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ModelInvocationLogRecord(Base):
    __tablename__ = "model_invocation_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("model-log"))
    provider_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("model_providers.id"))
    prompt_template_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("prompt_templates.id"))
    task_contract_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("task_contracts.id"))
    model_id: Mapped[str | None] = mapped_column(String(120))
    skill_id: Mapped[str | None] = mapped_column(String(120))
    step_id: Mapped[str | None] = mapped_column(String(120))
    pipeline_step_id: Mapped[str | None] = mapped_column(String(120))
    provider_type: Mapped[str | None] = mapped_column(String(40))
    mode: Mapped[str] = mapped_column(String(40), default="mock_preview")
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_length: Mapped[int] = mapped_column(Integer, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_code: Mapped[str | None] = mapped_column(String(80))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    schema_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    sanitized_input_hash: Mapped[str | None] = mapped_column(String(64))
    output_hash: Mapped[str | None] = mapped_column(String(64))
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(40), default="normal")
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    findings_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ModelInvocationApprovalRecord(Base):
    __tablename__ = "model_invocation_approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("approval"))
    provider_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("model_providers.id"))
    prompt_template_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("prompt_templates.id"))
    task_contract_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("task_contracts.id"))
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_length: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(40), default="normal")
    findings_json: Mapped[str] = mapped_column(Text, default="[]")
    redacted_preview: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ModelEvaluationLogRecord(Base):
    __tablename__ = "model_evaluation_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("model-eval"))
    invocation_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("model_invocation_logs.id"))
    model_id: Mapped[str] = mapped_column(String(120), nullable=False)
    skill_id: Mapped[str | None] = mapped_column(String(120))
    step_type: Mapped[str | None] = mapped_column(String(80))
    reviewer_model_id: Mapped[str | None] = mapped_column(String(120))
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    schema_score: Mapped[float] = mapped_column(Float, default=0.0)
    safety_score: Mapped[float] = mapped_column(Float, default=0.0)
    cost_score: Mapped[float] = mapped_column(Float, default=0.0)
    latency_score: Mapped[float] = mapped_column(Float, default=0.0)
    user_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    final_used: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PromptTemplateRecord(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("prompt"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    task_type: Mapped[str] = mapped_column(String(80), default="task_contract")
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    safety_notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
