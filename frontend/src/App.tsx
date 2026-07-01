import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  advanceAgentRunStep,
  cancelAgentRun,
  checkModelProvider,
  checkSkillConflict,
  confirmOutline,
  confirmRequirement,
  createDbSkill,
  createLocalModelProvider,
  createMockModelProvider,
  createModelInvocationApprovalIntent,
  createProject,
  createPromptTemplate,
  createSecurityRequest,
  disableDbSkill,
  disableMemoryItem,
  disableModelProvider,
  fetchAgentDeliverables,
  fetchAgentRuns,
  fetchAgentSteps,
  fetchAuditLogs,
  fetchConversationMessages,
  fetchConversations,
  fetchDbSkills,
  fetchFiles,
  fetchHybridArchitecture,
  fetchLocalModels,
  fetchMemoryItems,
  fetchModelInvocationLogs,
  fetchModelProviders,
  fetchProjects,
  fetchPromptTemplates,
  fetchReviewResults,
  fetchSecurityRequests,
  fetchTaskContracts,
  fetchWorkbenchState,
  inspectFile,
  invokeLocalModel,
  parseFilePreview,
  pauseAgentRun,
  previewPrompt,
  resumeAgentRun,
  reviewModelInvocation,
  saveMemorySuggestion,
  searchMemoryItems,
  sendChatMessage,
  startAgentRun,
  testModelProvider,
  updateDbSkillStatus,
  updateModelProvider,
  uploadWorkbenchFile
} from "./api";
import { MainWorkspace } from "./components/MainWorkspace";
import { RightInspector } from "./components/RightInspector";
import { Sidebar } from "./components/Sidebar";
import { TopStatusBar } from "./components/TopStatusBar";
import { getPreferredLocalModelName, getPrimaryLocalProvider, sortLocalModels } from "./components/localProvider";
import type { PendingLocalChatRequestView, UiPreferences, WorkbenchView } from "./components/componentTypes";
import type {
  AgentDeliverableView,
  AgentRunView,
  AgentStepView,
  ChatResponse,
  ConversationView,
  FileInspectResponse,
  FileParsePreviewResponse,
  HybridArchitectureState,
  LocalModelInfo,
  LocalModelInvokeResponse,
  MemoryItemDbView,
  Message,
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
  SkillDbView,
  TaskContractView,
  UploadedFileView,
  WorkbenchState
} from "./types";

const LOCAL_PROVIDER_ENDPOINTS = ["http://127.0.0.1:11434", "http://localhost:11434"];

const DEFAULT_UI_PREFERENCES: UiPreferences = {
  simpleMode: true,
  showDebugInformation: false,
  showRawTaskContract: false,
  showPipelineSteps: false,
  showMockArtifacts: false,
  showProviderIds: false,
  autoRunLowRiskLocalTasks: true
};

function App() {
  const [state, setState] = useState<WorkbenchState | null>(null);
  const [projects, setProjects] = useState<ProjectView[]>([]);
  const [currentProjectId, setCurrentProjectId] = useState("");
  const [conversations, setConversations] = useState<ConversationView[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [files, setFiles] = useState<UploadedFileView[]>([]);
  const [taskContracts, setTaskContracts] = useState<TaskContractView[]>([]);
  const [agentDeliverables, setAgentDeliverables] = useState<AgentDeliverableView[]>([]);
  const [agentRuns, setAgentRuns] = useState<AgentRunView[]>([]);
  const [agentSteps, setAgentSteps] = useState<AgentStepView[]>([]);
  const [reviewResults, setReviewResults] = useState<ReviewResultView[]>([]);
  const [securityRequests, setSecurityRequests] = useState<SecurityRequestView[]>([]);
  const [auditLogs, setAuditLogs] = useState<NetworkAuditLogView[]>([]);
  const [skills, setSkills] = useState<SkillDbView[]>([]);
  const [memoryItems, setMemoryItems] = useState<MemoryItemDbView[]>([]);
  const [memorySearchResults, setMemorySearchResults] = useState<MemoryItemDbView[]>([]);
  const [fileInspectResult, setFileInspectResult] = useState<FileInspectResponse | null>(null);
  const [filePreviewResult, setFilePreviewResult] = useState<FileParsePreviewResponse | null>(null);
  const [modelProviders, setModelProviders] = useState<ModelProviderView[]>([]);
  const [modelInvocationLogs, setModelInvocationLogs] = useState<ModelInvocationLogView[]>([]);
  const [promptTemplates, setPromptTemplates] = useState<PromptTemplateView[]>([]);
  const [promptPreview, setPromptPreview] = useState<ModelInvocationReview | null>(null);
  const [invocationApprovalIntent, setInvocationApprovalIntent] = useState<ModelInvocationApprovalIntent | null>(null);
  const [invocationReview, setInvocationReview] = useState<ModelInvocationApprovalReview | null>(null);
  const [providerCheck, setProviderCheck] = useState<ModelProviderCheckResult | null>(null);
  const [localModels, setLocalModels] = useState<LocalModelInfo[]>([]);
  const [selectedLocalModel, setSelectedLocalModel] = useState("");
  const [localInvokeResult, setLocalInvokeResult] = useState<LocalModelInvokeResponse | null>(null);
  const [hybridArchitecture, setHybridArchitecture] = useState<HybridArchitectureState | null>(null);
  const [activeView, setActiveView] = useState<WorkbenchView>("workbench");
  const [uiPreferences, setUiPreferences] = useState<UiPreferences>(DEFAULT_UI_PREFERENCES);
  const [skillConflictNote, setSkillConflictNote] = useState("");
  const [selectedModel, setSelectedModel] = useState("mock-local-planner");
  const [pendingLocalChatRequest, setPendingLocalChatRequest] = useState<PendingLocalChatRequestView | null>(null);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    fetchWorkbenchState().then((data) => {
      setState(data);
      setMessages(data.conversation.messages);
      setSelectedModel(data.models.find((model) => model.enabled)?.id ?? data.models[0]?.id ?? "mock-local-planner");
    });
    refreshProjects();
    refreshSkills();
    refreshModelGateway();
    fetchHybridArchitecture().then(setHybridArchitecture).catch(() => setHybridArchitecture(null));
  }, []);

  useEffect(() => {
    if (currentProjectId) {
      refreshProjectData(currentProjectId);
      refreshMemoryItems(currentProjectId);
    }
  }, [currentProjectId]);

  useEffect(() => {
    if (currentConversationId) {
      refreshConversationData(currentConversationId);
    } else {
      setTaskContracts([]);
      setAgentDeliverables([]);
      setAgentRuns([]);
      setAgentSteps([]);
      setReviewResults([]);
    }
  }, [currentConversationId]);

  const modelOptions = useMemo(() => {
    const localProvider = getPrimaryLocalProvider(modelProviders);
    const sortedLocalModels = sortLocalModels(localModels);
    const localOptions = localProvider
      ? sortedLocalModels.map((model) => ({
          id: `local::${localProvider.id}::${model.name}`,
          name: `${model.name} / ollama`,
          enabled: localProvider.enabled && localProvider.status === "active",
          description: "Local Ollama model. Reviewed by Model Gateway before use.",
          provider: "local"
        }))
      : [];
    return [...localOptions, ...(state?.models ?? [])];
  }, [localModels, modelProviders, state?.models]);


  useEffect(() => {
    const preferQwen25Selection = modelOptions.find((model) => model.id.includes("qwen2.5:7b") && model.enabled);
    if (preferQwen25Selection && (!selectedModel || selectedModel.startsWith("mock-"))) {
      setSelectedModel(preferQwen25Selection.id);
    }
  }, [modelOptions, selectedModel]);
  const selectedModelDescription =
    modelOptions.find((model) => model.id === selectedModel)?.description || "Default model calls are off unless an active local provider passes review.";
  const currentProject = projects.find((project) => project.id === currentProjectId);
  const currentConversation = conversations.find((conversation) => conversation.id === currentConversationId);
  const latestTaskContract = taskContracts[0];
  const latestDeliverable = agentDeliverables[0];
  const latestReview = reviewResults[0];

  async function refreshProjects() {
    try {
      const items = await fetchProjects();
      setProjects(items);
      setCurrentProjectId((current) => current || items[0]?.id || "");
    } catch {
      setProjects([]);
    }
  }

  async function refreshProjectData(projectId: string, preferredConversationId?: string) {
    const [conversationItems, fileItems, requestItems, auditItems] = await Promise.all([
      fetchConversations(projectId),
      fetchFiles(projectId),
      fetchSecurityRequests(projectId),
      fetchAuditLogs(projectId)
    ]);
    setConversations(conversationItems);
    setFiles(fileItems);
    setSecurityRequests(requestItems);
    setAuditLogs(auditItems);
    setCurrentConversationId((current) => {
      if (preferredConversationId && conversationItems.some((conversation) => conversation.id === preferredConversationId)) {
        return preferredConversationId;
      }
      if (current && conversationItems.some((conversation) => conversation.id === current)) {
        return current;
      }
      return conversationItems[0]?.id || "";
    });
  }

  async function refreshSkills() {
    setSkills(await fetchDbSkills());
  }

  async function refreshMemoryItems(projectId: string) {
    setMemoryItems(await fetchMemoryItems(projectId));
  }

  async function refreshModelGateway() {
    const [providers, prompts, logs] = await Promise.all([
      fetchModelProviders(),
      fetchPromptTemplates(),
      fetchModelInvocationLogs()
    ]);
    setModelProviders(providers);
    setPromptTemplates(prompts);
    setModelInvocationLogs(logs);

    const primaryLocalProvider = getPrimaryLocalProvider(providers);
    if (primaryLocalProvider?.enabled && primaryLocalProvider.status === "active") {
      try {
        const result = await fetchLocalModels(primaryLocalProvider.id);
        const preferredModel = getPreferredLocalModelName(result.models);
        setLocalModels(result.models);
        setSelectedLocalModel((current) => result.models.some((model) => model.name === current) ? current : preferredModel);
        setProviderCheck({
          provider_id: primaryLocalProvider.id,
          reachable: result.reachable,
          message: result.message || (result.models.length > 0 ? "Local models loaded." : "Local models not loaded. Start Ollama and click Fetch Models."),
          provider_kind: result.models[0]?.provider_kind
        });
      } catch {
        setLocalModels([]);
        setProviderCheck({
          provider_id: primaryLocalProvider.id,
          reachable: false,
          message: "Local models not loaded. Start Ollama and click Fetch Models.",
          provider_kind: undefined
        });
      }
    }
  }

  async function refreshConversationData(conversationId: string) {
    const [messageItems, contractItems, deliverableItems, reviewItems, runItems] = await Promise.all([
      fetchConversationMessages(conversationId),
      fetchTaskContracts(conversationId),
      fetchAgentDeliverables(conversationId),
      fetchReviewResults(conversationId),
      fetchAgentRuns(conversationId)
    ]);
    setMessages(
      messageItems.map((message) => ({
        id: message.id,
        role: message.role,
        content: message.content,
        timestamp: message.created_at
      }))
    );
    setTaskContracts(contractItems);
    setAgentDeliverables(deliverableItems);
    setReviewResults(reviewItems);
    setAgentRuns(runItems);
    if (runItems[0]) {
      setAgentSteps(await fetchAgentSteps(runItems[0].id));
    } else {
      setAgentSteps([]);
    }
  }

  async function handleCreateProject() {
    const name = window.prompt("请输入项目名称");
    if (!name?.trim()) {
      return;
    }
    const project = await createProject(name.trim());
    await refreshProjects();
    setCurrentProjectId(project.id);
    setActiveView("workbench");
  }

  async function handleCreateSkill() {
    await createDbSkill();
    await refreshSkills();
    setActiveView("skills");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || !selectedModel) {
      return;
    }

    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: "user", content: trimmed, timestamp: new Date().toISOString() }
    ]);
    setInput("");
    setIsSending(true);

    try {
      const localSelection = parseLocalModelSelection(selectedModel);
      const response = await sendChatMessage(
        trimmed,
        selectedModel,
        currentProjectId || undefined,
        localSelection?.providerId,
        localSelection?.modelName,
        false,
        currentConversationId || undefined
      );
      if (response.requires_user_approval && localSelection) {
        setPendingLocalChatRequest({
          message: trimmed,
          selectedModel,
          providerId: localSelection.providerId,
          modelName: localSelection.modelName,
          projectId: response.project_id || currentProjectId || undefined,
          conversationId: response.conversation_id || currentConversationId || undefined,
          approvalId: response.approval_id || undefined
        });
      } else {
        setPendingLocalChatRequest(null);
      }
      await applyChatResponse(response);
    } catch {
      appendAssistantMessage("Backend is unavailable. Start FastAPI and retry.");
    } finally {
      setIsSending(false);
    }
  }

  async function handleConfirmPendingLocalChat() {
    if (!pendingLocalChatRequest) {
      return;
    }
    setIsSending(true);
    try {
      // MVP temporary approval gate. Next stage should bind approval_id to prompt_hash.
      const response = await sendChatMessage(
        pendingLocalChatRequest.message,
        pendingLocalChatRequest.selectedModel,
        pendingLocalChatRequest.projectId,
        pendingLocalChatRequest.providerId,
        pendingLocalChatRequest.modelName,
        true,
        pendingLocalChatRequest.conversationId,
        pendingLocalChatRequest.approvalId
      );
      setPendingLocalChatRequest(null);
      await applyChatResponse(response);
    } catch {
      appendAssistantMessage("File is quarantined, not parsed, and not sent to any Agent.");
    } finally {
      setIsSending(false);
    }
  }

  async function applyChatResponse(response: ChatResponse) {
    setMessages((current) => [...current, response.reply]);
    setState((current) =>
      current
        ? {
            ...current,
            conversation: {
              ...current.conversation,
              requirement_card: response.requirement_card,
              outline_card: response.outline_card
            },
            agent_status: response.agent_status
          }
        : current
    );
    if (response.conversation_id) {
      setCurrentConversationId(response.conversation_id);
      await refreshConversationData(response.conversation_id);
    }
    if (response.project_id) {
      setCurrentProjectId(response.project_id);
      await refreshProjectData(response.project_id, response.conversation_id || undefined);
    } else if (currentProjectId) {
      await refreshProjectData(currentProjectId, response.conversation_id || undefined);
    } else {
      await refreshProjects();
    }
    if (response.requires_user_approval || response.blocked) {
      appendAssistantMessage(response.safety_message || "This task needs safe confirmation before continuing.");
    }
    if (response.fallback_used && !response.requires_user_approval && !response.blocked) {
      appendAssistantMessage("Model output was not valid JSON, so the safe fallback was used.");
    }
    if (uiPreferences.autoRunLowRiskLocalTasks && response.agent_run_id && !response.requires_user_approval && !response.blocked) {
      await autoAdvanceSafeRun(response.agent_run_id, response.conversation_id || undefined);
    }
  }

  async function autoAdvanceSafeRun(runId: string, conversationId?: string) {
    const maxSteps = 5;
    for (let index = 0; index < maxSteps; index += 1) {
      const stepItems = await fetchAgentSteps(runId);
      const nextStep = stepItems.find((step) => ["draft", "pending", "ready"].includes(step.status));
      if (nextStep?.requires_user_approval) {
        appendAssistantMessage("This step needs confirmation before continuing.");
        break;
      }
      try {
        await advanceAgentRunStep(runId);
      } catch {
        appendAssistantMessage("The next safe step could not advance automatically. Click Continue to retry.");
        break;
      }
      const refreshedSteps = await fetchAgentSteps(runId);
      setAgentSteps(refreshedSteps);
      if (conversationId) {
        const refreshedRuns = await fetchAgentRuns(conversationId);
        setAgentRuns(refreshedRuns);
        const currentRun = refreshedRuns.find((run) => run.id === runId) || refreshedRuns[0];
        if (!currentRun || ["paused", "completed", "failed", "cancelled"].includes(currentRun.status)) {
          break;
        }
      }
    }
    if (conversationId) {
      await refreshConversationData(conversationId);
    }
    await refreshModelGateway();
  }
  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setIsUploading(true);
    try {
      await uploadWorkbenchFile(file, currentProjectId || undefined);
      if (currentProjectId) {
        await refreshProjectData(currentProjectId, currentConversationId || undefined);
      } else {
        await refreshProjects();
      }
      appendAssistantMessage("File is quarantined, not parsed, and not sent to any Agent.");
    } catch {
      appendAssistantMessage("文件上传失败。请检查扩展名、大小限制和后端服务。");
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  }

  async function handleConfirmRequirement() {
    if (!currentConversationId) {
      return;
    }
    await confirmRequirement(currentConversationId);
    await refreshConversationData(currentConversationId);
    if (currentProjectId) {
      await refreshProjectData(currentProjectId, currentConversationId);
    }
  }

  async function handleConfirmOutline() {
    if (!currentConversationId) {
      return;
    }
    await confirmOutline(currentConversationId);
    await refreshConversationData(currentConversationId);
    if (currentProjectId) {
      await refreshProjectData(currentProjectId, currentConversationId);
    }
  }

  async function handleStartAgentRun() {
    if (!currentConversationId) {
      return;
    }
    const localSelection = parseLocalModelSelection(selectedModel);
    const run = await startAgentRun(
      currentConversationId,
      currentProjectId || undefined,
      latestTaskContract?.id,
      localSelection?.providerId,
      localSelection?.modelName
    );
    setAgentRuns((current) => [run, ...current]);
    setAgentSteps(await fetchAgentSteps(run.id));
  }

  async function handleAdvanceAgentStep(runId?: string) {
    const targetRunId = runId || agentRuns[0]?.id;
    if (!targetRunId) {
      return;
    }
    await advanceAgentRunStep(targetRunId);
    setAgentSteps(await fetchAgentSteps(targetRunId));
    if (currentConversationId) {
      await refreshConversationData(currentConversationId);
    }
    await refreshModelGateway();
  }

  async function handlePauseAgentRun(runId: string) {
    await pauseAgentRun(runId);
    if (currentConversationId) {
      await refreshConversationData(currentConversationId);
    }
  }

  async function handleResumeAgentRun(runId: string) {
    await resumeAgentRun(runId);
    if (currentConversationId) {
      await refreshConversationData(currentConversationId);
    }
  }

  async function handleCancelAgentRun(runId: string) {
    await cancelAgentRun(runId);
    if (currentConversationId) {
      await refreshConversationData(currentConversationId);
    }
  }

  async function handleInspectFile(fileId: string) {
    setFileInspectResult(await inspectFile(fileId));
  }

  async function handleParseFilePreview(fileId: string) {
    setFilePreviewResult(await parseFilePreview(fileId));
  }

  async function handleSearchMemory(query = "") {
    setMemorySearchResults(await searchMemoryItems(query, currentProjectId || undefined));
  }

  async function handleSecurityRequest() {
    if (!currentProjectId) {
      return;
    }
    await createSecurityRequest(currentProjectId);
    await refreshProjectData(currentProjectId, currentConversationId || undefined);
  }

  async function handleEnableSkill(skillId: string) {
    await updateDbSkillStatus(skillId, "active");
    await refreshSkills();
  }

  async function handleDisableSkill(skillId: string) {
    await disableDbSkill(skillId);
    await refreshSkills();
  }

  async function handleCheckSkill(skill: SkillDbView) {
    const result = await checkSkillConflict(skill);
    setSkillConflictNote(`${result.result}: ${result.reason}`);
  }

  async function handleSaveSuggestion(suggestionId: string, scope: "project" | "global") {
    if (!currentProjectId) {
      return;
    }
    await saveMemorySuggestion(suggestionId, currentProjectId, scope);
    await refreshMemoryItems(currentProjectId);
  }

  async function handleDisableMemory(memoryId: string) {
    await disableMemoryItem(memoryId);
    if (currentProjectId) {
      await refreshMemoryItems(currentProjectId);
    }
  }

  async function handleCreateModelProvider() {
    await createMockModelProvider();
    await refreshModelGateway();
  }

  async function handleCreateLocalProvider() {
    const existing = getPrimaryLocalProvider(modelProviders);
    if (existing) {
      appendAssistantMessage("Local Ollama already exists. Use existing provider instead.");
      setActiveView("providers");
      return;
    }
    await createLocalModelProvider();
    await refreshModelGateway();
  }

  async function handleDisableModelProvider(providerId: string) {
    await disableModelProvider(providerId);
    await refreshModelGateway();
  }

  async function handleEnableModelProvider(providerId: string) {
    await updateModelProvider(providerId, { enabled: true });
    await refreshModelGateway();
  }

  async function handleSetModelProviderActive(providerId: string) {
    await updateModelProvider(providerId, { enabled: true, status: "active" });
    await refreshModelGateway();
  }

  async function handleSetLocalProviderEndpoint(providerId: string, endpoint: string) {
    if (!LOCAL_PROVIDER_ENDPOINTS.includes(endpoint)) {
      appendAssistantMessage("endpoint 不在本机白名单内，前端未提交保存。");
      return;
    }
    await updateModelProvider(providerId, { endpoint });
    await refreshModelGateway();
  }

  async function handleCheckModelProvider(providerId: string) {
    setProviderCheck(await checkModelProvider(providerId));
  }

  async function handleFetchLocalModels(providerId?: string) {
    const targetProviderId = providerId || getPrimaryLocalProvider(modelProviders)?.id || "";
    if (!targetProviderId) {
      return;
    }
    try {
      const result = await fetchLocalModels(targetProviderId);
      const preferredModel = getPreferredLocalModelName(result.models);
      setLocalModels(result.models);
      setSelectedLocalModel((current) => result.models.some((model) => model.name === current) ? current : preferredModel);
      setProviderCheck({
        provider_id: targetProviderId,
        reachable: result.reachable,
        message: result.message || (result.models.length > 0 ? "Local models loaded." : "Local models not loaded. Start Ollama and click Fetch Models."),
        provider_kind: result.models[0]?.provider_kind
      });
    } catch {
      setLocalModels([]);
      setProviderCheck({
        provider_id: targetProviderId,
        reachable: false,
        message: "Local models not loaded. Start Ollama and click Fetch Models.",
        provider_kind: undefined
      });
    }
  }

  async function handleTestModelProvider() {
    const providerId = getPrimaryLocalProvider(modelProviders)?.id || "";
    const modelName = selectedLocalModel || getPreferredLocalModelName(localModels);
    if (!providerId || !modelName) {
      return;
    }
    setLocalInvokeResult(await testModelProvider(providerId, modelName));
    await refreshModelGateway();
  }

  async function handleCreatePromptTemplate() {
    await createPromptTemplate();
    await refreshModelGateway();
  }

  async function handlePreviewPrompt() {
    const providerId = modelProviders.find((provider) => provider.enabled)?.id || modelProviders[0]?.id;
    const promptTemplateId = promptTemplates.find((prompt) => prompt.status === "active")?.id || promptTemplates[0]?.id;
    const taskContractId = taskContracts[0]?.id;
    setPromptPreview(await previewPrompt(providerId, promptTemplateId, taskContractId));
    await refreshModelGateway();
  }

  async function handleReviewInvocation() {
    const providerId = modelProviders.find((provider) => provider.enabled)?.id || modelProviders[0]?.id;
    const promptTemplateId = promptTemplates.find((prompt) => prompt.status === "active")?.id || promptTemplates[0]?.id;
    const taskContractId = taskContracts[0]?.id;
    const review = await reviewModelInvocation(providerId, promptTemplateId, taskContractId);
    setInvocationReview(review);
    if (review.requires_user_approval && !review.blocked) {
      setInvocationApprovalIntent(await createModelInvocationApprovalIntent(providerId, promptTemplateId, taskContractId));
    } else {
      setInvocationApprovalIntent(null);
    }
  }

  async function handleLocalInvoke(userApproved = false, approvalId?: string) {
    const providerId = getPrimaryLocalProvider(modelProviders)?.id || "";
    const modelName = selectedLocalModel || getPreferredLocalModelName(localModels);
    if (!providerId || !modelName) {
      return;
    }
    const promptTemplateId = promptTemplates.find((prompt) => prompt.status === "active")?.id || promptTemplates[0]?.id;
    const taskContractId = taskContracts[0]?.id;
    const result = await invokeLocalModel(providerId, modelName, promptTemplateId, taskContractId, userApproved, approvalId);
    setLocalInvokeResult(result);
    await refreshModelGateway();
    if (result.requires_user_approval && !userApproved) {
      setInvocationApprovalIntent({
        approval_id: result.approval_id,
        provider_id: providerId,
        prompt_template_id: promptTemplateId,
        task_contract_id: taskContractId,
        prompt_hash: result.prompt_hash || "",
        prompt_length: result.redacted_prompt_preview.length,
        risk_level: result.risk_level,
        blocked: result.blocked,
        requires_user_approval: true,
        redacted_preview: result.redacted_prompt_preview,
        findings: result.findings,
        status: "pending",
        expires_at: null,
        message: result.message
      });
      setInvocationReview({
        risk_level: result.risk_level,
        blocked: result.blocked,
        requires_user_approval: true,
        redacted_preview: result.redacted_prompt_preview,
        findings: result.findings,
        recommendation: result.message
      });
    }
  }


  async function handleContinueTask() {
    const currentRun = agentRuns[0];
    if (!currentRun) {
      if (latestTaskContract && currentConversationId) {
        await handleStartAgentRun();
      } else {
        appendAssistantMessage("Please enter a task and click Run Task first.");
      }
      return;
    }
    if (currentRun.status === "paused") {
      await resumeAgentRun(currentRun.id);
      await autoAdvanceSafeRun(currentRun.id, currentConversationId || undefined);
      return;
    } else if (currentRun.status === "running") {
      appendAssistantMessage("Task is currently running. Wait for the current step to finish, then continue.");
      return;
    } else if (currentRun.status === "completed") {
      appendAssistantMessage("Task completed. You can review the final output or start a new task.");
      return;
    } else if (currentRun.status === "cancelled" || currentRun.status === "failed") {
      appendAssistantMessage("This run needs attention. Open Advanced Details for diagnostics.");
      return;
    } else {
      await autoAdvanceSafeRun(currentRun.id, currentConversationId || undefined);
      return;
    }
  }

  function handleUiPreferenceChange(key: keyof UiPreferences, value: boolean) {
    setUiPreferences((current) => ({ ...current, [key]: value }));
  }
  function appendAssistantMessage(content: string) {
    setMessages((current) => [
      ...current,
      { id: `local-${Date.now()}`, role: "assistant", content, timestamp: new Date().toISOString() }
    ]);
  }

  if (!state) {
    return <div className="loading">Loading workbench...</div>;
  }

  return (
    <div className="app-shell">
      <TopStatusBar
        database={state.database}
        currentProject={currentProject}
        currentConversation={currentConversation}
        selectedModelDescription={selectedModelDescription}
        selectedModelName={modelOptions.find((model) => model.id === selectedModel)?.name || selectedLocalModel || "qwen2.5:7b"}
        modelProviders={modelProviders}
      />
      <div className="workbench-layout">
        <Sidebar
          activeView={activeView}
          onViewChange={setActiveView}
          projects={projects}
          currentProjectId={currentProjectId}
          onSelectProject={setCurrentProjectId}
          onCreateProject={handleCreateProject}
          conversations={conversations}
          currentConversationId={currentConversationId}
          onSelectConversation={setCurrentConversationId}
          taskContracts={taskContracts}
          skills={skills}
          modelProviders={modelProviders}
          artifactCount={(hybridArchitecture?.artifact_center ?? []).length + agentDeliverables.length}
        />
        <MainWorkspace
          activeView={activeView}
          uiPreferences={uiPreferences}
          onUiPreferenceChange={handleUiPreferenceChange}
          state={state}
          messages={messages}
          files={files}
          taskContracts={taskContracts}
          latestTaskContract={latestTaskContract}
          latestDeliverable={latestDeliverable}
          agentDeliverables={agentDeliverables}
          latestReview={latestReview}
          agentRuns={agentRuns}
          agentSteps={agentSteps}
          skills={skills}
          memoryItems={memoryItems}
          memorySearchResults={memorySearchResults}
          fileInspectResult={fileInspectResult}
          filePreviewResult={filePreviewResult}
          modelProviders={modelProviders}
          promptTemplates={promptTemplates}
          promptPreview={promptPreview}
          invocationApprovalIntent={invocationApprovalIntent}
          invocationReview={invocationReview}
          localInvokeResult={localInvokeResult}
          hybridArchitecture={hybridArchitecture}
          providerCheck={providerCheck}
          localModels={localModels}
          selectedLocalModel={selectedLocalModel}
          localProviderEndpoints={LOCAL_PROVIDER_ENDPOINTS}
          selectedModel={selectedModel}
          selectedModelDescription={selectedModelDescription}
          modelOptions={modelOptions}
          pendingLocalChatRequest={pendingLocalChatRequest}
          input={input}
          isSending={isSending}
          isUploading={isUploading}
          skillConflictNote={skillConflictNote}
          fileInputRef={fileInputRef}
          onModelChange={setSelectedModel}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          onConfirmPendingLocalChat={handleConfirmPendingLocalChat}
          onUpload={handleUpload}
          onOpenUploadPicker={() => fileInputRef.current?.click()}
          onConfirmRequirement={handleConfirmRequirement}
          onConfirmOutline={handleConfirmOutline}
          onStartAgentRun={handleStartAgentRun}
          onContinueTask={handleContinueTask}
          onAdvanceAgentStep={handleAdvanceAgentStep}
          onInspectFile={handleInspectFile}
          onParseFilePreview={handleParseFilePreview}
          onCreateSkill={handleCreateSkill}
          onEnableSkill={handleEnableSkill}
          onDisableSkill={handleDisableSkill}
          onCheckSkill={handleCheckSkill}
          onSaveSuggestion={handleSaveSuggestion}
          onDisableMemory={handleDisableMemory}
          onSearchMemory={handleSearchMemory}
          onCreateMockProvider={handleCreateModelProvider}
          onCreateLocalProvider={handleCreateLocalProvider}
          onEnableProvider={handleEnableModelProvider}
          onSetProviderActive={handleSetModelProviderActive}
          onDisableProvider={handleDisableModelProvider}
          onSetLocalEndpoint={handleSetLocalProviderEndpoint}
          onCheckProvider={handleCheckModelProvider}
          onFetchLocalModels={handleFetchLocalModels}
          onSelectLocalModel={setSelectedLocalModel}
          onTestProvider={handleTestModelProvider}
          onCreatePromptTemplate={handleCreatePromptTemplate}
          onPreviewPrompt={handlePreviewPrompt}
          onReviewInvocation={handleReviewInvocation}
          onLocalInvoke={handleLocalInvoke}
        />
        <RightInspector
          uiPreferences={uiPreferences}
          latestTaskContract={latestTaskContract}
          agentRuns={agentRuns}
          agentSteps={agentSteps}
          agentDeliverables={agentDeliverables}
          reviewResults={reviewResults}
          modelProviders={modelProviders}
          modelInvocationLogs={modelInvocationLogs}
          promptTemplates={promptTemplates}
          promptPreview={promptPreview}
          invocationApprovalIntent={invocationApprovalIntent}
          invocationReview={invocationReview}
          providerCheck={providerCheck}
          localModels={localModels}
          selectedLocalModel={selectedLocalModel}
          localInvokeResult={localInvokeResult}
          hybridArchitecture={hybridArchitecture}
          files={files}
          securityRequests={securityRequests}
          auditLogs={auditLogs}
          memoryItems={memoryItems}
          currentSkill={state.current_skill}
          localProviderEndpoints={LOCAL_PROVIDER_ENDPOINTS}
          onAdvanceAgentStep={handleAdvanceAgentStep}
          onPauseAgentRun={handlePauseAgentRun}
          onResumeAgentRun={handleResumeAgentRun}
          onCancelAgentRun={handleCancelAgentRun}
          onCreateMockProvider={handleCreateModelProvider}
          onCreateLocalProvider={handleCreateLocalProvider}
          onEnableProvider={handleEnableModelProvider}
          onSetProviderActive={handleSetModelProviderActive}
          onDisableProvider={handleDisableModelProvider}
          onSetLocalEndpoint={handleSetLocalProviderEndpoint}
          onCheckProvider={handleCheckModelProvider}
          onFetchLocalModels={handleFetchLocalModels}
          onSelectLocalModel={setSelectedLocalModel}
          onTestProvider={handleTestModelProvider}
          onCreatePromptTemplate={handleCreatePromptTemplate}
          onLocalInvoke={handleLocalInvoke}
          onSecurityRequest={handleSecurityRequest}
          onSaveSuggestion={handleSaveSuggestion}
        />
      </div>
    </div>
  );
}

function parseLocalModelSelection(value: string): { providerId: string; modelName: string } | null {
  if (!value.startsWith("local::")) {
    return null;
  }
  const [, providerId, modelName] = value.split("::");
  if (!providerId || !modelName) {
    return null;
  }
  return { providerId, modelName };
}

export default App;
