from app.schemas.workbench import AgentStatus, SubAgentAssignment


def get_agent_status() -> AgentStatus:
    return AgentStatus(
        controller="主控 Agent",
        phase="mock 状态机",
        sub_agents=[
            SubAgentAssignment(name="Planner", role="任务规划", status="mock_ready"),
            SubAgentAssignment(name="Writer", role="内容整理", status="mock_ready"),
            SubAgentAssignment(name="Code Agent", role="代码任务", status="mock_ready"),
            SubAgentAssignment(name="Review Agent", role="审核结果", status="mock_ready"),
        ],
        review_result="等待用户确认需求和大纲，随后生成 mock 审核结果。",
    )
