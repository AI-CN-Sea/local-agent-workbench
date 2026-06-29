import type { AgentDeliverableView, ReviewResultView } from "../types";
import { formatTime, metadataText } from "./format";
import { EmptyState } from "./EmptyState";
import { PanelCard } from "./PanelCard";
import { StatusBadge } from "./StatusBadge";

type ArtifactPreviewProps = {
  artifacts: Array<Record<string, unknown>>;
  latestDeliverable?: AgentDeliverableView;
  latestReview?: ReviewResultView;
  compact?: boolean;
};

export function ArtifactPreview({ artifacts, latestDeliverable, latestReview, compact = false }: ArtifactPreviewProps) {
  return (
    <PanelCard title="Artifact Preview" eyebrow="Artifact Center" compact={compact}>
      {!latestDeliverable && artifacts.length === 0 ? (
        <EmptyState title="暂无 Artifact" description="Agent Run 完成后会在这里显示交付物元数据，不自动打开上传文件。" />
      ) : (
        <div className="artifact-preview">
          {latestDeliverable && (
            <article className="artifact-primary">
              <div className="row-between">
                <strong>{latestDeliverable.agent_name}</strong>
                <StatusBadge kind={latestDeliverable.status === "completed" ? "COMPLETED" : "MOCK_ONLY"} label={latestDeliverable.status} />
              </div>
              <p>{latestDeliverable.summary}</p>
              <small>{formatTime(latestDeliverable.created_at)}</small>
            </article>
          )}
          {latestReview && (
            <article className="artifact-review">
              <div className="row-between">
                <strong>{latestReview.reviewer}</strong>
                <StatusBadge kind={latestReview.approved ? "COMPLETED" : "REQUIRES_APPROVAL"} label={latestReview.severity} />
              </div>
              <small>{latestReview.findings.slice(0, 2).join(" / ") || "No findings"}</small>
            </article>
          )}
          <div className="compact-list">
            {artifacts.slice(0, compact ? 3 : 8).map((artifact, index) => (
              <div className="compact-item" key={`artifact-preview-${metadataText(artifact.artifact_id, String(index))}`}>
                <strong>{metadataText(artifact.title, "Artifact")}</strong>
                <small>
                  {metadataText(artifact.artifact_type, "artifact")} / {metadataText(artifact.status, "mock_only")}
                </small>
                <small>{metadataText(artifact.summary, "No preview available.")}</small>
              </div>
            ))}
          </div>
        </div>
      )}
    </PanelCard>
  );
}
