import { Bot, ShieldCheck } from "lucide-react";

import type { ConversationView, DatabaseStatus, ModelProviderView, ProjectView } from "../types";
import { StatusBadge } from "./StatusBadge";

type TopStatusBarProps = {
  database: DatabaseStatus;
  currentProject?: ProjectView;
  currentConversation?: ConversationView;
  selectedModelDescription?: string;
  selectedModelName?: string;
  modelProviders: ModelProviderView[];
};

export function TopStatusBar({ currentProject, currentConversation, selectedModelName, modelProviders }: TopStatusBarProps) {
  const hasActiveLocal = modelProviders.some(
    (provider) =>
      (provider.provider_type === "local" || provider.provider_type === "local_ollama") &&
      provider.enabled &&
      provider.status === "active"
  );

  return (
    <header className="top-status-bar simple-top-bar">
      <div className="top-brand">
        <Bot size={20} />
        <div>
          <strong>Local Agent Workbench</strong>
          <span>Local Only</span>
        </div>
      </div>
      <div className="top-context-line" title={`${currentProject?.name || "No project"} / ${currentConversation?.title || "No conversation"}`}>
        <strong>Model: {selectedModelName || "qwen2.5:7b"}</strong>
        <span>{currentProject?.name || "No project selected"}</span>
      </div>
      <div className="top-badges">
        <StatusBadge kind="REAL_LOCAL" label="Local Only" />
        <StatusBadge kind={hasActiveLocal ? "REAL_LOCAL" : "REQUIRES_APPROVAL"} label={hasActiveLocal ? "Ollama Active" : "Ollama Needs Active"} />
        <StatusBadge kind="NO_EXTERNAL_CALL" label="External API Disabled" />
        <StatusBadge kind="NO_DESKTOP_EXECUTION" label="Desktop Tool Disabled" />
        <ShieldCheck size={17} />
      </div>
    </header>
  );
}