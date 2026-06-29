export type Message = {
  id: string;
  role: "user" | "assistant" | string;
  content: string;
  timestamp: string;
};

export type RequirementCard = {
  title: string;
  status: string;
  items: string[];
};

export type OutlineCard = {
  title: string;
  status: string;
  sections: string[];
};

export type ConversationSnapshot = {
  title: string;
  messages: Message[];
  requirement_card: RequirementCard;
  outline_card: OutlineCard;
};

export type ModelOption = {
  id: string;
  name: string;
  provider: string;
  enabled: boolean;
  description: string;
};

export type SubAgentAssignment = {
  name: string;
  role: string;
  status: string;
};

export type AgentStatus = {
  controller: string;
  phase: string;
  sub_agents: SubAgentAssignment[];
  review_result: string;
};

export type SkillInfo = {
  id: string;
  name: string;
  enabled: boolean;
  description: string;
};

export type SecurityNotice = {
  level: string;
  message: string;
  checks: string[];
};

export type MemorySuggestion = {
  id: string;
  title: string;
  detail: string;
};

export type ToolInfo = {
  id: string;
  name: string;
  enabled: boolean;
  description: string;
};

export type DatabaseStatus = {
  engine: string;
  path: string;
  status: string;
};

export type WorkbenchState = {
  conversation: ConversationSnapshot;
  models: ModelOption[];
  agent_status: AgentStatus;
  current_skill: SkillInfo;
  security_notice: SecurityNotice;
  memory_suggestions: MemorySuggestion[];
  tools: ToolInfo[];
  skills: SkillInfo[];
  database: DatabaseStatus;
};

export type ChatResponse = {
  project_id?: string | null;
  conversation_id?: string | null;
  agent_run_id?: string | null;
  reply: Message;
  requirement_card: RequirementCard;
  outline_card: OutlineCard;
  agent_status: AgentStatus;
  requires_user_approval?: boolean;
  blocked?: boolean;
  fallback_used?: boolean;
  safety_message?: string | null;
  approval_id?: string | null;
  prompt_hash?: string | null;
};

export type UploadedFileResponse = {
  file_id: string;
  original_filename: string;
  size_bytes: number;
  extension: string;
  relative_path: string;
  sha256: string;
  status: "quarantine" | string;
  security_message: string;
};

export type ProjectView = {
  id: string;
  name: string;
  description?: string | null;
  owner: string;
  status: string;
  created_at: string;
};

export type ConversationView = {
  id: string;
  project_id: string;
  title: string;
  status: string;
  current_state: string;
  created_at: string;
  updated_at: string;
};

export type MessageView = {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  created_at: string;
};

export type UploadedFileView = {
  id: string;
  project_id: string;
  original_filename: string;
  size_bytes: number;
  extension: string;
  relative_path: string;
  sha256: string;
  status: string;
  created_at: string;
};

export type FileInspectResponse = {
  file_id: string;
  original_filename: string;
  size_bytes: number;
  extension: string;
  sha256: string;
  status: string;
  can_parse_preview: boolean;
  parse_preview_enabled: boolean;
  message: string;
};

export type FileParsePreviewResponse = {
  file_id: string;
  blocked: boolean;
  summary: string;
  redacted_preview: string;
  message: string;
};

export type SecurityRequestView = {
  id: string;
  project_id?: string | null;
  action: string;
  reason: string;
  requested_by: string;
  resource?: string | null;
  status: string;
  created_at: string;
};

export type NetworkAuditLogView = {
  id: string;
  project_id?: string | null;
  action: string;
  destination: string;
  allowed: boolean;
  reason: string;
  mode: string;
  created_at: string;
};

export type TaskContractView = {
  id: string;
  project_id: string;
  conversation_id: string;
  title: string;
  objective: string;
  inputs: string[];
  outputs: string[];
  constraints: string[];
  acceptance_criteria: string[];
  steps: Array<Record<string, unknown>>;
  metadata: Record<string, unknown>;
  selected_skill?: string | null;
  recommended_executor?: string | null;
  pipeline_steps: Array<Record<string, unknown>>;
  model_roles: string[];
  recommended_models: Array<Record<string, unknown>>;
  privacy_level?: string | null;
  external_allowed: boolean;
  requires_redaction: boolean;
  sanitized_prompt: string;
  redaction_notes: string[];
  api_safe_context: string;
  local_only_context: boolean;
  estimated_cost_level?: string | null;
  requires_user_confirmation: boolean;
  risk_level: string;
  execution_allowed: boolean;
  blocked_reasons: string[];
  status: string;
  created_at: string;
  updated_at: string;
};

export type AgentRunView = {
  id: string;
  project_id: string;
  conversation_id: string;
  task_contract_id: string;
  model_provider_id?: string | null;
  model_name?: string | null;
  status: string;
  current_step_index: number;
  cancel_requested: boolean;
  created_at: string;
  updated_at: string;
};

export type AgentStepView = {
  id: string;
  run_id: string;
  step_index: number;
  pipeline_step_id?: string | null;
  step_name?: string | null;
  step_type?: string | null;
  model_role?: string | null;
  agent_name: string;
  skill_ids: string[];
  selected_provider_id?: string | null;
  selected_model_id?: string | null;
  status: string;
  requires_user_approval?: boolean;
  input_summary: string;
  output_summary: string;
  risk_level: string;
  cost_estimate?: string | null;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  latency_ms?: number | null;
  quality_score?: number | null;
  final_score: number;
  selected_reason?: string | null;
  alternatives: Array<Record<string, unknown>>;
  evaluation_status: string;
  error_message?: string | null;
  execution_metadata?: Record<string, unknown>;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type AgentDeliverableView = {
  id: string;
  project_id: string;
  conversation_id?: string | null;
  task_contract_id?: string | null;
  agent_name: string;
  summary: string;
  artifacts: unknown[];
  risks: string[];
  status: string;
  created_at: string;
};

export type ReviewResultView = {
  id: string;
  project_id: string;
  target_id: string;
  reviewer: string;
  approved: boolean;
  severity: string;
  findings: string[];
  recommendations: string[];
  created_at: string;
};

export type SkillDbView = {
  id: string;
  name: string;
  category: "code" | "writing" | "drawing" | "research" | "others" | string;
  description: string;
  rules: string;
  status: "active" | "disabled" | "draft" | string;
  enabled: boolean;
  safety_warnings: string[];
  created_at: string;
  updated_at: string;
};

export type SkillConflictResponse = {
  result: "possible_conflict" | "no_conflict" | string;
  matches: SkillDbView[];
  reason: string;
};

export type MemoryItemDbView = {
  id: string;
  project_id?: string | null;
  scope: "global" | "project" | "writing_style" | "output_format" | "skill" | string;
  title: string;
  content: string;
  sensitivity: string;
  status: "pending" | "active" | "disabled" | string;
  source: string;
  safety_warnings: string[];
  created_at: string;
  updated_at: string;
};

export type ModelProviderView = {
  id: string;
  name: string;
  provider_type: "mock" | "local" | "local_ollama" | "remote_api" | "desktop_tool" | "external_disabled" | string;
  endpoint?: string | null;
  enabled: boolean;
  privacy_mode: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type PromptTemplateView = {
  id: string;
  name: string;
  task_type: string;
  template_text: string;
  safety_notes: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ModelInvocationReview = {
  blocked: boolean;
  risk_level: string;
  prompt_preview: string;
  raw_preview_available: boolean;
  redacted_prompt_preview: string;
  prompt_hash: string;
  prompt_length: number;
  findings: string[];
  message: string;
};

export type ModelInvocationApprovalReview = {
  risk_level: string;
  blocked: boolean;
  requires_user_approval: boolean;
  redacted_preview: string;
  findings: string[];
  recommendation: string;
};

export type ModelInvocationApprovalIntent = {
  approval_id?: string | null;
  provider_id?: string | null;
  prompt_template_id?: string | null;
  task_contract_id?: string | null;
  prompt_hash: string;
  prompt_length: number;
  risk_level: string;
  blocked: boolean;
  requires_user_approval: boolean;
  redacted_preview: string;
  findings: string[];
  status: string;
  expires_at?: string | null;
  message: string;
};

export type ModelInvocationLogView = {
  id: string;
  provider_id?: string | null;
  prompt_template_id?: string | null;
  task_contract_id?: string | null;
  model_id?: string | null;
  skill_id?: string | null;
  step_id?: string | null;
  pipeline_step_id?: string | null;
  provider_type?: string | null;
  mode: string;
  prompt_hash: string;
  prompt_length: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  latency_ms?: number | null;
  success: boolean;
  error_code?: string | null;
  retry_count: number;
  schema_valid: boolean;
  sanitized_input_hash?: string | null;
  output_hash?: string | null;
  blocked_reason?: string | null;
  risk_level: string;
  blocked: boolean;
  findings: string[];
  created_at: string;
};

export type ModelProviderCheckResult = {
  provider_id: string;
  reachable: boolean;
  message: string;
  provider_kind?: string | null;
};

export type LocalModelInfo = {
  name: string;
  provider_kind: string;
};

export type LocalModelListResponse = {
  provider_id: string;
  reachable: boolean;
  models: LocalModelInfo[];
  message: string;
};

export type LocalModelInvokeResponse = {
  blocked: boolean;
  risk_level: string;
  requires_user_approval: boolean;
  provider_id: string;
  model_name: string;
  response_text: string;
  redacted_prompt_preview: string;
  findings: string[];
  message: string;
  approval_id?: string | null;
  prompt_hash?: string | null;
};

export type HybridArchitectureState = {
  provider_types: string[];
  provider_descriptors: Array<Record<string, unknown>>;
  provider_fetch_strategies: Array<Record<string, unknown>>;
  provider_usage_snapshots: Array<Record<string, unknown>>;
  provider_cost_stats: Array<Record<string, unknown>>;
  provider_quota_windows: Array<Record<string, unknown>>;
  model_profiles: Array<Record<string, unknown>>;
  capability_scores: Array<Record<string, unknown>>;
  model_evaluation_logs: Array<Record<string, unknown>>;
  skill_registry: Array<Record<string, unknown>>;
  skill_pipelines: Array<Record<string, unknown>>;
  skill_packages: Array<Record<string, unknown>>;
  artifact_center: Array<Record<string, unknown>>;
  desktop_tools: Array<Record<string, unknown>>;
};
