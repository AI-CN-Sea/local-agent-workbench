import type {
  HybridArchitectureState,
  LocalModelInfo,
  ModelProviderCheckResult,
  ModelProviderView,
  PromptTemplateView
} from "../types";
import { EmptyState } from "./EmptyState";
import { metadataBool, metadataText } from "./format";
import { PanelCard } from "./PanelCard";
import { StatusBadge } from "./StatusBadge";

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

export function ProviderMonitor({
  hybridArchitecture,
  modelProviders,
  promptTemplates,
  providerCheck,
  localModels,
  selectedLocalModel,
  localProviderEndpoints,
  onCreateMockProvider,
  onCreateLocalProvider,
  onEnableProvider,
  onSetProviderActive,
  onDisableProvider,
  onSetLocalEndpoint,
  onCheckProvider,
  onFetchLocalModels,
  onSelectLocalModel,
  onTestProvider,
  onCreatePromptTemplate
}: ProviderMonitorProps) {
  const descriptors = hybridArchitecture?.provider_descriptors ?? [];
  const strategies = hybridArchitecture?.provider_fetch_strategies ?? [];

  return (
    <div className="provider-monitor">
      <PanelCard
        title="Provider Controls"
        eyebrow="Model Gateway"
        compact
        actions={
          <div className="mini-actions">
            {onCreateLocalProvider && (
              <button type="button" onClick={onCreateLocalProvider}>
                Add Local
              </button>
            )}
            {onCreateMockProvider && (
              <button type="button" onClick={onCreateMockProvider}>
                Add Mock
              </button>
            )}
          </div>
        }
      >
        <div className="badge-row">
          <StatusBadge kind="REAL_LOCAL" label="Ollama localhost allowed" />
          <StatusBadge kind="MOCK_ONLY" label="remote_api mock" />
          <StatusBadge kind="NO_DESKTOP_EXECUTION" label="desktop_tool mock" />
        </div>
        <small className="muted-line">白名单 endpoint: {localProviderEndpoints.join(" / ")}</small>
      </PanelCard>

      <div className="compact-list">
        {modelProviders.length === 0 ? (
          <EmptyState title="暂无 Provider" description="可以添加 mock 或受控本机 Ollama provider。" />
        ) : (
          modelProviders.map((provider) => {
            const isLocal = provider.provider_type === "local" || provider.provider_type === "local_ollama";
            const isActive = provider.enabled && provider.status === "active";
            return (
              <article className="compact-item provider-item" key={provider.id}>
                <div className="row-between">
                  <strong>{provider.name}</strong>
                  <StatusBadge
                    kind={isLocal && isActive ? "REAL_LOCAL" : provider.provider_type === "mock" ? "MOCK_ONLY" : "RESERVED_DISABLED"}
                    label={`${provider.provider_type} / ${provider.status}`}
                  />
                </div>
                <small>{provider.endpoint || "No endpoint"} / privacy {provider.privacy_mode}</small>
                {isLocal && onSetLocalEndpoint && (
                  <select value={provider.endpoint || ""} onChange={(event) => onSetLocalEndpoint(provider.id, event.target.value)}>
                    <option value="">选择本机 endpoint</option>
                    {localProviderEndpoints.map((endpoint) => (
                      <option key={endpoint} value={endpoint}>
                        {endpoint}
                      </option>
                    ))}
                  </select>
                )}
                <div className="mini-actions">
                  {onEnableProvider && (
                    <button type="button" onClick={() => onEnableProvider(provider.id)}>
                      启用 provider
                    </button>
                  )}
                  {onSetProviderActive && (
                    <button type="button" onClick={() => onSetProviderActive(provider.id)}>
                      设为 active
                    </button>
                  )}
                  {onDisableProvider && (
                    <button type="button" onClick={() => onDisableProvider(provider.id)}>
                      禁用
                    </button>
                  )}
                  {isLocal && onCheckProvider && (
                    <button type="button" onClick={() => onCheckProvider(provider.id)}>
                      检测本机 provider
                    </button>
                  )}
                  {isLocal && onFetchLocalModels && (
                    <button type="button" onClick={() => onFetchLocalModels(provider.id)}>
                      查看模型
                    </button>
                  )}
                </div>
              </article>
            );
          })
        )}
      </div>

      {providerCheck && (
        <div className="compact-item">
          <strong>Provider Check</strong>
          <small>{providerCheck.reachable ? "reachable" : "unreachable"} / {providerCheck.provider_kind || "unknown"}</small>
          <small>{providerCheck.message}</small>
        </div>
      )}

      {localModels.length > 0 && (
        <div className="compact-item">
          <strong>Local Models</strong>
          {onSelectLocalModel && (
            <select value={selectedLocalModel} onChange={(event) => onSelectLocalModel(event.target.value)}>
              <option value="">选择本机模型</option>
              {localModels.map((model) => (
                <option key={`${model.provider_kind}-${model.name}`} value={model.name}>
                  {model.name} / {model.provider_kind}
                </option>
              ))}
            </select>
          )}
          {onTestProvider && (
            <button type="button" onClick={onTestProvider}>
              本地模型调用测试
            </button>
          )}
        </div>
      )}

      <PanelCard
        title="Prompt Templates"
        eyebrow="Prompt / Task Contract"
        compact
        actions={
          onCreatePromptTemplate ? (
            <button type="button" onClick={onCreatePromptTemplate}>
              新建模板
            </button>
          ) : undefined
        }
      >
        <div className="compact-list">
          {promptTemplates.slice(0, 6).map((prompt) => (
            <div className="compact-item" key={prompt.id}>
              <strong>{prompt.name}</strong>
              <small>{prompt.task_type} / {prompt.status}</small>
              <small>{prompt.safety_notes || "No safety notes"}</small>
            </div>
          ))}
          {promptTemplates.length === 0 && <EmptyState title="暂无 Prompt Template" />}
        </div>
      </PanelCard>

      <PanelCard title="Provider Descriptors" eyebrow="Hybrid Architecture" compact>
        <div className="compact-list">
          {descriptors.slice(0, 6).map((provider, index) => (
            <div className="compact-item" key={`descriptor-${metadataText(provider.provider_id, String(index))}`}>
              <strong>{metadataText(provider.display_name, "Provider")}</strong>
              <small>
                {metadataText(provider.provider_type, "mock")} / {metadataText(provider.status, "disabled")}
              </small>
              <small>{metadataText(provider.notes, "descriptor only")}</small>
            </div>
          ))}
          {descriptors.length === 0 && <EmptyState title="暂无 Provider Descriptor" />}
        </div>
      </PanelCard>

      <PanelCard title="Fetch Strategy" eyebrow="Reserved" compact>
        <div className="compact-list">
          {strategies.slice(0, 4).map((strategy, index) => (
            <div className="compact-item" key={`strategy-${metadataText(strategy.strategy_id, String(index))}`}>
              <strong>{metadataText(strategy.strategy_kind, "strategy")}</strong>
              <small>
                {metadataText(strategy.provider_id, "provider")} / {metadataBool(strategy.enabled) ? "enabled" : "disabled"}
              </small>
              <small>{metadataText(strategy.disabled_reason, "No credential, cookie, CLI, OAuth, or dashboard fetch is enabled.")}</small>
            </div>
          ))}
          {strategies.length === 0 && <EmptyState title="暂无 Fetch Strategy" />}
        </div>
      </PanelCard>
    </div>
  );
}
