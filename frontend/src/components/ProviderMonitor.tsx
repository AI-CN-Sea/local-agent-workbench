import type { HybridArchitectureState, LocalModelInfo, ModelProviderCheckResult, ModelProviderView, PromptTemplateView } from "../types";
import { EmptyState } from "./EmptyState";
import { metadataBool, metadataText } from "./format";
import { PanelCard } from "./PanelCard";
import { StatusBadge } from "./StatusBadge";
import { getPrimaryLocalProvider, sortLocalModels } from "./localProvider";

type ProviderMonitorProps = {
  hybridArchitecture: HybridArchitectureState | null;
  modelProviders: ModelProviderView[];
  promptTemplates: PromptTemplateView[];
  providerCheck: ModelProviderCheckResult | null;
  localModels: LocalModelInfo[];
  selectedLocalModel: string;
  localProviderEndpoints: string[];
  onCreateMockProvider?: () => void;
  onCreateLocalProvider?: () => void;
  onEnableProvider?: (providerId: string) => void;
  onSetProviderActive?: (providerId: string) => void;
  onDisableProvider?: (providerId: string) => void;
  onSetLocalEndpoint?: (providerId: string, endpoint: string) => void;
  onCheckProvider?: (providerId: string) => void;
  onFetchLocalModels?: (providerId?: string) => void;
  onSelectLocalModel?: (value: string) => void;
  onTestProvider?: () => void;
  onCreatePromptTemplate?: () => void;
};

export function ProviderMonitor(props: ProviderMonitorProps) {
  const localProvider = getPrimaryLocalProvider(props.modelProviders);
  const debugProviders = props.modelProviders.filter((provider) => provider.id !== localProvider?.id);
  const qwenModel = props.localModels.find((model) => model.name === "qwen2.5:7b");
  const visibleModels = sortLocalModels(props.localModels);

  return (
    <div className="provider-monitor">
      <PanelCard title="Local Ollama" eyebrow="Model Settings" compact>
        {localProvider ? (
          <div className="local-provider-card">
            <div className="section-heading">
              <div>
                <strong>{localProvider.name}</strong>
                <small>{localProvider.endpoint || "No endpoint"}</small>
              </div>
              <StatusBadge kind={localProvider.enabled && localProvider.status === "active" ? "REAL_LOCAL" : "REQUIRES_APPROVAL"} label={localProvider.enabled && localProvider.status === "active" ? "active" : "needs active"} />
            </div>
            {props.onSetLocalEndpoint && (
              <select value={localProvider.endpoint || ""} onChange={(event) => props.onSetLocalEndpoint?.(localProvider.id, event.target.value)}>
                <option value="">Select localhost endpoint</option>
                {props.localProviderEndpoints.map((endpoint) => <option key={endpoint} value={endpoint}>{endpoint}</option>)}
              </select>
            )}
            <div className="mini-actions">
              <button type="button" onClick={() => props.onEnableProvider?.(localProvider.id)}>Enable</button>
              <button type="button" onClick={() => props.onSetProviderActive?.(localProvider.id)}>Set Active</button>
              <button type="button" onClick={() => props.onCheckProvider?.(localProvider.id)}>Check Provider</button>
              <button type="button" onClick={() => props.onFetchLocalModels?.(localProvider.id)}>Fetch Models</button>
              <button type="button" onClick={() => props.onDisableProvider?.(localProvider.id)}>Disable</button>
            </div>
            {providerCheckBlock(props.providerCheck)}
          </div>
        ) : (
          <div className="compact-item">
            <strong>Local Ollama is not seeded.</strong>
            <small>Click Add Local once. If it already exists, the app will reuse it.</small>
            <button type="button" onClick={props.onCreateLocalProvider}>Add Local</button>
          </div>
        )}
      </PanelCard>

      <PanelCard title="Loaded Local Models" eyebrow="Ollama models" compact>
        {visibleModels.length > 0 ? (
          <div className="compact-list">
            <div className="compact-item highlighted-item">
              <strong>{qwenModel?.name || visibleModels[0].name}</strong>
              <small>{qwenModel ? "Recommended default model" : "First available local model"}</small>
              <StatusBadge kind="REAL_LOCAL" label="selectable" />
            </div>
            {props.onSelectLocalModel && (
              <select value={props.selectedLocalModel} onChange={(event) => props.onSelectLocalModel?.(event.target.value)}>
                <option value="">Select local model</option>
                {visibleModels.map((model) => <option key={`${model.provider_kind}-${model.name}`} value={model.name}>{model.name} / ollama</option>)}
              </select>
            )}
            {props.onTestProvider && <button type="button" onClick={props.onTestProvider}>Local model call test</button>}
          </div>
        ) : (
          <EmptyState title="No local models loaded" description="Start Ollama, set Local Ollama active, then click Fetch Models." />
        )}
      </PanelCard>

      <details className="advanced-details">
        <summary>Advanced / Debug Providers</summary>
        <div className="compact-list">
          {debugProviders.map((provider) => (
            <div className="compact-item" key={provider.id}>
              <strong>{provider.name}</strong>
              <small>{provider.provider_type} / {provider.status} / {provider.endpoint || "no endpoint"}</small>
              <StatusBadge kind={provider.provider_type === "mock" ? "MOCK_ONLY" : "RESERVED_DISABLED"} label={provider.enabled ? "enabled" : "disabled"} />
            </div>
          ))}
          {debugProviders.length === 0 && <EmptyState title="No debug providers" />}
        </div>
      </details>

      <details className="advanced-details">
        <summary>Advanced Prompt Templates and Routing Metadata</summary>
        <div className="compact-list">
          {props.promptTemplates.slice(0, 6).map((prompt) => (
            <div className="compact-item" key={prompt.id}>
              <strong>{prompt.name}</strong>
              <small>{prompt.task_type} / {prompt.status}</small>
              <small>{prompt.safety_notes || "No safety notes"}</small>
            </div>
          ))}
          {(props.hybridArchitecture?.provider_fetch_strategies ?? []).slice(0, 4).map((strategy, index) => (
            <div className="compact-item" key={`strategy-${metadataText(strategy.strategy_id, String(index))}`}>
              <strong>{metadataText(strategy.strategy_kind, "strategy")}</strong>
              <small>{metadataText(strategy.provider_id, "provider")} / {metadataBool(strategy.enabled) ? "enabled" : "disabled"}</small>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

function providerCheckBlock(providerCheck: ModelProviderCheckResult | null) {
  if (!providerCheck) return null;
  return (
    <div className="compact-item">
      <strong>Provider check</strong>
      <small>{providerCheck.reachable ? "reachable" : "unreachable"} / {providerCheck.provider_kind || "unknown"}</small>
      <small>{providerCheck.message}</small>
    </div>
  );
}

