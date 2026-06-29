import { Bot, ShieldCheck } from "lucide-react";

import type { ConversationView, DatabaseStatus, ModelProviderView, ProjectView } from "../types";
import { StatusBadge } from "./StatusBadge";

type TopStatusBarProps = {
  database: DatabaseStatus;
  currentProject?: ProjectView;
  currentConversation?: ConversationView;
  selectedModelDescription?: string;
  modelProviders: ModelProviderView[];
};

export function TopStatusBar({ currentProject, currentConversation, modelProviders }: TopStatusBarProps) {
  const hasActiveLocal = modelProviders.some(
    (provider) =>
      (provider.provider_type === "local" || provider.provider_type === "local_ollama") &&
      provider.enabled &&
      provider.status === "active"
  );

  return (
    <header className="top-status-bar">
      <div className="top-brand">
        <Bot size={20} />
        <div>
          <strong>Local Agent Workbench</strong>
          <span>Local controlled mode</span>
        </div>
      </div>
      <div className="top-context-line" title={`${currentProject?.name || "未选择项目"} / ${currentConversation?.title || "未选择对话"}`}>
        <strong>{currentProject?.name || "未选择项目"}</strong>
        <span>{currentConversation?.title || "未选择对话"}</span>
      </div>
      <div className="top-badges">
        <StatusBadge kind="REAL_LOCAL" label="LOCAL ONLY" />
        <StatusBadge kind="NO_EXTERNAL_CALL" label="NO_EXTERNAL_CALL" />
        <StatusBadge kind="NO_DESKTOP_EXECUTION" label="DESKTOP MOCK" />
        <StatusBadge kind={hasActiveLocal ? "REAL_LOCAL" : "REQUIRES_APPROVAL"} label={hasActiveLocal ? "Ollama active" : "Ollama inactive"} />
        <ShieldCheck size={17} />
      </div>
    </header>
  );
}
