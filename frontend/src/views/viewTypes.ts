import type { ChangeEventHandler, FormEventHandler, RefObject } from "react";

import type {
  AgentDeliverableView,
  AgentRunView,
  FileInspectResponse,
  FileParsePreviewResponse,
  HybridArchitectureState,
  LocalModelInfo,
  LocalModelInvokeResponse,
  MemoryItemDbView,
  Message,
  ModelInvocationApprovalIntent,
  ModelInvocationApprovalReview,
  ModelInvocationReview,
  ModelProviderCheckResult,
  ModelProviderView,
  PromptTemplateView,
  ReviewResultView,
  SkillDbView,
  TaskContractView,
  UploadedFileView,
  WorkbenchState
} from "../types";
import type { PendingLocalChatRequestView, WorkbenchView } from "../components/componentTypes";

export type ModelOptionView = {
  id: string;
  name: string;
  enabled: boolean;
  description: string;
  provider?: string;
};

export type WorkspaceViewProps = {
  activeView: WorkbenchView;
  state: WorkbenchState;
  messages: Message[];
  files: UploadedFileView[];
  taskContracts: TaskContractView[];
  latestTaskContract?: TaskContractView;
  latestDeliverable?: AgentDeliverableView;
  latestReview?: ReviewResultView;
  agentRuns: AgentRunView[];
  skills: SkillDbView[];
  memoryItems: MemoryItemDbView[];
  memorySearchResults: MemoryItemDbView[];
  fileInspectResult: FileInspectResponse | null;
  filePreviewResult: FileParsePreviewResponse | null;
  modelProviders: ModelProviderView[];
  promptTemplates: PromptTemplateView[];
  promptPreview: ModelInvocationReview | null;
  invocationApprovalIntent: ModelInvocationApprovalIntent | null;
  invocationReview: ModelInvocationApprovalReview | null;
  localInvokeResult: LocalModelInvokeResponse | null;
  hybridArchitecture: HybridArchitectureState | null;
  providerCheck: ModelProviderCheckResult | null;
  localModels: LocalModelInfo[];
  selectedLocalModel: string;
  localProviderEndpoints: string[];
  selectedModel: string;
  selectedModelDescription?: string;
  modelOptions: ModelOptionView[];
  pendingLocalChatRequest: PendingLocalChatRequestView | null;
  input: string;
  isSending: boolean;
  isUploading: boolean;
  skillConflictNote: string;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onModelChange: (value: string) => void;
  onInputChange: (value: string) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
  onConfirmPendingLocalChat: () => void;
  onUpload: ChangeEventHandler<HTMLInputElement>;
  onOpenUploadPicker: () => void;
  onConfirmRequirement: () => void;
  onConfirmOutline: () => void;
  onStartAgentRun: () => void;
  onAdvanceAgentStep: (runId?: string) => void;
  onInspectFile: (fileId: string) => void;
  onParseFilePreview: (fileId: string) => void;
  onCreateSkill: () => void;
  onEnableSkill: (skillId: string) => void;
  onDisableSkill: (skillId: string) => void;
  onCheckSkill: (skill: SkillDbView) => void;
  onSaveSuggestion: (suggestionId: string, scope: "project" | "global") => void;
  onDisableMemory: (memoryId: string) => void;
  onSearchMemory: (query?: string) => void;
  onCreateMockProvider: () => void;
  onCreateLocalProvider: () => void;
  onEnableProvider: (providerId: string) => void;
  onSetProviderActive: (providerId: string) => void;
  onDisableProvider: (providerId: string) => void;
  onSetLocalEndpoint: (providerId: string, endpoint: string) => void;
  onCheckProvider: (providerId: string) => void;
  onFetchLocalModels: (providerId?: string) => void;
  onSelectLocalModel: (value: string) => void;
  onTestProvider: () => void;
  onCreatePromptTemplate: () => void;
  onPreviewPrompt: () => void;
  onReviewInvocation: () => void;
  onLocalInvoke: (userApproved?: boolean, approvalId?: string) => void;
};
