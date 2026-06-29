import type { AgentDeliverableView, AgentRunView, AgentStepView } from "../types";
import { formatCost, formatTime, metadataBool, metadataList, metadataText, normalizeRisk } from "./format";
import { EmptyState } from "./EmptyState";
import { StatusBadge } from "./StatusBadge";

type AgentRunTimelineProps = {
  agentRuns: AgentRunView[];
  agentSteps: AgentStepView[];
  deliverables: AgentDeliverableView[];
  onAdvanceAgentStep?: (runId?: string) => void;
  onPauseAgentRun?: (runId: string) => void;
  onResumeAgentRun?: (runId: string) => void;
  onCancelAgentRun?: (runId: string) => void;
};

export function AgentRunTimeline({
  agentRuns,
  agentSteps,
  deliverables,
  onAdvanceAgentStep,
  onPauseAgentRun,
  onResumeAgentRun,
  onCancelAgentRun
}: AgentRunTimelineProps) {
  const currentRun = agentRuns[0];

  if (!currentRun && agentSteps.length === 0) {
    return <EmptyState title="暂无 Agent Run" description="启动 Agent Run 后，Planner / Writer / Code Agent / Review Agent 步骤会显示在这里。" />;
  }

  return (
    <div className="timeline-stack">
      {currentRun && (
        <div className="run-summary">
          <div>
            <strong>Run {currentRun.id.slice(0, 8)}</strong>
            <small>
              Step {currentRun.current_step_index} / {currentRun.status} / {formatTime(currentRun.updated_at)}
            </small>
          </div>
          <div className="mini-actions">
            {onAdvanceAgentStep && (
              <button type="button" onClick={() => onAdvanceAgentStep(currentRun.id)}>
                Advance Step
              </button>
            )}
            {onPauseAgentRun && (
              <button type="button" onClick={() => onPauseAgentRun(currentRun.id)}>
                Pause
              </button>
            )}
            {onResumeAgentRun && (
              <button type="button" onClick={() => onResumeAgentRun(currentRun.id)}>
                Resume
              </button>
            )}
            {onCancelAgentRun && (
              <button type="button" className="danger-button" onClick={() => onCancelAgentRun(currentRun.id)}>
                Stop
              </button>
            )}
          </div>
        </div>
      )}

      <div className="timeline">
        {agentSteps.map((step) => {
          const metadata = step.execution_metadata ?? {};
          const usedLocalModel = metadataBool(metadata.used_local_model);
          return (
            <article className="timeline-item" key={step.id}>
              <div className="timeline-marker" />
              <div className="timeline-content">
                <div className="row-between">
                  <strong>
                    {step.step_index}. {step.step_name || step.agent_name}
                  </strong>
                  <StatusBadge kind={step.status === "completed" ? "COMPLETED" : step.status === "failed" ? "FAILED" : "RUNNING"} label={step.status} />
                </div>
                <small>
                  {step.agent_name} / {step.model_role || "model_role"} / {step.step_type || "step"}
                </small>
                <small>Risk: <StatusBadge kind={normalizeRisk(step.risk_level)} label={step.risk_level} /></small>
                <small>Provider: {metadataText(metadata.model_provider_id, step.selected_provider_id || "None")}</small>
                <small>Model: {metadataText(metadata.model_name, step.selected_model_id || "None")}</small>
                <small>Local model: {usedLocalModel ? "Yes" : "No"} / Skills: {metadataList(metadata.injected_skill_ids)}</small>
                <small>
                  Tokens/cost: {step.input_tokens} in / {step.output_tokens} out / {formatCost(step.estimated_cost)}
                </small>
                {step.error_message && <small className="danger-text">{step.error_message}</small>}
              </div>
            </article>
          );
        })}
      </div>

      {deliverables.slice(0, 4).map((deliverable) => (
        <div className="compact-item" key={deliverable.id}>
          <strong>{deliverable.agent_name}</strong>
          <small>{deliverable.status} / {formatTime(deliverable.created_at)}</small>
          <small>{deliverable.summary}</small>
        </div>
      ))}
    </div>
  );
}
