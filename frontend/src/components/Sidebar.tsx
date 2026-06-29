import { Archive, Bot, ChevronDown, FolderPlus, MessageSquarePlus, Settings, ShieldAlert, Sparkles } from "lucide-react";

import type { ConversationView, ModelProviderView, ProjectView, SkillDbView, TaskContractView } from "../types";
import type { WorkbenchView } from "./componentTypes";
import { formatTime } from "./format";

type SidebarProps = {
  activeView: WorkbenchView;
  onViewChange: (view: WorkbenchView) => void;
  projects: ProjectView[];
  currentProjectId: string;
  onSelectProject: (projectId: string) => void;
  onCreateProject: () => void;
  conversations: ConversationView[];
  currentConversationId: string;
  onSelectConversation: (conversationId: string) => void;
  taskContracts: TaskContractView[];
  skills: SkillDbView[];
  modelProviders: ModelProviderView[];
  artifactCount: number;
};

const navItems: Array<{ view: WorkbenchView; label: string; icon: typeof Bot; helper: string }> = [
  { view: "workbench", label: "Workbench", icon: MessageSquarePlus, helper: "Chat / Command" },
  { view: "skills", label: "Skills", icon: Sparkles, helper: "Packages" },
  { view: "providers", label: "Providers", icon: Bot, helper: "Ollama / mock" },
  { view: "artifacts", label: "Artifacts", icon: Archive, helper: "Center" },
  { view: "privacy", label: "Privacy", icon: ShieldAlert, helper: "Boundary" },
  { view: "settings", label: "Settings", icon: Settings, helper: "Runtime" }
];

export function Sidebar({
  activeView,
  onViewChange,
  projects,
  currentProjectId,
  onSelectProject,
  onCreateProject,
  conversations,
  currentConversationId,
  onSelectConversation,
  taskContracts,
  skills,
  modelProviders,
  artifactCount
}: SidebarProps) {
  const currentProject = projects.find((project) => project.id === currentProjectId);
  const currentConversation = conversations.find((conversation) => conversation.id === currentConversationId);

  return (
    <aside className="sidebar" aria-label="Workbench navigation">
      <div className="sidebar-brand">
        <Bot size={22} />
        <div>
          <strong>Agent Workbench</strong>
          <span>本地多 Agent 工作台</span>
        </div>
      </div>

      <nav className="view-nav" aria-label="Primary views">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.view}
              className={`view-nav-item ${activeView === item.view ? "active" : ""}`}
              type="button"
              onClick={() => onViewChange(item.view)}
            >
              <Icon size={16} />
              <span>{item.label}</span>
              <small>{item.helper}</small>
            </button>
          );
        })}
      </nav>

      <section className="current-context">
        <div className="sidebar-section-title">
          <strong>Current Context</strong>
          <button type="button" onClick={onCreateProject} title="新建项目">
            <FolderPlus size={15} />
          </button>
        </div>
        <div className="context-card">
          <span>项目</span>
          <strong>{currentProject?.name || "暂无项目"}</strong>
          <span>对话</span>
          <strong>{currentConversation?.title || "暂无对话"}</strong>
        </div>
        <div className="compact-metrics-row">
          <span>T {taskContracts.length}</span>
          <span>S {skills.length}</span>
          <span>P {modelProviders.length}</span>
          <span>A {artifactCount}</span>
        </div>
      </section>

      <details className="sidebar-details">
        <summary><ChevronDown size={14} /> 切换项目</summary>
        <div className="sidebar-list">
          {projects.map((project) => (
            <button
              key={project.id}
              className={`sidebar-list-item ${project.id === currentProjectId ? "active" : ""}`}
              type="button"
              onClick={() => onSelectProject(project.id)}
            >
              <span>{project.name}</span>
              <small>{project.status} / {formatTime(project.created_at)}</small>
            </button>
          ))}
          {projects.length === 0 && <div className="sidebar-empty">暂无项目</div>}
        </div>
      </details>

      <details className="sidebar-details">
        <summary><ChevronDown size={14} /> 切换对话</summary>
        <div className="sidebar-list">
          {conversations.slice(0, 8).map((conversation) => (
            <button
              key={conversation.id}
              className={`sidebar-list-item ${conversation.id === currentConversationId ? "active" : ""}`}
              type="button"
              onClick={() => onSelectConversation(conversation.id)}
            >
              <span>{conversation.title}</span>
              <small>{conversation.current_state} / {formatTime(conversation.updated_at)}</small>
            </button>
          ))}
          {conversations.length === 0 && <div className="sidebar-empty">暂无对话</div>}
        </div>
      </details>
    </aside>
  );
}
