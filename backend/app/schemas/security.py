from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskContract(BaseModel):
    id: str = Field(default_factory=lambda: f"task-{uuid4().hex[:8]}")
    title: str
    objective: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    status: str = "draft"


class AgentDeliverable(BaseModel):
    id: str = Field(default_factory=lambda: f"deliverable-{uuid4().hex[:8]}")
    agent_name: str
    task_id: str | None = None
    summary: str
    artifacts: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReviewResult(BaseModel):
    id: str = Field(default_factory=lambda: f"review-{uuid4().hex[:8]}")
    target_id: str
    reviewer: str = "mock-reviewer"
    approved: bool
    severity: str = "info"
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SkillCard(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool = False
    permissions: list[str] = Field(default_factory=list)
    input_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] = Field(default_factory=dict)


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: f"memory-{uuid4().hex[:8]}")
    scope: str = "project"
    title: str
    content: str
    sensitivity: str = "normal"
    source: str = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SecurityRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"security-request-{uuid4().hex[:8]}")
    project_id: str | None = None
    action: str
    reason: str
    requested_by: str = "local-user"
    resource: str | None = None
    payload_preview: str | None = None
    requires_user_approval: bool = True
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NetworkAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: f"network-audit-{uuid4().hex[:8]}")
    project_id: str | None = None
    action: str
    destination: str
    allowed: bool = False
    reason: str
    mode: str = "mock"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Project(BaseModel):
    id: str = Field(default_factory=lambda: f"project-{uuid4().hex[:8]}")
    name: str
    description: str | None = None
    owner: str = "local-user"
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: f"conversation-{uuid4().hex[:8]}")
    project_id: str | None = None
    title: str
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Message(BaseModel):
    id: str = Field(default_factory=lambda: f"message-{uuid4().hex[:8]}")
    conversation_id: str | None = None
    role: str
    content: str
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PayloadFinding(BaseModel):
    type: str
    label: str
    value: str
    start: int
    end: int
    severity: str
    recommendation: str


class PayloadScanRequest(BaseModel):
    text: str = Field(min_length=1)
    context: str | None = None


class PayloadScanResponse(BaseModel):
    safe: bool
    sensitivity: str
    findings: list[PayloadFinding]
    recommendations: list[str]


class RedactRequest(BaseModel):
    text: str = Field(min_length=1)


class RedactResponse(BaseModel):
    redacted_text: str
    findings: list[PayloadFinding]


class SecurityPolicy(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool = True
    enforcement: str = "mock"


class SecurityRequestResponse(BaseModel):
    request: SecurityRequest
    decision: ReviewResult
    audit_log: NetworkAuditLog


class UploadedFile(BaseModel):
    id: str
    project_id: str
    original_filename: str
    size_bytes: int
    extension: str
    relative_path: str
    sha256: str
    status: str = "quarantine"
    created_at: datetime


class FileUploadResponse(BaseModel):
    file_id: str
    original_filename: str
    size_bytes: int
    extension: str
    relative_path: str
    sha256: str
    status: str = "quarantine"
    security_message: str = "文件已隔离，未解析，未发送给 Agent。"


class NetworkAuditLogCreate(BaseModel):
    project_id: str | None = None
    action: str
    destination: str
    reason: str = "mock audit entry"
