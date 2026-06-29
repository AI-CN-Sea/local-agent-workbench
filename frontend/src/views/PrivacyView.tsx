import { EmptyState } from "../components/EmptyState";
import { shortHash } from "../components/format";
import { PanelCard } from "../components/PanelCard";
import { StatusBadge } from "../components/StatusBadge";
import type { WorkspaceViewProps } from "./viewTypes";

export function PrivacyView(props: WorkspaceViewProps) {
  return (
    <>
      <ViewHeader title="安全边界" subtitle="本地优先、外部默认关闭、上传文件隔离。" />
      <div className="view-scroll">
        <PanelCard title="隐私与执行规则" eyebrow="Privacy Gateway">
          <div className="boundary-grid">
            <BoundaryItem label="外部 API" kind="NO_EXTERNAL_CALL" value="关闭" />
            <BoundaryItem label="网页搜索" kind="NO_EXTERNAL_CALL" value="关闭" />
            <BoundaryItem label="MCP" kind="RESERVED_DISABLED" value="关闭" />
            <BoundaryItem label="文件解析" kind="RESERVED_DISABLED" value="关闭" />
            <BoundaryItem label="本地模型" kind="REAL_LOCAL" value="仅允许 localhost / 127.0.0.1" />
            <BoundaryItem label="上传文件" kind="REQUIRES_APPROVAL" value="quarantine，未解析，未发送给 Agent" />
          </div>
        </PanelCard>

        <PanelCard title="Prompt 安全预览" eyebrow="脱敏内容">
          {props.promptPreview ? (
            <div className="compact-item">
              <StatusBadge kind={props.promptPreview.blocked ? "BLOCKED" : "LOW_RISK"} label={props.promptPreview.risk_level} />
              <small>prompt hash {shortHash(props.promptPreview.prompt_hash)} / length {props.promptPreview.prompt_length}</small>
              <details open>
                <summary>脱敏 prompt preview</summary>
                <pre className="redacted-preview">{props.promptPreview.redacted_prompt_preview}</pre>
              </details>
            </div>
          ) : (
            <EmptyState title="暂无 Prompt Preview" description="预览时只显示脱敏内容，日志不保存完整 prompt。" />
          )}
          <div className="mini-actions">
            <button type="button" onClick={props.onPreviewPrompt}>生成 Prompt Preview</button>
            <button type="button" onClick={props.onReviewInvocation}>Invocation Review</button>
          </div>
        </PanelCard>

        <PanelCard title="Memory" eyebrow="用户确认后保存">
          <div className="mini-actions">
            <button type="button" onClick={() => props.onSearchMemory("")}>检索 active memory</button>
          </div>
          <div className="card-grid">
            {props.memoryItems.map((memory) => (
              <div className="compact-item" key={memory.id}>
                <strong>{memory.title}</strong>
                <small>{memory.scope} / {memory.status} / {memory.sensitivity}</small>
                <small>{memory.content}</small>
                {memory.safety_warnings.length > 0 && <small className="warning-text">{memory.safety_warnings.join(" / ")}</small>}
                <button type="button" onClick={() => props.onDisableMemory(memory.id)}>禁用</button>
              </div>
            ))}
            {props.memoryItems.length === 0 && <EmptyState title="暂无 Memory" />}
          </div>
        </PanelCard>
      </div>
    </>
  );
}

function BoundaryItem({ label, value, kind }: { label: string; value: string; kind: "REAL_LOCAL" | "NO_EXTERNAL_CALL" | "RESERVED_DISABLED" | "REQUIRES_APPROVAL" }) {
  return (
    <div className="boundary-item">
      <strong>{label}</strong>
      <small>{value}</small>
      <StatusBadge kind={kind} />
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
