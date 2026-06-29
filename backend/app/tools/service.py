from app.schemas.workbench import ToolInfo


def list_mock_tools() -> list[ToolInfo]:
    return [
        ToolInfo(
            id="tool-file-upload",
            name="文件上传",
            enabled=True,
            description="后端已支持 quarantine 隔离上传，只保存元数据和隔离文件，不自动解析或发送给 Agent。",
        ),
        ToolInfo(
            id="tool-mcp",
            name="MCP",
            enabled=False,
            description="预留 MCP 接入点，当前不启用。",
        ),
        ToolInfo(
            id="tool-web-search",
            name="联网搜索",
            enabled=False,
            description="预留搜索工具，当前不执行真实联网请求。",
        ),
    ]
