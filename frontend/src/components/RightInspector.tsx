import { Archive, Bot, FileText, PanelRightClose, PanelRightOpen, Route, ShieldAlert } from "lucide-react";
import { useState } from "react";

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
import type { InspectorTab } from "./componentTypes";
import { AgentRunTimeline } from "./AgentRunTimeline";
import { ArtifactPreview } from "./ArtifactPreview";
import { EmptyState } from "./EmptyState";
import { formatCost, formatTime, metadataNumber, metadataText, normalizeRisk, shortHash } from "./format";
import { PanelCard } from "./PanelCard";
import { StatusBadge } from "./StatusBadge";

type RightInspectorProps = {
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

  if (collapsed) {
    return (
      <aside className="right-inspector collapsed" aria-label="Inspector collapsed">
        <button type="button" className="inspector-collapse" onClick={() => setCollapsed(false)} title="展开 Inspector">
          <PanelRightOpen size={18} />
        </button>
      </aside>
    );
  }

  return (
    <aside className="right-inspector" aria-label="Inspector">
      <div className="inspector-topline">
        <strong>Inspector</strong>
        <button type="button" className="icon-button" onClick={() => setCollapsed(true)} title="折叠 Inspector">
          <PanelRightClose size={16} />
        </button>
      </div>
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
      <div className="inspector-body">
        {activeTab === "task" && <TaskTab {...props} />}
        {activeTab === "pipeline" && <PipelineTab {...props} />}
        {activeTab === "models" && <ModelsTab {...props} />}
        {activeTab === "safety" && <SafetyTab {...props} />}
        {activeTab === "artifacts" && <ArtifactsTab {...props} />}
      </div>
    </aside>
  );
}

function TaskTab({ latestTaskContract, currentSkill, reviewResults }: RightInspectorProps) {
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Status", latestTaskContract?.status || "waiting"], ["Risk", latestTaskContract?.risk_level || "normal"], ["Skill", currentSkill.name]]} />
      <PanelCard title="Task 摘要" eyebrow="Current">
        {latestTaskContract ? (
          <div className="compact-item">
            <strong>{latestTaskContract.title}</strong>
            <small>{latestTaskContract.objective}</small>
            <details>
              <summary>任务协议详情</summary>
              <ul>
                {latestTaskContract.inputs.slice(0, 5).map((item) => <li key={`input-${item}`}>Input: {item}</li>)}
                {latestTaskContract.outputs.slice(0, 5).map((item) => <li key={`output-${item}`}>Output: {item}</li>)}
                {latestTaskContract.acceptance_criteria.slice(0, 5).map((item) => <li key={`criteria-${item}`}>Accept: {item}</li>)}
              </ul>
            </details>
          </div>
        ) : (
          <EmptyState title="暂无 Task Contract" description="发送需求或确认需求卡片后会生成任务协议。" />
        )}
      </PanelCard>
      <details className="folded-section">
        <summary>Skill 与审核结果</summary>
        <div className="compact-list">
          <div className="compact-item"><strong>{currentSkill.name}</strong><small>{currentSkill.description}</small></div>
          {reviewResults.slice(0, 3).map((review) => <div className="compact-item" key={review.id}><strong>{review.reviewer}</strong><small>{review.severity}</small></div>)}
        </div>
      </details>
    </div>
  );
}

function PipelineTab(props: RightInspectorProps) {
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Run", props.agentRuns[0]?.status || "none"], ["Steps", String(props.agentSteps.length)], ["Output", props.agentDeliverables[0]?.status || "none"]]} />
      <PanelCard title="Pipeline 进度" eyebrow="Agent Run">
        <AgentRunTimeline agentRuns={props.agentRuns} agentSteps={props.agentSteps.slice(0, 3)} deliverables={props.agentDeliverables.slice(0, 1)} onAdvanceAgentStep={props.onAdvanceAgentStep} onPauseAgentRun={props.onPauseAgentRun} onResumeAgentRun={props.onResumeAgentRun} onCancelAgentRun={props.onCancelAgentRun} />
      </PanelCard>
      <details className="folded-section"><summary>全部 Pipeline Steps</summary><div className="compact-list">{(props.latestTaskContract?.pipeline_steps ?? []).map((step, index) => <small key={`pipeline-${index}`}>{metadataText(step.step_name, `Step ${index + 1}`)}</small>)}</div></details>
    </div>
  );
}

function ModelsTab(props: RightInspectorProps) {
  const activeProvider = props.modelProviders.find((provider) => provider.enabled && provider.status === "active");
  const recommended = props.latestTaskContract?.recommended_models?.[0];
  const totalCost = props.modelInvocationLogs.reduce((sum, log) => sum + log.estimated_cost, 0);
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Provider", activeProvider?.name || "none"], ["Models", String(props.localModels.length)], ["Cost", formatCost(totalCost)]]} />
      <PanelCard title="模型服务" eyebrow="本地模型网关">
        <div className="compact-list">
          <div className="compact-item"><strong>{metadataText(recommended?.recommended_model, "暂无推荐模型")}</strong><small>{metadataText(recommended?.recommended_provider_type, "mock/local gated")}</small></div>
          {props.modelProviders.slice(0, 3).map((provider) => <div className="compact-item" key={provider.id}><strong>{provider.name}</strong><StatusBadge kind={provider.enabled && provider.status === "active" ? "REAL_LOCAL" : provider.provider_type === "mock" ? "MOCK_ONLY" : "RESERVED_DISABLED"} label={`${provider.provider_type} / ${provider.status}`} /></div>)}
        </div>
      </PanelCard>
      <details className="folded-section"><summary>调用记录与评估日志</summary><div className="compact-list">{props.modelInvocationLogs.slice(0, 8).map((log) => <div className="compact-item" key={log.id}><strong>{log.mode}</strong><small>hash {shortHash(log.prompt_hash)} / cost {formatCost(log.estimated_cost)} / {formatTime(log.created_at)}</small></div>)}{props.modelInvocationLogs.length === 0 && <EmptyState title="暂无调用记录" />}</div></details>
    </div>
  );
}

function SafetyTab(props: RightInspectorProps) {
  const approvalStatus = props.invocationApprovalIntent?.status || (props.invocationReview?.requires_user_approval ? "required" : "none");
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Privacy", props.latestTaskContract?.privacy_level || "local_only"], ["External", "disabled"], ["Approval", approvalStatus]]} />
      <PanelCard title="安全边界" eyebrow="Security" actions={<button type="button" onClick={props.onSecurityRequest}>安全请求 mock</button>}>
        <div className="boundary-grid compact-boundary">
          <Boundary label="外部 API" kind="NO_EXTERNAL_CALL" value="关闭" />
          <Boundary label="网页搜索" kind="NO_EXTERNAL_CALL" value="关闭" />
          <Boundary label="MCP" kind="RESERVED_DISABLED" value="关闭" />
          <Boundary label="桌面执行" kind="NO_DESKTOP_EXECUTION" value="关闭" />
        </div>
      </PanelCard>
      <details className="folded-section"><summary>审计日志与审批详情</summary><div className="compact-list">{props.securityRequests.slice(0, 5).map((request) => <div className="compact-item" key={request.id}><strong>{request.action}</strong><small>{request.status} / {formatTime(request.created_at)}</small></div>)}{props.auditLogs.slice(0, 5).map((log) => <div className="compact-item" key={log.id}><strong>{log.action}</strong><small>{log.allowed ? "allowed" : "denied"} / {log.mode}</small></div>)}</div></details>
    </div>
  );
}

function ArtifactsTab(props: RightInspectorProps) {
  return (
    <div className="inspector-stack">
      <SummaryMetrics items={[["Artifacts", String((props.hybridArchitecture?.artifact_center ?? []).length + props.agentDeliverables.length)], ["Files", String(props.files.length)], ["Reviews", String(props.reviewResults.length)]]} />
      <ArtifactPreview artifacts={(props.hybridArchitecture?.artifact_center ?? []).slice(0, 3)} latestDeliverable={props.agentDeliverables[0]} latestReview={props.reviewResults[0]} />
      <details className="folded-section"><summary>历史 Artifact 与隔离文件</summary><div className="compact-list">{props.files.slice(0, 8).map((file) => <div className="compact-item" key={file.id}><strong>{file.original_filename}</strong><small>{file.status} / sha256 {shortHash(file.sha256)}</small></div>)}{props.files.length === 0 && <EmptyState title="暂无隔离文件" />}</div></details>
    </div>
  );
}

function SummaryMetrics({ items }: { items: Array<[string, string]> }) {
  return <div className="summary-metrics">{items.map(([label, value]) => <div className="summary-metric" key={`${label}-${value}`}><span>{label}</span><strong title={value}>{value}</strong></div>)}</div>;
}

function Boundary({ label, value, kind }: { label: string; value: string; kind: "REAL_LOCAL" | "NO_EXTERNAL_CALL" | "RESERVED_DISABLED" | "NO_DESKTOP_EXECUTION" }) {
  return <div className="boundary-item"><strong>{label}</strong><small>{value}</small><StatusBadge kind={kind} /></div>;
}
