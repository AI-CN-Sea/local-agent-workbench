import type {
  ChatResponse,
  AgentRunView,
  AgentStepView,
  AgentDeliverableView,
  ConversationView,
  LocalModelInvokeResponse,
  LocalModelListResponse,
  MessageView,
  ModelInvocationApprovalIntent,
  ModelInvocationApprovalReview,
  ModelInvocationLogView,
  ModelInvocationReview,
  ModelProviderCheckResult,
  ModelProviderView,
  NetworkAuditLogView,
  ProjectView,
  PromptTemplateView,
  ReviewResultView,
  SecurityRequestView,
  SkillConflictResponse,
  SkillDbView,
  TaskContractView,
  FileInspectResponse,
  FileParsePreviewResponse,
  UploadedFileResponse,
  UploadedFileView,
  MemoryItemDbView,
  HybridArchitectureState,
  WorkbenchState
} from "./types";

const fallbackState: WorkbenchState = {
  conversation: {
    title: "本地多 Agent 工作台 Demo",
    messages: [
      {
        id: "local-msg-001",
        role: "assistant",
        content: "前端已加载本地 mock 数据。启动后端后会自动使用 /api/workbench/state。",
        timestamp: "2026-06-01T00:00:00Z"
      }
    ],
    requirement_card: {
      title: "需求确认",
      status: "waiting_requirement_confirmation",
      items: ["确认目标", "确认输入输出", "确认工具和安全边界"]
    },
    outline_card: {
      title: "大纲确认",
      status: "waiting_outline_confirmation",
      sections: ["任务拆解", "Agent 分工", "执行步骤", "审核交付"]
    }
  },
  models: [
    {
      id: "mock-local-planner",
      name: "Mock Local Planner",
      provider: "mock",
      enabled: true,
      description: "本地 mock 模型"
    }
  ],
  agent_status: {
    controller: "主控 Agent",
    phase: "需求澄清",
    sub_agents: [
      { name: "Planner", role: "任务规划", status: "standby" },
      { name: "Coder", role: "代码生成", status: "standby" }
    ],
    review_result: "等待用户确认需求和大纲"
  },
  current_skill: {
    id: "skill-requirement-analysis",
    name: "需求分析",
    enabled: true,
    description: "整理用户需求"
  },
  security_notice: {
    level: "info",
    message: "默认不调用模型；仅允许经审查后的本机模型调用。",
    checks: ["外部 API：关闭", "网页搜索：关闭", "MCP：关闭"]
  },
  memory_suggestions: [
    {
      id: "mem-local-001",
      title: "项目偏好",
      detail: "建议记录：默认优先使用本地 mock 数据。"
    }
  ],
  tools: [],
  skills: [],
  database: {
    engine: "SQLite",
    path: "sqlite:///./local_agent_workbench.db",
    status: "configured_mock"
  }
};

export async function fetchWorkbenchState(): Promise<WorkbenchState> {
  try {
    const response = await fetch("/api/workbench/state");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return (await response.json()) as WorkbenchState;
  } catch {
    return fallbackState;
  }
}

export async function fetchHybridArchitecture(): Promise<HybridArchitectureState> {
  const response = await fetch("/api/hybrid/architecture");
  if (!response.ok) {
    throw new Error(`Hybrid architecture request failed: ${response.status}`);
  }
  return (await response.json()) as HybridArchitectureState;
}

export async function sendChatMessage(
  message: string,
  modelId: string,
  projectId?: string,
  localProviderId?: string,
  localModelName?: string,
  userApproved = false,
  conversationId?: string,
  approvalId?: string
): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      model_id: modelId,
      project_id: projectId,
      conversation_id: conversationId,
      local_provider_id: localProviderId,
      local_model_name: localModelName,
      user_approved: userApproved,
      approval_id: approvalId
    })
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`);
  }

  return (await response.json()) as ChatResponse;
}

export async function uploadWorkbenchFile(file: File, projectId?: string): Promise<UploadedFileResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (projectId) {
    formData.append("project_id", projectId);
  }

  const response = await fetch("/api/files/upload", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Upload failed: ${response.status}`);
  }

  return (await response.json()) as UploadedFileResponse;
}

export async function fetchProjects(): Promise<ProjectView[]> {
  const response = await fetch("/api/projects");
  if (!response.ok) {
    throw new Error(`Projects request failed: ${response.status}`);
  }
  return (await response.json()) as ProjectView[];
}

export async function createProject(name: string): Promise<ProjectView> {
  const response = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  if (!response.ok) {
    throw new Error(`Project creation failed: ${response.status}`);
  }
  return (await response.json()) as ProjectView;
}

export async function fetchConversations(projectId: string): Promise<ConversationView[]> {
  const response = await fetch(`/api/conversations?project_id=${encodeURIComponent(projectId)}`);
  if (!response.ok) {
    throw new Error(`Conversations request failed: ${response.status}`);
  }
  return (await response.json()) as ConversationView[];
}

export async function fetchConversationMessages(conversationId: string): Promise<MessageView[]> {
  const response = await fetch(`/api/conversations/${encodeURIComponent(conversationId)}/messages`);
  if (!response.ok) {
    throw new Error(`Messages request failed: ${response.status}`);
  }
  return (await response.json()) as MessageView[];
}

export async function fetchFiles(projectId: string): Promise<UploadedFileView[]> {
  const response = await fetch(`/api/files?project_id=${encodeURIComponent(projectId)}`);
  if (!response.ok) {
    throw new Error(`Files request failed: ${response.status}`);
  }
  return (await response.json()) as UploadedFileView[];
}

export async function inspectFile(fileId: string): Promise<FileInspectResponse> {
  const response = await fetch(`/api/files/${encodeURIComponent(fileId)}/inspect`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`File inspect failed: ${response.status}`);
  }
  return (await response.json()) as FileInspectResponse;
}

export async function parseFilePreview(fileId: string): Promise<FileParsePreviewResponse> {
  const response = await fetch(`/api/files/${encodeURIComponent(fileId)}/parse-preview`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`File parse preview failed: ${response.status}`);
  }
  return (await response.json()) as FileParsePreviewResponse;
}

export async function fetchSecurityRequests(projectId: string): Promise<SecurityRequestView[]> {
  const response = await fetch(`/api/security/requests?project_id=${encodeURIComponent(projectId)}`);
  if (!response.ok) {
    throw new Error(`Security requests failed: ${response.status}`);
  }
  return (await response.json()) as SecurityRequestView[];
}

export async function fetchAuditLogs(projectId: string): Promise<NetworkAuditLogView[]> {
  const response = await fetch(`/api/security/audit-logs?project_id=${encodeURIComponent(projectId)}`);
  if (!response.ok) {
    throw new Error(`Audit logs failed: ${response.status}`);
  }
  return (await response.json()) as NetworkAuditLogView[];
}

export async function fetchTaskContracts(conversationId: string): Promise<TaskContractView[]> {
  const response = await fetch(`/api/task-contracts?conversation_id=${encodeURIComponent(conversationId)}`);
  if (!response.ok) {
    throw new Error(`Task contracts failed: ${response.status}`);
  }
  return (await response.json()) as TaskContractView[];
}

export async function fetchAgentDeliverables(conversationId: string): Promise<AgentDeliverableView[]> {
  const response = await fetch(`/api/agent-deliverables?conversation_id=${encodeURIComponent(conversationId)}`);
  if (!response.ok) {
    throw new Error(`Agent deliverables failed: ${response.status}`);
  }
  return (await response.json()) as AgentDeliverableView[];
}

export async function fetchReviewResults(conversationId: string): Promise<ReviewResultView[]> {
  const response = await fetch(`/api/review-results?conversation_id=${encodeURIComponent(conversationId)}`);
  if (!response.ok) {
    throw new Error(`Review results failed: ${response.status}`);
  }
  return (await response.json()) as ReviewResultView[];
}

export async function startAgentRun(
  conversationId: string,
  projectId?: string,
  taskContractId?: string,
  modelProviderId?: string,
  modelName?: string
): Promise<AgentRunView> {
  const response = await fetch("/api/agent-runs/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: conversationId,
      project_id: projectId,
      task_contract_id: taskContractId,
      model_provider_id: modelProviderId,
      model_name: modelName
    })
  });
  if (!response.ok) {
    throw new Error(`Agent run start failed: ${response.status}`);
  }
  return (await response.json()) as AgentRunView;
}

export async function fetchAgentRuns(conversationId: string): Promise<AgentRunView[]> {
  const response = await fetch(`/api/agent-runs?conversation_id=${encodeURIComponent(conversationId)}`);
  if (!response.ok) {
    throw new Error(`Agent runs failed: ${response.status}`);
  }
  return (await response.json()) as AgentRunView[];
}

export async function fetchAgentSteps(runId: string): Promise<AgentStepView[]> {
  const response = await fetch(`/api/agent-runs/${encodeURIComponent(runId)}/steps`);
  if (!response.ok) {
    throw new Error(`Agent steps failed: ${response.status}`);
  }
  return (await response.json()) as AgentStepView[];
}

export async function advanceAgentRunStep(runId: string): Promise<AgentStepView> {
  const response = await fetch(`/api/agent-runs/${encodeURIComponent(runId)}/step`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Agent step failed: ${response.status}`);
  }
  return (await response.json()) as AgentStepView;
}

export async function pauseAgentRun(runId: string): Promise<AgentRunView> {
  const response = await fetch(`/api/agent-runs/${encodeURIComponent(runId)}/pause`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Agent run pause failed: ${response.status}`);
  }
  return (await response.json()) as AgentRunView;
}

export async function resumeAgentRun(runId: string): Promise<AgentRunView> {
  const response = await fetch(`/api/agent-runs/${encodeURIComponent(runId)}/resume`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Agent run resume failed: ${response.status}`);
  }
  return (await response.json()) as AgentRunView;
}

export async function cancelAgentRun(runId: string): Promise<AgentRunView> {
  const response = await fetch(`/api/agent-runs/${encodeURIComponent(runId)}/cancel`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Agent run cancel failed: ${response.status}`);
  }
  return (await response.json()) as AgentRunView;
}

export async function confirmRequirement(conversationId: string): Promise<ConversationView> {
  const response = await fetch(`/api/conversations/${encodeURIComponent(conversationId)}/confirm-requirement`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Requirement confirmation failed: ${response.status}`);
  }
  return (await response.json()) as ConversationView;
}

export async function confirmOutline(conversationId: string): Promise<ConversationView> {
  const response = await fetch(`/api/conversations/${encodeURIComponent(conversationId)}/confirm-outline`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Outline confirmation failed: ${response.status}`);
  }
  return (await response.json()) as ConversationView;
}

export async function createSecurityRequest(projectId: string): Promise<void> {
  const response = await fetch("/api/security/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      action: "external.network.request",
      reason: "UI mock security request; real network remains disabled.",
      resource: "mock://denied-network-request"
    })
  });
  if (!response.ok) {
    throw new Error(`Security request failed: ${response.status}`);
  }
}

export async function fetchDbSkills(): Promise<SkillDbView[]> {
  const response = await fetch("/api/skills/db");
  if (!response.ok) {
    throw new Error(`Skills request failed: ${response.status}`);
  }
  return (await response.json()) as SkillDbView[];
}

export async function createDbSkill(): Promise<SkillDbView> {
  const response = await fetch("/api/skills/db", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: `Mock Skill ${Date.now()}`,
      category: "others",
      description: "前端创建的本地 mock Skill。",
      rules: "不调用真实模型，不联网，不读取上传文件。",
      status: "draft"
    })
  });
  if (!response.ok) {
    throw new Error(`Skill creation failed: ${response.status}`);
  }
  return (await response.json()) as SkillDbView;
}

export async function updateDbSkillStatus(skillId: string, status: string): Promise<SkillDbView> {
  const response = await fetch(`/api/skills/db/${encodeURIComponent(skillId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });
  if (!response.ok) {
    throw new Error(`Skill update failed: ${response.status}`);
  }
  return (await response.json()) as SkillDbView;
}

export async function disableDbSkill(skillId: string): Promise<SkillDbView> {
  const response = await fetch(`/api/skills/db/${encodeURIComponent(skillId)}/disable`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Skill disable failed: ${response.status}`);
  }
  return (await response.json()) as SkillDbView;
}

export async function checkSkillConflict(skill: SkillDbView): Promise<SkillConflictResponse> {
  const response = await fetch("/api/skills/check-conflict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: skill.name, category: skill.category })
  });
  if (!response.ok) {
    throw new Error(`Skill conflict check failed: ${response.status}`);
  }
  return (await response.json()) as SkillConflictResponse;
}

export async function fetchMemoryItems(projectId: string): Promise<MemoryItemDbView[]> {
  const response = await fetch(`/api/memory/items?project_id=${encodeURIComponent(projectId)}`);
  if (!response.ok) {
    throw new Error(`Memory request failed: ${response.status}`);
  }
  return (await response.json()) as MemoryItemDbView[];
}

export async function searchMemoryItems(query: string, projectId?: string): Promise<MemoryItemDbView[]> {
  const params = new URLSearchParams();
  params.set("q", query);
  if (projectId) {
    params.set("project_id", projectId);
  }
  const response = await fetch(`/api/memory/search?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Memory search failed: ${response.status}`);
  }
  return (await response.json()) as MemoryItemDbView[];
}

export async function disableMemoryItem(memoryId: string): Promise<MemoryItemDbView> {
  const response = await fetch(`/api/memory/items/${encodeURIComponent(memoryId)}/disable`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Memory disable failed: ${response.status}`);
  }
  return (await response.json()) as MemoryItemDbView;
}

export async function saveMemorySuggestion(
  suggestionId: string,
  projectId: string,
  scope: "project" | "global"
): Promise<MemoryItemDbView> {
  const response = await fetch(`/api/memory/suggestions/${encodeURIComponent(suggestionId)}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, scope })
  });
  if (!response.ok) {
    throw new Error(`Memory suggestion save failed: ${response.status}`);
  }
  return (await response.json()) as MemoryItemDbView;
}

export async function fetchModelProviders(): Promise<ModelProviderView[]> {
  const response = await fetch("/api/model-gateway/providers");
  if (!response.ok) {
    throw new Error(`Model providers request failed: ${response.status}`);
  }
  return (await response.json()) as ModelProviderView[];
}

export async function fetchModelInvocationLogs(): Promise<ModelInvocationLogView[]> {
  const response = await fetch("/api/model-gateway/invocation-logs");
  if (!response.ok) {
    throw new Error(`Model invocation logs request failed: ${response.status}`);
  }
  return (await response.json()) as ModelInvocationLogView[];
}

export async function createMockModelProvider(): Promise<ModelProviderView> {
  const response = await fetch("/api/model-gateway/providers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: `Mock Provider ${Date.now()}`,
      provider_type: "mock",
      enabled: true,
      privacy_mode: "local_only",
      status: "active"
    })
  });
  if (!response.ok) {
    throw new Error(`Model provider creation failed: ${response.status}`);
  }
  return (await response.json()) as ModelProviderView;
}

export async function createLocalModelProvider(endpoint = "http://127.0.0.1:11434"): Promise<ModelProviderView> {
  const response = await fetch("/api/model-gateway/providers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: `Local Provider ${Date.now()}`,
      provider_type: "local_ollama",
      endpoint,
      enabled: false,
      privacy_mode: "local_only",
      status: "draft"
    })
  });
  if (!response.ok) {
    throw new Error(`Local model provider creation failed: ${response.status}`);
  }
  return (await response.json()) as ModelProviderView;
}

export async function disableModelProvider(providerId: string): Promise<ModelProviderView> {
  const response = await fetch(`/api/model-gateway/providers/${encodeURIComponent(providerId)}/disable`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Model provider disable failed: ${response.status}`);
  }
  return (await response.json()) as ModelProviderView;
}

export async function updateModelProvider(
  providerId: string,
  payload: Partial<Pick<ModelProviderView, "name" | "provider_type" | "endpoint" | "enabled" | "privacy_mode" | "status">>
): Promise<ModelProviderView> {
  const response = await fetch(`/api/model-gateway/providers/${encodeURIComponent(providerId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`Model provider update failed: ${response.status}`);
  }
  return (await response.json()) as ModelProviderView;
}

export async function checkModelProvider(providerId: string): Promise<ModelProviderCheckResult> {
  const response = await fetch(`/api/model-gateway/providers/${encodeURIComponent(providerId)}/check`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Model provider check failed: ${response.status}`);
  }
  return (await response.json()) as ModelProviderCheckResult;
}

export async function fetchLocalModels(providerId: string): Promise<LocalModelListResponse> {
  const response = await fetch(`/api/model-gateway/providers/${encodeURIComponent(providerId)}/models`);
  if (!response.ok) {
    throw new Error(`Local model list failed: ${response.status}`);
  }
  return (await response.json()) as LocalModelListResponse;
}

export async function testModelProvider(providerId: string, modelName: string): Promise<LocalModelInvokeResponse> {
  const response = await fetch(`/api/model-gateway/providers/${encodeURIComponent(providerId)}/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model_name: modelName })
  });
  if (!response.ok) {
    throw new Error(`Local model provider test failed: ${response.status}`);
  }
  return (await response.json()) as LocalModelInvokeResponse;
}

export async function fetchPromptTemplates(): Promise<PromptTemplateView[]> {
  const response = await fetch("/api/model-gateway/prompts");
  if (!response.ok) {
    throw new Error(`Prompt templates request failed: ${response.status}`);
  }
  return (await response.json()) as PromptTemplateView[];
}

export async function createPromptTemplate(): Promise<PromptTemplateView> {
  const response = await fetch("/api/model-gateway/prompts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: `Task Contract Prompt ${Date.now()}`,
      task_type: "task_contract",
      template_text:
        "Objective: {objective}\nInputs: {inputs}\nOutputs: {outputs}\nConstraints: {constraints}\nAcceptance: {acceptance_criteria}",
      safety_notes: "仅用于本地 prompt preview，不调用外部模型 API。",
      status: "draft"
    })
  });
  if (!response.ok) {
    throw new Error(`Prompt template creation failed: ${response.status}`);
  }
  return (await response.json()) as PromptTemplateView;
}

export async function previewPrompt(
  providerId?: string,
  promptTemplateId?: string,
  taskContractId?: string
): Promise<ModelInvocationReview> {
  const response = await fetch("/api/model-gateway/preview-prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider_id: providerId || undefined,
      prompt_template_id: promptTemplateId || undefined,
      task_contract_id: taskContractId || undefined,
      mock_task_contract: taskContractId
        ? undefined
        : {
            objective: "Generate a local-only mock plan.",
            inputs: ["current UI state only"],
            outputs: ["prompt preview"],
            constraints: ["no external API", "local model only through Model Gateway", "no uploaded file content"],
            acceptance_criteria: ["scanner called", "audit log stores hash only"]
          }
    })
  });
  if (!response.ok) {
    throw new Error(`Prompt preview failed: ${response.status}`);
  }
  return (await response.json()) as ModelInvocationReview;
}

export async function reviewModelInvocation(
  providerId?: string,
  promptTemplateId?: string,
  taskContractId?: string
): Promise<ModelInvocationApprovalReview> {
  const response = await fetch("/api/model-gateway/invocation-review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider_id: providerId || undefined,
      prompt_template_id: promptTemplateId || undefined,
      task_contract_id: taskContractId || undefined,
      mock_task_contract: taskContractId
        ? undefined
        : {
            objective: "Review a local-only mock invocation.",
            inputs: ["current UI state only"],
            outputs: ["approval card"],
            constraints: ["no external API", "local model only through Model Gateway", "no uploaded file content"],
            acceptance_criteria: ["redacted preview only", "no full prompt in logs"]
          }
    })
  });
  if (!response.ok) {
    throw new Error(`Invocation review failed: ${response.status}`);
  }
  return (await response.json()) as ModelInvocationApprovalReview;
}

export async function createModelInvocationApprovalIntent(
  providerId?: string,
  promptTemplateId?: string,
  taskContractId?: string
): Promise<ModelInvocationApprovalIntent> {
  const response = await fetch("/api/model-gateway/approval-intents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider_id: providerId || undefined,
      prompt_template_id: promptTemplateId || undefined,
      task_contract_id: taskContractId || undefined,
      mock_task_contract: taskContractId
        ? undefined
        : {
            objective: "Create a local-only invocation approval intent.",
            inputs: ["current UI state only"],
            outputs: ["approval id"],
            constraints: ["no external API", "local model only through Model Gateway", "no uploaded file content"],
            acceptance_criteria: ["approval id is bound to prompt hash", "no full prompt in logs"]
          }
    })
  });
  if (!response.ok) {
    throw new Error(`Approval intent creation failed: ${response.status}`);
  }
  return (await response.json()) as ModelInvocationApprovalIntent;
}

export async function invokeLocalModel(
  providerId: string,
  modelName: string,
  promptTemplateId?: string,
  taskContractId?: string,
  userApproved = false,
  approvalId?: string
): Promise<LocalModelInvokeResponse> {
  const response = await fetch("/api/model-gateway/local-invoke", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider_id: providerId,
      model_name: modelName,
      prompt_template_id: promptTemplateId || undefined,
      task_contract_id: taskContractId || undefined,
      user_approved: userApproved,
      approval_id: approvalId || undefined,
      mock_task_contract: taskContractId
        ? undefined
        : {
            objective: "Run a local-only model invocation smoke test.",
            inputs: ["current UI state only"],
            outputs: ["short local model response"],
            constraints: ["no external API", "no web search", "no uploaded file content"],
            acceptance_criteria: ["local provider only", "no full prompt or response in logs"]
          }
    })
  });
  if (!response.ok) {
    throw new Error(`Local invocation failed: ${response.status}`);
  }
  return (await response.json()) as LocalModelInvokeResponse;
}
