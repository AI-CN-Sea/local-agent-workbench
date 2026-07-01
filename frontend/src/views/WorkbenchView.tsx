import { Paperclip, Play } from "lucide-react";

import type { AgentDeliverableView, AgentRunView, AgentStepView, Message, ReviewResultView, TaskContractView, UploadedFileView } from "../types";
import { ArtifactPreview } from "../components/ArtifactPreview";
import { EmptyState } from "../components/EmptyState";
import { formatBytes, formatTime, shortHash } from "../components/format";
import { StatusBadge } from "../components/StatusBadge";
import { getPrimaryLocalProvider } from "../components/localProvider";
import type { WorkspaceViewProps } from "./viewTypes";

const progressStages = [
  "Understanding Request",
  "Planning",
  "Generating Output",
  "Reviewing Result",
  "Completed"
];

export function WorkbenchView(props: WorkspaceViewProps) {
  const primaryProvider = getPrimaryLocalProvider(props.modelProviders);
  const activeProvider = primaryProvider?.enabled && primaryProvider.status === "active" ? primaryProvider : undefined;
  const selectedModel = props.modelOptions.find((model) => model.id === props.selectedModel);
  const displayModel = selectedModel?.name || props.selectedLocalModel || "qwen2.5:7b";
  const finalOutput = selectFinalOutput(props.agentDeliverables, props.latestReview, props.uiPreferences.showMockArtifacts);
  const visibleArtifacts = props.uiPreferences.showMockArtifacts
    ? props.hybridArchitecture?.artifact_center ?? []
    : (props.hybridArchitecture?.artifact_center ?? []).filter((artifact) => !isMockArtifact(String(artifact.status || artifact.artifact_type || artifact.title || "")));
  const progress = buildProgress(props.latestTaskContract, props.agentRuns[0], props.agentSteps, props.latestDeliverable, props.latestReview);
  const review = buildReviewSummary(props.latestTaskContract, props.latestReview, props.agentRuns[0]);

  return (
    <>
      <header className="simple-hero">
        <div>
          <span className="panel-eyebrow">Simple Workbench</span>
          <h1>Run a local Agent task</h1>
          <p>Enter a task, choose a local model, and let the workbench handle low-risk local steps automatically.</p>
        </div>
        <div className="simple-status-strip">
          <StatusBadge kind="REAL_LOCAL" label="Local Only" />
          <StatusBadge kind={activeProvider ? "REAL_LOCAL" : "REQUIRES_APPROVAL"} label={activeProvider ? "Ollama Active" : "Ollama Needs Active"} />
          <StatusBadge kind="NO_EXTERNAL_CALL" label="External API Disabled" />
          <StatusBadge kind="NO_DESKTOP_EXECUTION" label="Desktop Tool Disabled" />
        </div>
      </header>

      <div className="simple-scroll">
        <section className="simple-task-card">
          <div className="section-heading">
            <div>
              <span className="panel-eyebrow">Current model</span>
              <h2>{displayModel}</h2>
            </div>
            <StatusBadge kind={selectedModel?.enabled ? "REAL_LOCAL" : "MOCK_ONLY"} label={selectedModel?.provider === "local" ? "Local Ollama" : "Mock / fallback"} />
          </div>
          <form className="simple-task-form" onSubmit={props.onSubmit}>
            <input ref={props.fileInputRef} className="hidden-file-input" type="file" onChange={props.onUpload} />
            <label className="model-picker simple-model-picker">
              <span>Model</span>
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
              placeholder="请输入你想让本地 Agent 完成的任务"
              rows={4}
            />
            <div className="simple-task-actions">
              <button type="button" onClick={props.onOpenUploadPicker} disabled={props.isUploading} title="Upload to quarantine">
                <Paperclip size={16} /> Upload
              </button>
              <button type="button" onClick={() => props.onInputChange("")}>Clear / New Task</button>
              <button type="submit" className="primary-button" disabled={props.isSending || !props.input.trim()}>
                <Play size={16} /> Run Task / 运行任务
              </button>
            </div>
          </form>
        </section>

        {props.pendingLocalChatRequest && (
          <section className="attention-card">
            <strong>Needs confirmation</strong>
            <p>This local model request is medium risk. Confirm once to continue this run.</p>
            <button type="button" className="warning-button" onClick={props.onConfirmPendingLocalChat}>Confirm medium risk and continue</button>
          </section>
        )}

        <section className="simple-progress-card">
          <div className="section-heading">
            <div>
              <span className="panel-eyebrow">Processing progress</span>
              <h2>Task progress</h2>
            </div>
            <button type="button" onClick={() => props.onContinueTask()} disabled={props.isSending}>
              Continue
            </button>
          </div>
          <div className="progress-steps">
            {progressStages.map((stage) => (
              <div className={`progress-step progress-${progress[stage].replace(" ", "-")}`} key={stage}>
                <span>{stage}</span>
                <strong>{progress[stage]}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="simple-output-card">
          <div className="section-heading">
            <div>
              <span className="panel-eyebrow">Local Model Output</span>
              <h2>Final Output</h2>
            </div>
            <StatusBadge kind={finalOutput.kind === "local" ? "REAL_LOCAL" : finalOutput.kind === "fallback" ? "MOCK_ONLY" : "RUNNING"} label={finalOutput.label} />
          </div>
          {finalOutput.content ? (
            <pre className="final-output">{finalOutput.content}</pre>
          ) : (
            <EmptyState title="任务正在处理中" description={`当前已完成：${completedStageText(progress)}。点击 Continue 可继续推进低风险本地步骤。`} />
          )}
        </section>

        <section className="review-summary-card">
          <div className="section-heading">
            <div>
              <span className="panel-eyebrow">Review Summary</span>
              <h2>Quality check</h2>
            </div>
            <StatusBadge kind={review.riskKind} label={review.riskLabel} />
          </div>
          <div className="review-grid">
            <SummaryItem label="Completion" value={review.completion} />
            <SummaryItem label="Privacy" value={review.privacy} />
            <SummaryItem label="Risk" value={review.riskLabel} />
            <SummaryItem label="Suggested Next Step" value={review.nextStep} wide />
          </div>
        </section>

        <details className="advanced-details" open={props.uiPreferences.showDebugInformation || !props.uiPreferences.simpleMode}>
          <summary>Advanced Details / Developer Inspector</summary>
          <div className="advanced-grid">
            <TaskContractStrip taskContracts={props.taskContracts} onConfirmRequirement={props.onConfirmRequirement} onConfirmOutline={props.onConfirmOutline} showRawTaskContract={props.uiPreferences.showRawTaskContract} showPipelineSteps={props.uiPreferences.showPipelineSteps} />
            <FileIsolationList
              files={props.files}
              fileInspectResult={props.fileInspectResult}
              filePreviewResult={props.filePreviewResult}
              onInspectFile={props.onInspectFile}
              onParseFilePreview={props.onParseFilePreview}
            />
            <ConversationFeed messages={props.messages} />
            <ArtifactPreview
              artifacts={visibleArtifacts}
              latestDeliverable={props.latestDeliverable}
              latestReview={props.latestReview}
              compact
            />
          </div>
        </details>
      </div>
    </>
  );
}

function SummaryItem({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={`summary-item ${wide ? "summary-item-wide" : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
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
    return <EmptyState title="No uploaded files" description="Uploads enter quarantine. They are not opened, extracted, parsed, or sent to any Agent." />;
  }

  return (
    <section className="inline-section flat-section">
      <div className="section-heading">
        <h2>Quarantine files</h2>
        <StatusBadge kind="REQUIRES_APPROVAL" label="not parsed / not sent to Agent" />
      </div>
      <div className="file-list">
        {files.slice(0, 6).map((file) => (
          <article className="file-item" key={file.id}>
            <strong>{file.original_filename}</strong>
            <small>{formatBytes(file.size_bytes)} / {toUserStatus(file.status)} / sha256 {shortHash(file.sha256)} / {formatTime(file.created_at)}</small>
            <div className="mini-actions">
              <button type="button" onClick={() => onInspectFile(file.id)}>Inspect metadata</button>
              <button type="button" onClick={() => onParseFilePreview(file.id)}>Request parse preview</button>
            </div>
          </article>
        ))}
      </div>
      {fileInspectResult && <p className="notice-line">Inspect: {fileInspectResult.original_filename} / {fileInspectResult.message}</p>}
      {filePreviewResult && <p className="notice-line">Parse preview: {filePreviewResult.blocked ? "blocked" : "mock"} / {filePreviewResult.message}</p>}
    </section>
  );
}

function ConversationFeed({ messages }: { messages: Message[] }) {
  if (messages.length === 0) {
    return <EmptyState title="No messages" description="Messages will be stored in the current conversation." />;
  }
  return (
    <section className="conversation-feed" aria-label="Conversation messages">
      {messages.slice(-8).map((message) => (
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
  onConfirmOutline,
  showRawTaskContract,
  showPipelineSteps
}: Pick<WorkspaceViewProps, "taskContracts" | "onConfirmRequirement" | "onConfirmOutline"> & { showRawTaskContract: boolean; showPipelineSteps: boolean }) {
  if (taskContracts.length === 0) {
    return <EmptyState title="No Task Contract" description="A low-risk task creates a Task Contract automatically after Run Task." />;
  }

  return (
    <section className="inline-section flat-section">
      <div className="section-heading">
        <h2>Task Contract</h2>
        <div className="mini-actions">
          <button type="button" onClick={onConfirmRequirement}>Confirm Requirement</button>
          <button type="button" onClick={onConfirmOutline}>Confirm Outline</button>
        </div>
      </div>
      <div className="card-grid">
        {taskContracts.slice(0, 3).map((contract) => (
          <article className="compact-item" key={contract.id}>
            <div className="row-between">
              <strong>{contract.title}</strong>
              <StatusBadge kind={contract.execution_allowed ? "COMPLETED" : "REQUIRES_APPROVAL"} label={toUserStatus(contract.status)} />
            </div>
            <small>{contract.objective}</small>
            {showPipelineSteps && <small>{contract.inputs.length} inputs / {contract.outputs.length} outputs / {contract.steps.length} steps</small>}
            {showRawTaskContract && (
              <details>
                <summary>Raw metadata</summary>
                <pre className="redacted-preview">{JSON.stringify(contract.metadata, null, 2)}</pre>
              </details>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function selectFinalOutput(deliverables: AgentDeliverableView[], latestReview?: ReviewResultView, showMockArtifacts = false) {
  const visibleDeliverables = showMockArtifacts ? deliverables : deliverables.filter((item) => !isMockArtifact(`${item.agent_name} ${item.status} ${item.summary}`));
  const findLocal = (agentPattern: RegExp, summaryPattern?: RegExp) => visibleDeliverables.find((item) =>
    item.status === "local_model_generated" && (agentPattern.test(item.agent_name) || Boolean(summaryPattern?.test(item.summary)))
  );
  const codeOutput = findLocal(/code agent|code_implementation|code_specialist/i, /code_implementation|code_specialist/i);
  const documentOutput = findLocal(/document|writer|writing|formatting/i, /document_generation|writing/i);
  const plannerOutput = findLocal(/planner|planning/i, /planning|requirement/i);
  const fallbackOutput = visibleDeliverables.find((item) => item.status === "fallback_generated");
  const otherOutput = visibleDeliverables.find((item) => item.status !== "fallback_generated");
  const selected = codeOutput || documentOutput;

  if (selected) {
    return {
      content: selected.summary,
      kind: "local",
      label: toUserStatus(selected.status)
    };
  }
  if (latestReview) {
    return {
      content: latestReview.findings.concat(latestReview.recommendations).slice(0, 4).join("\n"),
      kind: "generated",
      label: "Review summary"
    };
  }
  const secondary = plannerOutput || fallbackOutput || otherOutput;
  if (secondary) {
    return {
      content: secondary.summary,
      kind: secondary.status === "local_model_generated" ? "local" : secondary.status === "fallback_generated" ? "fallback" : "generated",
      label: toUserStatus(secondary.status)
    };
  }
  return { content: "", kind: "empty", label: "Processing" };
}

function isMockArtifact(value: string) {
  const normalized = value.toLowerCase();
  return normalized.includes("mock codex instruction plan")
    || normalized.includes("mock document outline")
    || normalized.includes("mock diagram spec")
    || normalized.includes("mock_only");
}

function buildProgress(
  contract: TaskContractView | undefined,
  run: AgentRunView | undefined,
  steps: AgentStepView[],
  deliverable: AgentDeliverableView | undefined,
  review: ReviewResultView | undefined
): Record<string, "pending" | "running" | "completed" | "needs attention"> {
  const result: Record<string, "pending" | "running" | "completed" | "needs attention"> = {
    "Understanding Request": contract ? "completed" : "pending",
    Planning: steps.length > 0 || run ? "completed" : contract ? "running" : "pending",
    "Generating Output": deliverable ? "completed" : run?.status === "running" ? "running" : "pending",
    "Reviewing Result": review ? "completed" : deliverable ? "running" : "pending",
    Completed: run?.status === "completed" || review ? "completed" : run?.status === "failed" ? "needs attention" : "pending"
  };
  if (contract && !contract.execution_allowed) {
    result["Understanding Request"] = "needs attention";
  }
  return result;
}

function completedStageText(progress: Record<string, string>) {
  const completed = progressStages.filter((stage) => progress[stage] === "completed");
  return completed.length > 0 ? completed.join(" / ") : "waiting for task input";
}

function buildReviewSummary(contract?: TaskContractView, review?: ReviewResultView, run?: AgentRunView) {
  const risk = normalizeRisk(contract?.risk_level || review?.severity || "normal");
  const completion = review ? (review.approved ? "Passed" : "Needs work") : run?.status === "completed" ? "Passed" : "Processing";
  const riskKind: "HIGH_RISK" | "MEDIUM_RISK" | "LOW_RISK" = risk === "high" ? "HIGH_RISK" : risk === "medium" ? "MEDIUM_RISK" : "LOW_RISK";
  return {
    completion,
    privacy: contract?.external_allowed ? "Needs external approval" : "Local Only / No External Call",
    riskLabel: risk === "high" ? "Needs Confirmation" : risk === "medium" ? "Needs Attention" : "Normal / Low",
    riskKind,
    nextStep: review?.recommendations?.[0] || (run?.status === "completed" ? "Review the final output and start a new task if needed." : "Click Continue to advance the next safe local step.")
  };
}
function normalizeRisk(value: string): "low" | "medium" | "high" {
  const normalized = value.toLowerCase();
  if (normalized.includes("critical") || normalized.includes("high") || normalized.includes("p4")) return "high";
  if (normalized.includes("medium") || normalized.includes("p3") || normalized.includes("p2")) return "medium";
  return "low";
}

function toUserStatus(status: string) {
  const map: Record<string, string> = {
    blocked: "Needs confirmation",
    draft: "Ready",
    running: "Running",
    paused: "Waiting to continue",
    completed: "Completed",
    failed: "Needs attention",
    fallback_generated: "Safe local fallback",
    fallback_requirement_analysis: "Safe local fallback",
    local_master_agent_unavailable: "Needs local model setup",
    hybrid_local_controlled_pipeline: "Local controlled pipeline",
    local_model_generated: "Generated by local model",
    waiting_requirement_confirmation: "Ready",
    waiting_outline_confirmation: "Ready"
  };
  return map[status] || status;
}

