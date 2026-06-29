import { Paperclip, Play, Send, Square } from "lucide-react";

import type { AgentRunView, TaskContractView, UploadedFileView, WorkbenchState } from "../types";
import { ArtifactPreview } from "../components/ArtifactPreview";
import { EmptyState } from "../components/EmptyState";
import { formatBytes, formatTime, metadataText, shortHash } from "../components/format";
import { StatusBadge } from "../components/StatusBadge";
import type { PendingLocalChatRequestView } from "../components/componentTypes";
import type { WorkspaceViewProps } from "./viewTypes";

export function WorkbenchView(props: WorkspaceViewProps) {
  const hasTaskData = props.taskContracts.length > 0 || props.files.length > 0 || props.latestDeliverable;

  return (
    <>
      <TaskHeader latestTaskContract={props.latestTaskContract} state={props.state} />

      <div className="conversation-scroll">
        <ConversationFeed messages={props.messages} />
        {!hasTaskData && (
          <EmptyState
            title="发送需求后将生成 Task Contract、Skill Pipeline 和安全检查结果。"
            description="当前不会读取上传文件正文，也不会调用外部 API；mock 流程可直接验证交互。"
          />
        )}
        <details className="workspace-fold" open={props.files.length > 0}>
          <summary>文件隔离</summary>
          <FileIsolationList
            files={props.files}
            fileInspectResult={props.fileInspectResult}
            filePreviewResult={props.filePreviewResult}
            onInspectFile={props.onInspectFile}
            onParseFilePreview={props.onParseFilePreview}
          />
        </details>
        <details className="workspace-fold" open={props.taskContracts.length > 0}>
          <summary>Task Contract</summary>
          <TaskContractStrip
            taskContracts={props.taskContracts}
            onConfirmRequirement={props.onConfirmRequirement}
            onConfirmOutline={props.onConfirmOutline}
          />
        </details>
        <details className="workspace-fold" open={Boolean(props.latestDeliverable)}>
          <summary>Artifact Preview</summary>
          <ArtifactPreview
            artifacts={props.hybridArchitecture?.artifact_center ?? []}
            latestDeliverable={props.latestDeliverable}
            latestReview={props.latestReview}
            compact
          />
        </details>
      </div>

      <ActionBar
        currentRun={props.agentRuns[0]}
        latestTaskContract={props.latestTaskContract}
        pendingLocalChatRequest={props.pendingLocalChatRequest}
        state={props.state}
        onConfirmPendingLocalChat={props.onConfirmPendingLocalChat}
        onConfirmRequirement={props.onConfirmRequirement}
        onConfirmOutline={props.onConfirmOutline}
        onStartAgentRun={props.onStartAgentRun}
        onAdvanceAgentStep={props.onAdvanceAgentStep}
      />

      <form className="composer" onSubmit={props.onSubmit}>
        <input ref={props.fileInputRef} className="hidden-file-input" type="file" onChange={props.onUpload} />
        <button type="button" className="icon-button" onClick={props.onOpenUploadPicker} disabled={props.isUploading} title="上传到 quarantine">
          <Paperclip size={17} />
        </button>
        <label className="model-picker">
          <span>模型</span>
          <select value={props.selectedModel} onChange={(event) => props.onModelChange(event.target.value)}>
            {props.modelOptions.map((model) => (
              <option key={model.id} value={model.id} disabled={!model.enabled}>
                {model.name}
              </option>
            ))}
          </select>
        </label>
        <textarea
          value={props.input}
          onChange={(event) => props.onInputChange(event.target.value)}
          placeholder="输入需求；可使用 mock 流程或受控本地模型主控 Agent。"
          rows={1}
        />
        <button type="submit" className="primary-button" disabled={props.isSending || !props.input.trim()}>
          <Send size={17} />
          Send
        </button>
      </form>
    </>
  );
}

export function FileIsolationList({
  files,
  fileInspectResult,
  filePreviewResult,
  onInspectFile,
  onParseFilePreview
}: Pick<WorkspaceViewProps, "files" | "fileInspectResult" | "filePreviewResult" | "onInspectFile" | "onParseFilePreview">) {
  if (files.length === 0) {
    return <EmptyState title="暂无上传文件" description="上传后进入 quarantine，不自动打开、不解压、不解析。" />;
  }

  return (
    <section className="inline-section flat-section">
      <div className="section-heading">
        <h2>文件隔离</h2>
        <StatusBadge kind="REQUIRES_APPROVAL" label="quarantine / 未解析 / 未发送给 Agent" />
      </div>
      <div className="file-list">
        {files.slice(0, 6).map((file) => (
          <article className="file-item" key={file.id}>
            <strong>{file.original_filename}</strong>
            <small>
              {formatBytes(file.size_bytes)} / {file.status} / sha256 {shortHash(file.sha256)} / {formatTime(file.created_at)}
            </small>
            <div className="mini-actions">
              <button type="button" onClick={() => onInspectFile(file.id)}>隔离检查</button>
              <button type="button" onClick={() => onParseFilePreview(file.id)}>解析预览申请</button>
            </div>
          </article>
        ))}
      </div>
      {fileInspectResult && <p className="notice-line">Inspect: {fileInspectResult.original_filename} / {fileInspectResult.message}</p>}
      {filePreviewResult && <p className="notice-line">Parse preview: {filePreviewResult.blocked ? "blocked" : "mock"} / {filePreviewResult.message}</p>}
    </section>
  );
}

function TaskHeader({ latestTaskContract, state }: { latestTaskContract?: TaskContractView; state: WorkbenchState }) {
  const currentStatus = latestTaskContract?.status || state.conversation.requirement_card.status;
  const chips = [
    ["task_type", metadataText(latestTaskContract?.metadata?.task_type, "general")],
    ["skill", latestTaskContract?.selected_skill || state.current_skill.name],
    ["privacy", latestTaskContract?.privacy_level || "local_only"],
    ["status", currentStatus],
    ["executor", latestTaskContract?.recommended_executor || "Planner"]
  ];

  return (
    <header className="task-header compact-task-header">
      <div className="task-title-block">
        <span className="panel-eyebrow">Current Task</span>
        <h1>{latestTaskContract?.title || state.conversation.title}</h1>
        <p>{latestTaskContract?.objective || "当前对话尚未生成 Task Contract，可先发送需求或继续 mock 流程。"}</p>
      </div>
      <div className="task-chip-row">
        {chips.map(([label, value]) => (
          <span className="task-chip" key={label} title={value}>
            <small>{label}</small>
            <strong>{value}</strong>
          </span>
        ))}
      </div>
    </header>
  );
}

function ConversationFeed({ messages }: Pick<WorkspaceViewProps, "messages">) {
  if (messages.length === 0) {
    return <EmptyState title="暂无消息" description="在底部输入框发送需求后，消息会保存在当前 conversation。" />;
  }
  return (
    <section className="conversation-feed" aria-label="Conversation messages">
      {messages.map((message) => (
        <article className={`message-row message-${message.role}`} key={message.id}>
          <div className="message-meta">
            <strong>{message.role}</strong>
            <small>{formatTime(message.timestamp)}</small>
          </div>
          <p>{message.content}</p>
        </article>
      ))}
    </section>
  );
}

function TaskContractStrip({
  taskContracts,
  onConfirmRequirement,
  onConfirmOutline
}: Pick<WorkspaceViewProps, "taskContracts" | "onConfirmRequirement" | "onConfirmOutline">) {
  if (taskContracts.length === 0) {
    return <EmptyState title="暂无 Task Contract" description="确认需求后会在这里显示任务协议摘要。" />;
  }

  return (
    <section className="inline-section flat-section">
      <div className="section-heading">
        <h2>Task Contract</h2>
        <div className="mini-actions">
          <button type="button" onClick={onConfirmRequirement}>确认需求</button>
          <button type="button" onClick={onConfirmOutline}>确认大纲</button>
        </div>
      </div>
      <div className="card-grid">
        {taskContracts.slice(0, 3).map((contract) => (
          <article className="compact-item" key={contract.id}>
            <div className="row-between">
              <strong>{contract.title}</strong>
              <StatusBadge kind={contract.execution_allowed ? "COMPLETED" : "REQUIRES_APPROVAL"} label={contract.status} />
            </div>
            <small>{contract.objective}</small>
            <small>{contract.inputs.length} inputs / {contract.outputs.length} outputs / {contract.steps.length} steps</small>
          </article>
        ))}
      </div>
    </section>
  );
}

function ActionBar({
  currentRun,
  latestTaskContract,
  pendingLocalChatRequest,
  state,
  onConfirmPendingLocalChat,
  onConfirmRequirement,
  onConfirmOutline,
  onStartAgentRun,
  onAdvanceAgentStep
}: {
  currentRun?: AgentRunView;
  latestTaskContract?: TaskContractView;
  pendingLocalChatRequest: PendingLocalChatRequestView | null;
  state: WorkbenchState;
  onConfirmPendingLocalChat: () => void;
  onConfirmRequirement: () => void;
  onConfirmOutline: () => void;
  onStartAgentRun: () => void;
  onAdvanceAgentStep: (runId?: string) => void;
}) {
  const action = resolvePrimaryAction({ currentRun, latestTaskContract, pendingLocalChatRequest, state });
  const primaryHandler =
    action.kind === "medium"
      ? onConfirmPendingLocalChat
      : action.kind === "requirement"
        ? onConfirmRequirement
        : action.kind === "outline"
          ? onConfirmOutline
          : action.kind === "start"
            ? onStartAgentRun
            : () => onAdvanceAgentStep(currentRun?.id);

  return (
    <div className="action-bar compact-action-bar">
      <div className="next-action">
        <strong>下一步：{action.label}</strong>
        <small>{action.description}</small>
      </div>
      <div className="action-buttons">
        <button type="button" className={action.kind === "medium" ? "warning-button" : "primary-button"} onClick={primaryHandler}>
          {action.kind === "start" && <Play size={16} />}
          {action.label}
        </button>
        <details className="more-actions">
          <summary>更多操作</summary>
          <div className="more-actions-menu">
            <button type="button" onClick={onConfirmRequirement}>Confirm Requirement</button>
            <button type="button" onClick={onConfirmOutline}>Confirm Outline</button>
            <button type="button" onClick={() => onAdvanceAgentStep(currentRun?.id)}>Advance Step</button>
            <button type="button" className="danger-button" disabled={!currentRun}>
              <Square size={15} /> Stop / Cancel
            </button>
          </div>
        </details>
      </div>
    </div>
  );
}

function resolvePrimaryAction({
  currentRun,
  latestTaskContract,
  pendingLocalChatRequest,
  state
}: {
  currentRun?: AgentRunView;
  latestTaskContract?: TaskContractView;
  pendingLocalChatRequest: PendingLocalChatRequestView | null;
  state: WorkbenchState;
}): { kind: "medium" | "requirement" | "outline" | "start" | "advance"; label: string; description: string } {
  if (pendingLocalChatRequest) {
    return { kind: "medium", label: "Confirm Medium Risk", description: "当前本地主控调用为 medium 风险，需要显式确认后才会继续。" };
  }
  const requirementStatus = state.conversation.requirement_card.status;
  const outlineStatus = state.conversation.outline_card.status;
  if (!latestTaskContract || requirementStatus === "waiting_requirement_confirmation") {
    return { kind: "requirement", label: "Confirm Requirement", description: "先确认需求卡片，再进入大纲和 Task Contract 流程。" };
  }
  if (outlineStatus === "waiting_outline_confirmation" || latestTaskContract.status === "waiting_outline_confirmation") {
    return { kind: "outline", label: "Confirm Outline", description: "确认大纲后，任务会进入可启动 Agent Run 的状态。" };
  }
  if (!currentRun) {
    return { kind: "start", label: "Start Agent Run", description: "Task Contract 已准备好，可以启动 mock/本地受控 Agent Run。" };
  }
  return { kind: "advance", label: "Advance Step", description: "继续推进当前 Agent Run 的下一步。" };
}
