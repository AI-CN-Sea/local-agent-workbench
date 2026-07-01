import type { LocalModelInfo, ModelProviderView } from "../types";

export function isLocalProviderType(providerType: string): boolean {
  return providerType === "local_ollama" || providerType === "local";
}

export function getPrimaryLocalProvider(providers: ModelProviderView[]): ModelProviderView | undefined {
  return providers.find((provider) => provider.id === "provider-local-ollama")
    || providers.find((provider) => provider.name === "Local Ollama")
    || providers.find((provider) => provider.provider_type === "local_ollama" && provider.enabled && provider.status === "active")
    || providers.find((provider) => provider.provider_type === "local_ollama" || provider.provider_type === "local");
}

export function sortLocalModels(models: LocalModelInfo[]): LocalModelInfo[] {
  return [...models].sort((a, b) => {
    if (a.name === "qwen2.5:7b") return -1;
    if (b.name === "qwen2.5:7b") return 1;
    return a.name.localeCompare(b.name);
  });
}

export function getPreferredLocalModelName(models: LocalModelInfo[]): string {
  return models.find((model) => model.name === "qwen2.5:7b")?.name || models[0]?.name || "";
}