import { ArtifactPreview } from "../components/ArtifactPreview";
import { PanelCard } from "../components/PanelCard";
import { FileIsolationList } from "./WorkbenchView";
import type { WorkspaceViewProps } from "./viewTypes";

export function ArtifactsView(props: WorkspaceViewProps) {
  return (
    <>
      <ViewHeader title="Artifact Center" subtitle="展示 Agent 交付物和 Artifact 元数据；不打开、不解析上传文件。" />
      <div className="view-scroll">
        <ArtifactPreview
          artifacts={props.hybridArchitecture?.artifact_center ?? []}
          latestDeliverable={props.latestDeliverable}
          latestReview={props.latestReview}
        />
        <PanelCard title="Quarantine Files" eyebrow="未解析、未发送给 Agent">
          <FileIsolationList
            files={props.files}
            fileInspectResult={props.fileInspectResult}
            filePreviewResult={props.filePreviewResult}
            onInspectFile={props.onInspectFile}
            onParseFilePreview={props.onParseFilePreview}
          />
        </PanelCard>
      </div>
    </>
  );
}

function ViewHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <header className="task-header">
      <div>
        <span className="panel-eyebrow">Active View</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
    </header>
  );
}
