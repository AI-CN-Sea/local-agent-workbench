import { EmptyState } from "../components/EmptyState";
import { metadataBool, metadataText } from "../components/format";
import { PanelCard } from "../components/PanelCard";
import { StatusBadge } from "../components/StatusBadge";
import type { WorkspaceViewProps } from "./viewTypes";

export function SkillsView(props: WorkspaceViewProps) {
  return (
    <>
      <ViewHeader title="技能包与流程配置" subtitle="查看 Skill 包结构、DB Skill 卡片和 Pipeline 配置；不执行外部工具。" />
      <div className="view-scroll">
        <PanelCard
          title="技能包结构"
          eyebrow="SKILL.md / manifest.yaml / static / references"
          actions={<button type="button" onClick={props.onCreateSkill}>新增 Skill</button>}
        >
          <div className="card-grid">
            {(props.hybridArchitecture?.skill_packages ?? []).map((skillPackage, index) => (
              <div className="compact-item" key={`skill-package-${metadataText(skillPackage.package_id, String(index))}`}>
                <strong>{metadataText(skillPackage.name, "Skill Package")}</strong>
                <small>{metadataText(skillPackage.path, "skills/package")}</small>
                <small>
                  SKILL.md {metadataBool(skillPackage.skill_md_found) ? "yes" : "no"} / manifest{" "}
                  {metadataBool(skillPackage.manifest_found) ? "yes" : "no"} / static{" "}
                  {metadataBool(skillPackage.static_found) ? "yes" : "no"} / references{" "}
                  {metadataBool(skillPackage.references_found) ? "yes" : "no"}
                </small>
                <details>
                  <summary>技术细节</summary>
                  <small>仅扫描结构和元数据，不执行 scripts，不启用 MCP 检索。</small>
                </details>
              </div>
            ))}
            {(props.hybridArchitecture?.skill_packages ?? []).length === 0 && <EmptyState title="暂无 Skill Package 元数据" />}
          </div>
        </PanelCard>

        <PanelCard title="Skill Cards" eyebrow="DB managed">
          <div className="card-grid">
            {props.skills.map((skill) => (
              <div className="compact-item" key={skill.id}>
                <div className="row-between">
                  <strong>{skill.name}</strong>
                  <StatusBadge kind={skill.enabled ? "COMPLETED" : "RESERVED_DISABLED"} label={skill.status} />
                </div>
                <small>{skill.category} / {skill.description}</small>
                {skill.safety_warnings.length > 0 && <small className="warning-text">{skill.safety_warnings.join(" / ")}</small>}
                <div className="mini-actions">
                  <button type="button" onClick={() => props.onEnableSkill(skill.id)}>启用</button>
                  <button type="button" onClick={() => props.onDisableSkill(skill.id)}>禁用</button>
                  <button type="button" onClick={() => props.onCheckSkill(skill)}>检查冲突</button>
                </div>
              </div>
            ))}
            {props.skills.length === 0 && <EmptyState title="暂无 DB Skill" />}
          </div>
          {props.skillConflictNote && <p className="notice-line">{props.skillConflictNote}</p>}
        </PanelCard>

        <PanelCard title="流程配置" eyebrow="Skill Pipeline">
          <div className="card-grid">
            {(props.hybridArchitecture?.skill_pipelines ?? []).map((pipeline, index) => (
              <div className="compact-item" key={`pipeline-${metadataText(pipeline.pipeline_id, String(index))}`}>
                <strong>{metadataText(pipeline.name, "Skill Pipeline")}</strong>
                <small>{metadataText(pipeline.skill_id, "skill")} / {metadataText(pipeline.status, "mock_only")}</small>
                <small>{metadataText(pipeline.description, "Pipeline metadata only.")}</small>
              </div>
            ))}
            {(props.hybridArchitecture?.skill_pipelines ?? []).length === 0 && <EmptyState title="暂无 Pipeline" />}
          </div>
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
