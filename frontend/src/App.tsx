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
import type { PendingLocalChatRequestView, WorkbenchView } from "./components/componentTypes";
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
    const localProvider = modelProviders.find((provider) => isLocalProvider(provider.provider_type));
    const localOptions = localProvider
      ? localModels.map((model) => ({
          id: `local::${localProvider.id}::${model.name}`,
          name: `${model.name} / ${model.provider_kind}`,
          enabled: localProvider.enabled && localProvider.status === "active",
          description: "主控 Agent 使用本地模型生成需求确认和大纲。",
          provider: "local"
        }))
      : [];
    return [...(state?.models ?? []), ...localOptions];
  }, [localModels, modelProviders, state?.models]);

  const selectedModelDescription =
    modelOptions.find((model) => model.id === selectedModel)?.description || "默认不调用模型；仅在启用 active local provider 并通过审查后调用本机模型。";
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
      appendAssistantMessage("后端暂不可用。请确认 FastAPI 服务已启动后重试。");
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
      appendAssistantMessage("本地主控 Agent 确认后重试失败。请检查后端和本机 provider。");
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
      appendAssistantMessage(response.safety_message || "本地主控 Agent 需要安全确认或已被阻断。");
    }
    if (response.fallback_used && !response.requires_user_approval && !response.blocked) {
      appendAssistantMessage("模型输出 JSON 解析失败，已使用安全 fallback。");
    }
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
      appendAssistantMessage("文件已隔离，未解析，未发送给 Agent。");
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
    const targetProviderId = providerId || modelProviders.find((provider) => isLocalProvider(provider.provider_type))?.id || "";
    if (!targetProviderId) {
      return;
    }
    const result = await fetchLocalModels(targetProviderId);
    setLocalModels(result.models);
    setSelectedLocalModel((current) => current || result.models[0]?.name || "");
    setProviderCheck({
      provider_id: targetProviderId,
      reachable: result.reachable,
      message: result.message,
      provider_kind: result.models[0]?.provider_kind
    });
  }

  async function handleTestModelProvider() {
    const providerId = modelProviders.find((provider) => isLocalProvider(provider.provider_type))?.id || "";
    const modelName = selectedLocalModel || localModels[0]?.name || "";
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
    const providerId = modelProviders.find((provider) => isLocalProvider(provider.provider_type))?.id || "";
    const modelName = selectedLocalModel || localModels[0]?.name || "";
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
          state={state}
          messages={messages}
          files={files}
          taskContracts={taskContracts}
          latestTaskContract={latestTaskContract}
          latestDeliverable={latestDeliverable}
          latestReview={latestReview}
          agentRuns={agentRuns}
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

function isLocalProvider(providerType: string): boolean {
  return providerType === "local_ollama" || providerType === "local";
}

export default App;
