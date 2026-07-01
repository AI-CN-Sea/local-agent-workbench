from dataclasses import dataclass


ORCHESTRATOR_STATES = [
    "idle",
    "requirement_analysis",
    "waiting_requirement_confirmation",
    "outline_generation",
    "waiting_outline_confirmation",
    "task_contract_generation",
    "agent_dispatch_mock",
    "review_mock",
    "memory_suggestion",
]


@dataclass(frozen=True)
class StateTransition:
    state: str
    note: str


def run_mock_state_machine(user_message: str) -> list[StateTransition]:
    preview = user_message.strip()[:80] or "empty request"
    return [
        StateTransition("idle", "等待用户输入。"),
        StateTransition("requirement_analysis", f"基于规则整理需求：{preview}"),
        StateTransition("waiting_requirement_confirmation", "生成需求确认卡片，等待确认。"),
        StateTransition("outline_generation", "生成 mock 执行大纲。"),
        StateTransition("waiting_outline_confirmation", "等待用户确认大纲。"),
        StateTransition("task_contract_generation", "创建 task_contracts 记录。"),
        StateTransition("agent_dispatch_mock", "仅创建 mock 子 Agent 分工，不调用模型。"),
        StateTransition("review_mock", "生成 mock 审核记录。"),
        StateTransition("memory_suggestion", "生成记忆建议，不自动写入长期记忆之外的外部系统。"),
    ]


def final_state(transitions: list[StateTransition]) -> str:
    if not transitions:
        return "idle"
    return transitions[-1].state
