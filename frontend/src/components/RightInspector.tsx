import { Archive, Bot, FileText, PanelRightClose, PanelRightOpen, Route, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";

import type {
  AgentDeliverableView,
  AgentRunView,
  AgentStepView,
  HybridArchitectureState,
  LocalModelInfo,
  LocalModelInvokeResponse,
  MemoryItemDbView,
  ModelInvocationApprovalIntent,
  ModelInvocationApprovalReview,
  ModelInvocationLogView,
  ModelInvocationReview,
  ModelProviderCheckResult,
  ModelProviderView,
  NetworkAuditLogView,
  PromptTemplateView,
  ReviewResultView,
  SecurityRequestView,
  SkillInfo,
  TaskContractView,
  UploadedFileView
} from "../types";
import type { InspectorTab, UiPreferences } from "./componentTypes";
import { AgentRunTimeline } from "./AgentRunTimeline";
import { ArtifactPreview } from "./ArtifactPreview";
import { EmptyState } from "./EmptyState";
import { formatCost, formatTime, metadataText, shortHash } from "./format";
import { PanelCard } from "./PanelCard";
import { StatusBadge } from "./StatusBadge";
import { getPrimaryLocalProvider, isLocalProviderType } from "./localProvider";

type RightInspectorProps = {
  uiPreferences: UiPreferences;
  latestTaskContract?: TaskContractView;
  agentRuns: AgentRunView[];
  agentSteps: AgentStepView[];
  agentDeliverables: AgentDeliverableView[];
  reviewResults: ReviewResultView[];
  modelProviders: ModelProviderView[];
  modelInvocationLogs: ModelInvocationLogView[];
  promptTemplates: PromptTemplateView[];
  promptPreview: ModelInvocationReview | null;
  invocationApprovalIntent: ModelInvocationApprovalIntent | null;
  invocationReview: ModelInvocationApprovalReview | null;
  providerCheck: ModelProviderCheckResult | null;
  localModels: LocalModelInfo[];
  selectedLocalModel: string;
  localInvokeResult: LocalModelInvokeResponse | null;
  hybridArchitecture: HybridArchitectureState | null;
  files: UploadedFileView[];
  securityRequests: SecurityRequestView[];
  auditLogs: NetworkAuditLogView[];
  memoryItems: MemoryItemDbView[];
  currentSkill: SkillInfo;
  localProviderEndpoints: string[];
  onAdvanceAgentStep: (runId?: string) => void;
  onPauseAgentRun: (runId: string) => void;
  onResumeAgentRun: (runId: string) => void;
  onCancelAgentRun: (runId: string) => void;
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
  onLocalInvoke: (userApproved?: boolean, approvalId?: string) => void;
  onSecurityRequest: () => void;
  onSaveSuggestion: (suggestionId: string, scope: "project" | "global") => void;
};

const tabs: Array<{ id: InspectorTab; label: string; icon: typeof FileText }> = [
  { id: "task", label: "Task", icon: FileText },
  { id: "pipeline", label: "Pipeline", icon: Route },
  { id: "models", label: "Models", icon: Bot },
  { id: "safety", label: "Safety", icon: ShieldAlert },
  { id: "artifacts", label: "Artifacts", icon: Archive }
];

export function RightInspector(props: RightInspectorProps) {
  const [activeTab, setActiveTab] = useState<InspectorTab>("task");
  const [collapsed, setCollapsed] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(props.uiPreferences.showDebugInformation);

  useEffect(() => {
    setAdvancedOpen(props.uiPreferences.showDebugInformation);
  }, [props.uiPreferences.showDebugInformation]);

  if (collapsed) {
    return (
      <aside className="right-inspector collapsed" aria-label="Inspector collapsed">
        <button type="button" className="inspector-collapse" onClick={() => setCollapsed(false)} title="Open Inspector">
          <PanelRightOpen size={18} />
        </button>
      </aside>
    );
  }

  const primaryProvider = getPrimaryLocalProvider(props.modelProviders);
  const localProvider = primaryProvider?.enabled && primaryProvider.status === "active" ? primaryProvider : undefined;
  const runStatus = toUserStatus(props.agentRuns[0]?.status || "Ready");
  const skillName = friendlySkill(props.latestTaskContract?.selected_skill || props.currentSkill.name);

  return (
    <aside className="right-inspector" aria-label="Runtime summary">
      <div className="inspector-topline">
        <strong>Runtime Summary</strong>
        <button type="button" className="icon-button" onClick={() => setCollapsed(true)} title="Collapse Inspector">
          <PanelRightClose size={16} />
        </button>
      </div>
      <div className="inspector-body">
        <div className="inspector-stack">
          <SummaryMetrics
            items={[
              ["Model", props.selectedLocalModel || props.localModels.find((model) => model.name === "qwen2.5:7b")?.name || "qwen2.5:7b"],
              ["Provider", localProvider?.name || "Local Ollama"],
              ["Status", runStatus]
            ]}
          />
          <PanelCard title="Current runtime" eyebrow="Simple summary">
            <div className="runtime-summary-list">
              <RuntimeLine label="Skill" value={skillName} />
              <RuntimeLine label="Privacy" value={props.latestTaskContract?.privacy_level || "P1 Local"} />
              <RuntimeLine label="External Call" value="Disabled" />
              <RuntimeLine label="Desktop Execution" value="Disabled" />
              <RuntimeLine label="Risk" value={toUserRisk(props.latestTaskContract?.risk_level || "normal")} />
            </div>
          </PanelCard>
          <PanelCard title="Review Summary" eyebrow="Quality check">
            {props.reviewResults[0] ? (
              <div className="compact-item">
                <strong>{props.reviewResults[0].approved ? "Completion: passed" : "Completion: needs work"}</strong>
                <small>{props.reviewResults[0].recommendations[0] || "Review output before final use."}</small>
              </div>
            ) : (
              <EmptyState title="No review yet" description="Review appears after the run produces output." />
            )}
          </PanelCard>
          <details className="advanced-details" open={advancedOpen} onToggle={(event) => setAdvancedOpen(event.currentTarget.open)}>
            <summary>Advanced Inspector</summary>
            <div className="inspector-tabs">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button key={tab.id} className={activeTab === tab.id ? "active" : ""} type="button" onClick={() => setActiveTab(tab.id)}>
                    <Icon size={15} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
            <div className="advanced-tab-body">
              {activeTab === "task" && <TaskTab {...props} />}
              {activeTab === "pipeline" && <PipelineTab {...props} />}
              {activeTab === "models" && <ModelsTab {...props} />}
              {activeTab === "safety" && <SafetyTab {...props} />}
              {activeTab === "artifacts" && <ArtifactsTab {...props} />}
            </div>
          </details>
        </div>
      </div>
    </aside>
  );
}

function TaskTab({ latestTaskContract, currentSkill, reviewResults }: RightInspectorProps) {
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Status", toUserStatus(latestTaskContract?.status || "waiting")], ["Risk", toUserRisk(latestTaskContract?.risk_level || "normal")], ["Skill", friendlySkill(currentSkill.name)]]} />
      <PanelCard title="Task Contract" eyebrow="Raw task fields">
        {latestTaskContract ? (
          <div className="compact-item">
            <strong>{latestTaskContract.title}</strong>
            <small>{latestTaskContract.objective}</small>
            <details><summary>Raw metadata</summary><pre className="redacted-preview">{JSON.stringify(latestTaskContract.metadata, null, 2)}</pre></details>
          </div>
        ) : <EmptyState title="No Task Contract" />}
      </PanelCard>
      <details className="folded-section"><summary>Review records</summary><div className="compact-list">{reviewResults.slice(0, 3).map((review) => <div className="compact-item" key={review.id}><strong>{review.reviewer}</strong><small>{review.severity}</small></div>)}</div></details>
    </div>
  );
}

function PipelineTab(props: RightInspectorProps) {
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Run", toUserStatus(props.agentRuns[0]?.status || "none")], ["Steps", String(props.agentSteps.length)], ["Output", toUserStatus(props.agentDeliverables[0]?.status || "none")]]} />
      <PanelCard title="Agent run detail" eyebrow="Developer controls">
        <AgentRunTimeline agentRuns={props.agentRuns} agentSteps={props.agentSteps.slice(0, 5)} deliverables={props.agentDeliverables.slice(0, 2)} onAdvanceAgentStep={props.onAdvanceAgentStep} onPauseAgentRun={props.onPauseAgentRun} onResumeAgentRun={props.onResumeAgentRun} onCancelAgentRun={props.onCancelAgentRun} showProviderIds={props.uiPreferences.showProviderIds} />
      </PanelCard>
      <details className="folded-section"><summary>Raw pipeline steps</summary><div className="compact-list">{(props.latestTaskContract?.pipeline_steps ?? []).map((step, index) => <small key={`pipeline-${index}`}>{metadataText(step.step_name, `Step ${index + 1}`)}</small>)}</div></details>
    </div>
  );
}

function ModelsTab(props: RightInspectorProps) {
  const activeProvider = getPrimaryLocalProvider(props.modelProviders) || props.modelProviders.find((provider) => provider.enabled && provider.status === "active");
  const totalCost = props.modelInvocationLogs.reduce((sum, log) => sum + log.estimated_cost, 0);
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Provider", activeProvider?.name || "none"], ["Models", String(props.localModels.length)], ["Cost", formatCost(totalCost)]]} />
      <PanelCard title="Model details" eyebrow="Model Gateway">
        <div className="compact-list">
          {props.modelProviders.slice(0, 5).map((provider) => <div className="compact-item" key={provider.id}><strong>{provider.name}</strong><StatusBadge kind={isLocalProviderType(provider.provider_type) && provider.enabled && provider.status === "active" ? "REAL_LOCAL" : provider.provider_type === "mock" ? "MOCK_ONLY" : "RESERVED_DISABLED"} label={`${provider.provider_type} / ${provider.status}`} /></div>)}
        </div>
      </PanelCard>
      <details className="folded-section"><summary>Invocation logs</summary><div className="compact-list">{props.modelInvocationLogs.slice(0, 8).map((log) => <div className="compact-item" key={log.id}><strong>{log.mode}</strong><small>hash {shortHash(log.prompt_hash)} / cost {formatCost(log.estimated_cost)} / {formatTime(log.created_at)}</small></div>)}</div></details>
    </div>
  );
}

function SafetyTab(props: RightInspectorProps) {
  const approvalStatus = props.invocationApprovalIntent?.status || (props.invocationReview?.requires_user_approval ? "required" : "none");
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Privacy", props.latestTaskContract?.privacy_level || "local_only"], ["External", "disabled"], ["Approval", approvalStatus]]} />
      <PanelCard title="Security Boundary" eyebrow="Local policy" actions={<button type="button" onClick={props.onSecurityRequest}>Security request mock</button>}>
        <div className="boundary-grid compact-boundary">
          <Boundary label="External API" kind="NO_EXTERNAL_CALL" value="Disabled" />
          <Boundary label="Web Search" kind="NO_EXTERNAL_CALL" value="Disabled" />
          <Boundary label="MCP" kind="RESERVED_DISABLED" value="Disabled" />
          <Boundary label="Desktop Execution" kind="NO_DESKTOP_EXECUTION" value="Disabled" />
        </div>
      </PanelCard>
      <details className="folded-section"><summary>Audit logs</summary><div className="compact-list">{props.securityRequests.slice(0, 5).map((request) => <div className="compact-item" key={request.id}><strong>{request.action}</strong><small>{request.status} / {formatTime(request.created_at)}</small></div>)}{props.auditLogs.slice(0, 5).map((log) => <div className="compact-item" key={log.id}><strong>{log.action}</strong><small>{log.allowed ? "allowed" : "denied"} / {log.mode}</small></div>)}</div></details>
    </div>
  );
}

function ArtifactsTab(props: RightInspectorProps) {
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Artifacts", String((props.hybridArchitecture?.artifact_center ?? []).length + props.agentDeliverables.length)], ["Files", String(props.files.length)], ["Reviews", String(props.reviewResults.length)]]} />
      <ArtifactPreview artifacts={(props.hybridArchitecture?.artifact_center ?? []).slice(0, 3)} latestDeliverable={props.agentDeliverables[0]} latestReview={props.reviewResults[0]} />
      <details className="folded-section"><summary>Artifact history and quarantined files</summary><div className="compact-list">{props.files.slice(0, 8).map((file) => <div className="compact-item" key={file.id}><strong>{file.original_filename}</strong><small>{file.status} / sha256 {shortHash(file.sha256)}</small></div>)}</div></details>
    </div>
  );
}

function SummaryMetrics({ items }: { items: Array<[string, string]> }) {
  return <div className="summary-metrics">{items.map(([label, value]) => <div className="summary-metric" key={`${label}-${value}`}><span>{label}</span><strong title={value}>{value}</strong></div>)}</div>;
}

function RuntimeLine({ label, value }: { label: string; value: string }) {
  return <div className="runtime-line"><span>{label}</span><strong>{value}</strong></div>;
}

function Boundary({ label, value, kind }: { label: string; value: string; kind: "REAL_LOCAL" | "NO_EXTERNAL_CALL" | "RESERVED_DISABLED" | "NO_DESKTOP_EXECUTION" }) {
  return <div className="boundary-item"><strong>{label}</strong><small>{value}</small><StatusBadge kind={kind} /></div>;
}

function toUserStatus(status: string) {
  const map: Record<string, string> = {
    blocked: "Needs confirmation",
    draft: "Ready",
    running: "Running",
    paused: "Waiting to continue",
    completed: "Completed",
    failed: "Needs attention",
    fallback_generated: "Generated by local fallback",
    local_model_generated: "Generated by local model"
  };
  return map[status] || status;
}

function toUserRisk(risk: string) {
  const value = risk.toLowerCase();
  if (value.includes("high") || value.includes("critical") || value.includes("p4")) return "Needs Confirmation";
  if (value.includes("medium") || value.includes("p3")) return "Needs Attention";
  return "Normal / Low";
}

function friendlySkill(value: string) {
  const map: Record<string, string> = {
    "skill-coding": "Code",
    "skill-writing": "Writing",
    "skill-research-summary": "Research",
    "skill-document-helper": "Document",
    "skill-review": "Review",
    "skill-planning": "Planning",
    "requirement_analysis": "Planning"
  };
  return map[value] || value;
}