import { ArtifactsView } from "../views/ArtifactsView";
import { PrivacyView } from "../views/PrivacyView";
import { ProvidersView } from "../views/ProvidersView";
import { SettingsView } from "../views/SettingsView";
import { SkillsView } from "../views/SkillsView";
import { WorkbenchView } from "../views/WorkbenchView";
import type { WorkspaceViewProps } from "../views/viewTypes";

export function MainWorkspace(props: WorkspaceViewProps) {
  return (
    <main className="main-workspace" aria-label="Main workspace">
      {props.activeView === "workbench" && <WorkbenchView {...props} />}
      {props.activeView === "skills" && <SkillsView {...props} />}
      {props.activeView === "providers" && <ProvidersView {...props} />}
      {props.activeView === "artifacts" && <ArtifactsView {...props} />}
      {props.activeView === "privacy" && <PrivacyView {...props} />}
      {props.activeView === "settings" && <SettingsView {...props} />}
    </main>
  );
}
