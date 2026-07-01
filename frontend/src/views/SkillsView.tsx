import { EmptyState } from "../components/EmptyState";
import { metadataBool, metadataText } from "../components/format";
import { PanelCard } from "../components/PanelCard";
import { StatusBadge } from "../components/StatusBadge";
import type { SkillDbView } from "../types";
import type { WorkspaceViewProps } from "./viewTypes";

const friendlySkillNames: Record<string, string> = {
  "skill-coding": "Coding",
  "skill-writing": "Writing",
  "skill-research-summary": "Research Summary",
  "skill-document-helper": "Document Helper",
  "skill-review": "Review",
  "skill-planning": "Planning",
  "skill-requirement-analysis": "Planning"
};

export function SkillsView(props: WorkspaceViewProps) {
  const visibleSkills = friendlySkills(props.skills);
  return (
    <>
      <ViewHeader title="Skills" subtitle="User-facing skills for local tasks. Developer pipeline metadata is available in Advanced Details." />
      <div className="view-scroll">
        <PanelCard title="Available Skills" eyebrow="Simple skill list" actions={<button type="button" onClick={props.onCreateSkill}>New Skill</button>}>
          <div className="card-grid">
            {visibleSkills.map((skill) => (
              <div className="compact-item" key={skill.id}>
                <div className="row-between">
                  <strong>{friendlySkillNames[skill.id] || skill.name}</strong>
                  <StatusBadge kind={skill.enabled ? "COMPLETED" : "RESERVED_DISABLED"} label={skill.enabled ? "enabled" : "disabled"} />
                </div>
                <small>{simpleSkillDescription(skill)}</small>
                {skill.safety_warnings.length > 0 && <small className="warning-text">{skill.safety_warnings.join(" / ")}</small>}
                <div className="mini-actions">
                  <button type="button" onClick={() => props.onEnableSkill(skill.id)}>Enable</button>
                  <button type="button" onClick={() => props.onDisableSkill(skill.id)}>Disable</button>
                  <button type="button" onClick={() => props.onCheckSkill(skill)}>Check Conflict</button>
                </div>
              </div>
            ))}
            {visibleSkills.length === 0 && <EmptyState title="No user-facing skills" description="Seed skills are created when the backend initializes SQLite." />}
          </div>
          {props.skillConflictNote && <p className="notice-line">{props.skillConflictNote}</p>}
        </PanelCard>

        <details className="advanced-details">
          <summary>Advanced Skill Packages and Pipelines</summary>
          <PanelCard title="Skill package structure" eyebrow="SKILL.md / manifest.yaml / static / references">
            <div className="card-grid">
              {(props.hybridArchitecture?.skill_packages ?? []).map((skillPackage, index) => (
                <div className="compact-item" key={`skill-package-${metadataText(skillPackage.package_id, String(index))}`}>
                  <strong>{metadataText(skillPackage.name, "Skill Package")}</strong>
                  <small>{metadataText(skillPackage.path, "skills/package")}</small>
                  <small>
                    SKILL.md {metadataBool(skillPackage.skill_md_found) ? "yes" : "no"} / manifest {metadataBool(skillPackage.manifest_found) ? "yes" : "no"} / static {metadataBool(skillPackage.static_found) ? "yes" : "no"} / references {metadataBool(skillPackage.references_found) ? "yes" : "no"}
                  </small>
                </div>
              ))}
              {(props.hybridArchitecture?.skill_packages ?? []).length === 0 && <EmptyState title="No skill package metadata" />}
            </div>
          </PanelCard>
          <PanelCard title="Pipeline metadata" eyebrow="Developer view">
            <div className="card-grid">
              {(props.hybridArchitecture?.skill_pipelines ?? []).map((pipeline, index) => (
                <div className="compact-item" key={`pipeline-${metadataText(pipeline.pipeline_id, String(index))}`}>
                  <strong>{metadataText(pipeline.name, "Skill Pipeline")}</strong>
                  <small>{metadataText(pipeline.skill_id, "skill")} / {metadataText(pipeline.status, "mock_only")}</small>
                  <small>{metadataText(pipeline.description, "Pipeline metadata only.")}</small>
                </div>
              ))}
              {(props.hybridArchitecture?.skill_pipelines ?? []).length === 0 && <EmptyState title="No pipeline metadata" />}
            </div>
          </PanelCard>
        </details>
      </div>
    </>
  );
}

function friendlySkills(skills: SkillDbView[]) {
  const wanted = new Set(["skill-coding", "skill-writing", "skill-research-summary", "skill-document-helper", "skill-review", "skill-planning", "skill-requirement-analysis"]);
  return skills.filter((skill) => wanted.has(skill.id)).sort((a, b) => (friendlySkillNames[a.id] || a.name).localeCompare(friendlySkillNames[b.id] || b.name));
}

function simpleSkillDescription(skill: SkillDbView) {
  if (skill.id === "skill-coding") return "Generate code plans, code snippets, and test ideas.";
  if (skill.id === "skill-writing") return "Draft structured writing content.";
  if (skill.id === "skill-research-summary") return "Summarize user-provided research context without web search.";
  if (skill.id === "skill-document-helper") return "Prepare document outlines and formatting plans without parsing uploads.";
  if (skill.id === "skill-review") return "Check completeness, privacy, risk, and next steps.";
  if (skill.id === "skill-planning" || skill.id === "skill-requirement-analysis") return "Understand the request and plan safe local steps.";
  return skill.description;
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