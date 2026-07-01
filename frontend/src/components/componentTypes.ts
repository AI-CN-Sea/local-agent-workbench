export type WorkbenchView = "workbench" | "skills" | "providers" | "artifacts" | "privacy" | "settings";

export type InspectorTab = "task" | "pipeline" | "models" | "safety" | "artifacts";

export type StatusBadgeKind =
  | "REAL_LOCAL"
  | "MOCK_ONLY"
  | "RESERVED_DISABLED"
  | "NO_EXTERNAL_CALL"
  | "NO_DESKTOP_EXECUTION"
  | "REQUIRES_APPROVAL"
  | "BLOCKED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "PAUSED"
  | "LOW_RISK"
  | "MEDIUM_RISK"
  | "HIGH_RISK"
  | "NORMAL";

export type PendingLocalChatRequestView = {
  message: string;
  selectedModel: string;
  providerId: string;
  modelName: string;
  projectId?: string;
  conversationId?: string;
  approvalId?: string;
};

export type UiPreferences = {
  simpleMode: boolean;
  showDebugInformation: boolean;
  showRawTaskContract: boolean;
  showPipelineSteps: boolean;
  showMockArtifacts: boolean;
  showProviderIds: boolean;
  autoRunLowRiskLocalTasks: boolean;
};