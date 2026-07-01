from app.schemas.workbench import MemorySuggestion


def get_memory_suggestions() -> list[MemorySuggestion]:
    return [
        MemorySuggestion(
            id="mem-001",
            title="项目偏好",
            detail="建议记录：本项目默认先使用本地 mock 数据和 SQLite。",
        ),
        MemorySuggestion(
            id="mem-002",
            title="安全偏好",
            detail="建议记录：外部 API/搜索/MCP 关闭；本机模型调用前需要 Model Gateway 审查。",
        ),
    ]


def get_memory_suggestion(suggestion_id: str) -> MemorySuggestion | None:
    for suggestion in get_memory_suggestions():
        if suggestion.id == suggestion_id:
            return suggestion
    return None
