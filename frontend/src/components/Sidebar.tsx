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
  { view: "workbench", label: "Workbench", icon: MessageSquarePlus, helper: "Run task" },
  { view: "providers", label: "Models", icon: Bot, helper: "Ollama" },
  { view: "skills", label: "Skills", icon: Sparkles, helper: "User skills" },
  { view: "artifacts", label: "Artifacts", icon: Archive, helper: "Final output" },
  { view: "privacy", label: "Privacy", icon: ShieldAlert, helper: "Local only" },
  { view: "settings", label: "Settings", icon: Settings, helper: "Mode" }
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
  const activeLocalProviders = modelProviders.filter((provider) => (provider.provider_type === "local" || provider.provider_type === "local_ollama") && provider.enabled && provider.status === "active").length;

  return (
    <aside className="sidebar" aria-label="Workbench navigation">
      <div className="sidebar-brand">
        <Bot size={22} />
        <div>
          <strong>Agent Workbench</strong>
          <span>Simple local workspace</span>
        </div>
      </div>

      <nav className="view-nav" aria-label="Primary views">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button key={item.view} className={`view-nav-item ${activeView === item.view ? "active" : ""}`} type="button" onClick={() => onViewChange(item.view)}>
              <Icon size={16} />
              <span>{item.label}</span>
              <small>{item.helper}</small>
            </button>
          );
        })}
      </nav>

      <section className="current-context">
        <div className="sidebar-section-title">
          <strong>Current Task Space</strong>
          <button type="button" onClick={onCreateProject} title="New project">
            <FolderPlus size={15} />
          </button>
        </div>
        <div className="context-card">
          <span>Project</span>
          <strong>{currentProject?.name || "No project"}</strong>
          <span>Conversation</span>
          <strong>{currentConversation?.title || "No conversation"}</strong>
        </div>
        <div className="compact-metrics-row">
          <span>Tasks {taskContracts.length}</span>
          <span>Skills {skills.length}</span>
          <span>Models {activeLocalProviders}</span>
          <span>Artifacts {artifactCount}</span>
        </div>
      </section>

      <details className="sidebar-details">
        <summary><ChevronDown size={14} /> Projects</summary>
        <div className="sidebar-list">
          {projects.map((project) => (
            <button key={project.id} className={`sidebar-list-item ${project.id === currentProjectId ? "active" : ""}`} type="button" onClick={() => onSelectProject(project.id)}>
              <span>{project.name}</span>
              <small>{project.status} / {formatTime(project.created_at)}</small>
            </button>
          ))}
          {projects.length === 0 && <div className="sidebar-empty">No projects</div>}
        </div>
      </details>

      <details className="sidebar-details">
        <summary><ChevronDown size={14} /> Conversations</summary>
        <div className="sidebar-list">
          {conversations.slice(0, 8).map((conversation) => (
            <button key={conversation.id} className={`sidebar-list-item ${conversation.id === currentConversationId ? "active" : ""}`} type="button" onClick={() => onSelectConversation(conversation.id)}>
              <span>{conversation.title}</span>
              <small>{toUserStatus(conversation.current_state)} / {formatTime(conversation.updated_at)}</small>
            </button>
          ))}
          {conversations.length === 0 && <div className="sidebar-empty">No conversations</div>}
        </div>
      </details>
    </aside>
  );
}

function toUserStatus(status: string) {
  const map: Record<string, string> = {
    blocked: "Needs confirmation",
    draft: "Ready",
    running: "Running",
    paused: "Waiting to continue",
    completed: "Completed",
    failed: "Needs attention",
    waiting_requirement_confirmation: "Ready",
    waiting_outline_confirmation: "Ready"
  };
  return map[status] || status;
}