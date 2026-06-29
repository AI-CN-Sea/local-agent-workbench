import { PanelCard } from "../components/PanelCard";
import { StatusBadge } from "../components/StatusBadge";
import type { StatusBadgeKind } from "../components/componentTypes";
import type { WorkspaceViewProps } from "./viewTypes";

export function SettingsView(props: WorkspaceViewProps) {
  return (
    <>
      <ViewHeader title="Settings" subtitle="运行时、安全边界和预留能力配置。所有外部能力默认关闭。" />
      <div className="view-scroll">
        <PanelCard title="Local Runtime" eyebrow="Ollama whitelist">
          <div className="settings-grid">
            <SettingItem title="Endpoint 白名单" value={props.localProviderEndpoints.join(" / ")} badge="REAL_LOCAL" />
            <SettingItem title="Context presets" value="4096 / 8192 / 16384 experimental" badge="REQUIRES_APPROVAL" />
            <SettingItem title="调用策略" value="默认不调用模型；仅在启用 active local provider 并通过审查后调用本机模型。" badge="REAL_LOCAL" />
          </div>
        </PanelCard>
        <PanelCard title="Remote API" eyebrow="Reserved disabled">
          <div className="settings-grid">
            <SettingItem title="API Key" value="不保存、不要求" badge="RESERVED_DISABLED" />
            <SettingItem title="External call" value="关闭" badge="NO_EXTERNAL_CALL" />
            <SettingItem title="remote_api" value="mock only" badge="MOCK_ONLY" />
          </div>
        </PanelCard>
        <PanelCard title="桌面工具预留" eyebrow="Mock only">
          <div className="settings-grid">
            <SettingItem title="desktop_tool" value="mock only" badge="NO_DESKTOP_EXECUTION" />
            <SettingItem title="真实桌面执行" value="关闭" badge="RESERVED_DISABLED" />
            <SettingItem title="Shell / 文件修改" value="不自动执行" badge="REQUIRES_APPROVAL" />
          </div>
        </PanelCard>
        <PanelCard title="Security" eyebrow="Disabled capabilities">
          <div className="settings-grid">
            <SettingItem title="Cookie / OAuth / CLI token" value="关闭" badge="RESERVED_DISABLED" />
            <SettingItem title="MCP" value="关闭" badge="RESERVED_DISABLED" />
            <SettingItem title="Web Search" value="关闭" badge="NO_EXTERNAL_CALL" />
            <SettingItem title="上传文件" value="quarantine，未解析，未发送给 Agent" badge="REQUIRES_APPROVAL" />
          </div>
        </PanelCard>
        <PanelCard title="Build / System" eyebrow="Placeholder">
          <div className="settings-grid">
            <SettingItem title="Frontend version" value="0.1.0 placeholder" badge="MOCK_ONLY" />
            <SettingItem title="Backend status" value={props.state.database.status} badge="COMPLETED" />
            <SettingItem title="SQLite" value={props.state.database.path} badge="COMPLETED" />
          </div>
        </PanelCard>
      </div>
    </>
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
    <header className="task-header">
      <div>
        <span className="panel-eyebrow">Active View</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
    </header>
  );
}
