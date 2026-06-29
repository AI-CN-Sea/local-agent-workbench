from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str


class RequirementCard(BaseModel):
    title: str
    status: str
    items: list[str]


class OutlineCard(BaseModel):
    title: str
    status: str
    sections: list[str]


class ConversationSnapshot(BaseModel):
    title: str
    messages: list[Message]
    requirement_card: RequirementCard
    outline_card: OutlineCard


class ModelOption(BaseModel):
    id: str
    name: str
    provider: str
    enabled: bool = False
    description: str


class SubAgentAssignment(BaseModel):
    name: str
    role: str
    status: str


class AgentStatus(BaseModel):
    controller: str
    phase: str
    sub_agents: list[SubAgentAssignment]
    review_result: str


class SkillInfo(BaseModel):
    id: str
    name: str
    enabled: bool
    description: str


class SecurityNotice(BaseModel):
    level: str
    message: str
    checks: list[str]


class MemorySuggestion(BaseModel):
    id: str
    title: str
    detail: str


class ToolInfo(BaseModel):
    id: str
    name: str
    enabled: bool
    description: str


class DatabaseStatus(BaseModel):
    engine: str
    path: str
    status: str


class WorkbenchState(BaseModel):
    conversation: ConversationSnapshot
    models: list[ModelOption]
    agent_status: AgentStatus
    current_skill: SkillInfo
    security_notice: SecurityNotice
    memory_suggestions: list[MemorySuggestion]
    tools: list[ToolInfo]
    skills: list[SkillInfo]
    database: DatabaseStatus


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    model_id: str = "mock-local-planner"
    project_id: str | None = None
    conversation_id: str | None = None
    local_provider_id: str | None = None
    local_model_name: str | None = None
    user_approved: bool = False
    approval_id: str | None = None


class ChatResponse(BaseModel):
    project_id: str | None = None
    conversation_id: str | None = None
    agent_run_id: str | None = None
    reply: Message
    requirement_card: RequirementCard
    outline_card: OutlineCard
    agent_status: AgentStatus
    requires_user_approval: bool = False
    blocked: bool = False
    fallback_used: bool = False
    safety_message: str | None = None
    approval_id: str | None = None
    prompt_hash: str | None = None
