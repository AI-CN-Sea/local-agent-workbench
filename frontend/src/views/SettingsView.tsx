import { PanelCard } from "../components/PanelCard";
import { StatusBadge } from "../components/StatusBadge";
import type { UiPreferences } from "../components/componentTypes";
import type { StatusBadgeKind } from "../components/componentTypes";
import type { WorkspaceViewProps } from "./viewTypes";

export function SettingsView(props: WorkspaceViewProps) {
  return (
    <>
      <ViewHeader title="Settings" subtitle="Choose the simple user view or open developer details when needed." />
      <div className="view-scroll">
        <PanelCard title="User Mode" eyebrow="Simple by default">
          <div className="settings-grid">
            <ToggleItem label="Simple Mode" checked={props.uiPreferences.simpleMode} onChange={(value) => props.onUiPreferenceChange("simpleMode", value)} />
            <ToggleItem label="Show Debug Information" checked={props.uiPreferences.showDebugInformation} onChange={(value) => props.onUiPreferenceChange("showDebugInformation", value)} />
            <ToggleItem label="Show Raw TaskContract" checked={props.uiPreferences.showRawTaskContract} onChange={(value) => props.onUiPreferenceChange("showRawTaskContract", value)} />
            <ToggleItem label="Show Pipeline Steps" checked={props.uiPreferences.showPipelineSteps} onChange={(value) => props.onUiPreferenceChange("showPipelineSteps", value)} />
            <ToggleItem label="Show Mock Artifacts" checked={props.uiPreferences.showMockArtifacts} onChange={(value) => props.onUiPreferenceChange("showMockArtifacts", value)} />
            <ToggleItem label="Show Provider IDs" checked={props.uiPreferences.showProviderIds} onChange={(value) => props.onUiPreferenceChange("showProviderIds", value)} />
            <ToggleItem label="Auto-run low-risk local tasks" checked={props.uiPreferences.autoRunLowRiskLocalTasks} onChange={(value) => props.onUiPreferenceChange("autoRunLowRiskLocalTasks", value)} />
          </div>
        </PanelCard>

        <PanelCard title="Local Runtime" eyebrow="Ollama whitelist">
          <div className="settings-grid">
            <SettingItem title="Endpoint allowlist" value={props.localProviderEndpoints.join(" / ")} badge="REAL_LOCAL" />
            <SettingItem title="Default model" value="qwen2.5:7b / ollama" badge="REAL_LOCAL" />
            <SettingItem title="Invocation policy" value="Only active local provider after Model Gateway review" badge="REAL_LOCAL" />
          </div>
        </PanelCard>

        <PanelCard title="Disabled Capabilities" eyebrow="Security boundary">
          <div className="settings-grid">
            <SettingItem title="External API" value="Disabled" badge="NO_EXTERNAL_CALL" />
            <SettingItem title="Web Search" value="Disabled" badge="NO_EXTERNAL_CALL" />
            <SettingItem title="MCP" value="Disabled" badge="RESERVED_DISABLED" />
            <SettingItem title="Desktop Tool" value="Disabled" badge="NO_DESKTOP_EXECUTION" />
            <SettingItem title="Uploads" value="Quarantine only; not parsed or sent to Agent" badge="REQUIRES_APPROVAL" />
          </div>
        </PanelCard>

        <PanelCard title="System" eyebrow="Local state">
          <div className="settings-grid">
            <SettingItem title="Backend status" value={props.state.database.status} badge="COMPLETED" />
            <SettingItem title="SQLite" value={props.state.database.path} badge="COMPLETED" />
            <SettingItem title="Advanced Mode" value="Available through Workbench details and Inspector" badge="MOCK_ONLY" />
          </div>
        </PanelCard>
      </div>
    </>
  );
}

function ToggleItem({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="setting-item toggle-item">
      <strong>{label}</strong>
      <small>{checked ? "Enabled" : "Disabled"}</small>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
    </label>
  );
}

function SettingItem({ title, value, badge }: { title: string; value: string; badge: StatusBadgeKind }) {
  return (
    <div className="setting-item">
      <strong>{title}</strong>
      <small>{value}</small>
      <StatusBadge kind={badge} />
    </div>
  );
}

function ViewHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <header className="task-header single-column-header">
      <div>
        <span className="panel-eyebrow">Active View</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
    </header>
  );
}