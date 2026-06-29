import { ProviderMonitor } from "../components/ProviderMonitor";
import type { WorkspaceViewProps } from "./viewTypes";

export function ProvidersView(props: WorkspaceViewProps) {
  return (
    <>
      <ViewHeader title="模型服务监控" subtitle="仅本机 Ollama provider 可真实检测/调用；remote_api 与 desktop_tool 保持 mock/disabled。" />
      <div className="view-scroll">
        <ProviderMonitor
          hybridArchitecture={props.hybridArchitecture}
          modelProviders={props.modelProviders}
          promptTemplates={props.promptTemplates}
          providerCheck={props.providerCheck}
          localModels={props.localModels}
          selectedLocalModel={props.selectedLocalModel}
          localProviderEndpoints={props.localProviderEndpoints}
          onCreateMockProvider={props.onCreateMockProvider}
          onCreateLocalProvider={props.onCreateLocalProvider}
          onEnableProvider={props.onEnableProvider}
          onSetProviderActive={props.onSetProviderActive}
          onDisableProvider={props.onDisableProvider}
          onSetLocalEndpoint={props.onSetLocalEndpoint}
          onCheckProvider={props.onCheckProvider}
          onFetchLocalModels={props.onFetchLocalModels}
          onSelectLocalModel={props.onSelectLocalModel}
          onTestProvider={props.onTestProvider}
          onCreatePromptTemplate={props.onCreatePromptTemplate}
        />
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
