from pathlib import Path
import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.api.routes import read_workbench_state
from app.hybrid.service import architecture_state, list_artifact_center, list_model_evaluation_logs
from app.model_gateway.service import (
    create_model_invocation_approval_intent,
    list_model_invocation_log_views,
    preview_prompt,
)
from app.database.service import (
    advance_agent_step,
    create_session,
    create_task_contract,
    list_agent_deliverable_views,
    list_agent_step_views,
    list_task_contract_views,
    list_review_result_views,
    start_agent_run,
)
from app.main import app, health_check
from app.orchestrator.service import submit_user_message
from app.schemas.database import AgentRunStartRequest
from app.schemas.model_gateway import ModelInvocationRequest
from app.schemas.workbench import ChatRequest


def main() -> None:
    health = health_check()
    assert health["status"] == "ok"

    state = read_workbench_state()
    assert state.database.status == "initialized"

    chat = submit_user_message(ChatRequest(message="smoke test mock chat", model_id="mock-local-planner"))
    assert chat.conversation_id
    assert chat.project_id
    assert chat.agent_run_id

    contracts = list_task_contract_views(chat.conversation_id)
    assert contracts, "expected task contract"
    latest_contract = contracts[0]
    assert latest_contract.selected_skill, "expected selected skill"
    assert latest_contract.pipeline_steps, "expected skill pipeline steps"
    assert latest_contract.recommended_models, "expected routing recommendations"
    assert all("recommended_provider_id" in item for item in latest_contract.recommended_models)
    assert latest_contract.privacy_level in {"P0", "P1", "P2", "P3", "P4"}
    assert latest_contract.estimated_cost_level
    assert latest_contract.execution_allowed is True
    code_chat = submit_user_message(
        ChatRequest(message="Build a simple Python CLI with one test and no external API.", model_id="mock-local-planner")
    )
    assert code_chat.agent_run_id
    code_steps = list_agent_step_views(code_chat.agent_run_id)
    assert code_steps, "expected code task agent steps"
    assert code_steps[0].requires_user_approval is False, "ordinary code task must start with a non-approval step"
    code_step = advance_agent_step(code_chat.agent_run_id)
    assert code_step.status == "completed", code_step
    assert code_step.requires_user_approval is False
    assert list_agent_deliverable_views(code_chat.conversation_id), "expected deliverable from non-approval code step"

    hybrid = architecture_state()
    assert "local_ollama" in hybrid.provider_types
    assert "remote_api" in hybrid.provider_types
    assert "desktop_tool" in hybrid.provider_types
    assert hybrid.model_profiles
    assert hybrid.capability_scores
    assert hybrid.model_evaluation_logs
    assert hybrid.provider_descriptors
    assert hybrid.provider_fetch_strategies
    assert hybrid.provider_usage_snapshots
    assert hybrid.provider_cost_stats
    assert hybrid.provider_quota_windows
    assert hybrid.skill_registry
    assert hybrid.skill_pipelines
    assert hybrid.skill_packages
    assert hybrid.artifact_center
    assert hybrid.desktop_tools
    assert any(item.provider_type == "remote_api" and item.enabled is False for item in hybrid.provider_descriptors)
    assert any(item.provider_type == "desktop_tool" and item.enabled is False for item in hybrid.provider_descriptors)
    assert any(item.static_found and item.references_found for item in hybrid.skill_packages)
    assert all(item.scripts_enabled is False for item in hybrid.skill_packages)

    run = start_agent_run(
        AgentRunStartRequest(
            conversation_id=chat.conversation_id,
            project_id=chat.project_id,
        )
    )
    assert run.id

    for _ in range(8):
        steps = list_agent_step_views(run.id)
        if not any(step.status == "pending" for step in steps):
            break
        step = advance_agent_step(run.id)
        assert step.status == "completed", step
        assert step.pipeline_step_id
        assert step.step_type
        assert step.model_role
        assert step.selected_provider_id
        assert step.selected_model_id
        assert step.final_score > 0
        assert step.evaluation_status == "completed"
        assert step.alternatives
        assert step.execution_metadata.get("executor_mode") == "fallback"
        assert step.execution_metadata.get("used_local_model") is False
        assert step.execution_metadata.get("fallback_reason") == "missing_model_selection"
        assert step.execution_metadata.get("prompt_hash")

    deliverables = list_agent_deliverable_views(chat.conversation_id)
    assert deliverables, "expected deliverables from AgentExecutor"
    assert any(item.agent_name == "Review Agent" for item in deliverables), "expected Review Agent deliverable"

    reviews = list_review_result_views(chat.conversation_id)
    assert reviews, "expected review result from Review Agent step"
    assert list_model_evaluation_logs(), "expected model evaluation logs"
    preview = preview_prompt(ModelInvocationRequest(task_contract_id=latest_contract.id))
    assert preview.prompt_hash
    approval_intent = create_model_invocation_approval_intent(
        ModelInvocationRequest(
            mock_task_contract={
                "objective": "Review medium risk contact test-user@example.com without external calls.",
                "inputs": ["current UI state only"],
                "outputs": ["approval id"],
                "constraints": ["no external API", "local model only"],
                "acceptance_criteria": ["approval hash is bound"],
            }
        )
    )
    assert approval_intent.requires_user_approval is True
    assert approval_intent.approval_id
    assert approval_intent.prompt_hash
    invocation_logs = list_model_invocation_log_views()
    assert invocation_logs, "expected model invocation audit logs"
    assert invocation_logs[0].prompt_hash
    assert invocation_logs[0].prompt_length > 0
    dynamic_artifacts = list_artifact_center(conversation_id=chat.conversation_id)
    assert any(item.artifact_type == "task_contract" for item in dynamic_artifacts)

    session = create_session()
    try:
        local_fallback_contract = create_task_contract(
            session,
            project_id=chat.project_id,
            conversation_id=chat.conversation_id,
            title="Local provider fallback smoke contract",
            objective="Verify model provider fields propagate and unavailable provider falls back safely.",
            inputs=["smoke input"],
            outputs=["smoke output"],
            constraints=["local provider only", "no external API"],
            acceptance_criteria=["provider/model metadata is recorded", "fallback does not crash"],
            steps=[
                {
                    "step_index": 1,
                    "agent": "Planner",
                    "skill_ids": ["skill-planning"],
                    "goal": "Try unavailable local provider",
                    "expected_output": "Fallback output with metadata",
                    "requires_approval": False,
                }
            ],
        )
        local_fallback_contract_id = local_fallback_contract.id
        approval_contract = create_task_contract(
            session,
            project_id=chat.project_id,
            conversation_id=chat.conversation_id,
            title="Approval smoke contract",
            objective="Verify approval-required Agent step does not execute automatically.",
            inputs=["smoke input"],
            outputs=["smoke output"],
            constraints=["no external API", "no uploaded file content"],
            acceptance_criteria=["step blocks before executor"],
            steps=[
                {
                    "step_index": 1,
                    "agent": "Planner",
                    "skill_ids": ["skill-planning"],
                    "goal": "Approval-gated step",
                    "expected_output": "No deliverable before approval",
                    "requires_approval": True,
                }
            ],
        )
        approval_contract_id = approval_contract.id
    finally:
        session.close()

    local_fallback_run = start_agent_run(
        AgentRunStartRequest(
            conversation_id=chat.conversation_id,
            project_id=chat.project_id,
            task_contract_id=local_fallback_contract_id,
            model_provider_id="provider-does-not-exist",
            model_name="missing-local-model",
        )
    )
    assert local_fallback_run.model_provider_id == "provider-does-not-exist"
    assert local_fallback_run.model_name == "missing-local-model"
    local_fallback_step = advance_agent_step(local_fallback_run.id)
    assert local_fallback_step.status == "completed", local_fallback_step
    assert local_fallback_step.execution_metadata.get("executor_mode") == "fallback"
    assert local_fallback_step.execution_metadata.get("used_local_model") is False
    assert local_fallback_step.execution_metadata.get("model_provider_id") == "provider-does-not-exist"
    assert local_fallback_step.execution_metadata.get("model_name") == "missing-local-model"
    assert local_fallback_step.execution_metadata.get("fallback_reason") == "provider_not_found"

    approval_run = start_agent_run(
        AgentRunStartRequest(
            conversation_id=chat.conversation_id,
            project_id=chat.project_id,
            task_contract_id=approval_contract_id,
        )
    )
    deliverables_before = len(list_agent_deliverable_views(chat.conversation_id))
    approval_step = advance_agent_step(approval_run.id)
    deliverables_after = len(list_agent_deliverable_views(chat.conversation_id))
    assert approval_step.status == "requires_approval", approval_step
    assert approval_step.requires_user_approval is True
    assert approval_step.execution_metadata.get("approval_required") is True
    assert approval_step.execution_metadata.get("executor_mode") == "not_started"
    assert deliverables_after == deliverables_before, "approval-gated step must not create deliverables"


    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/workbench/state").status_code == 200
        providers_response = client.get("/api/model-gateway/providers")
        assert providers_response.status_code == 200
        providers = providers_response.json()
        assert any(item["id"] == "provider-local-ollama" for item in providers), "expected seeded Local Ollama provider"
        assert client.get("/api/models").status_code == 200
        privacy_response = client.post("/api/privacy/check", json={"text": "hello local workbench"})
        assert privacy_response.status_code == 200
        assert privacy_response.json()["execution_allowed"] is True
        task_response = client.post("/api/tasks", json={"message": "Build a tiny local-only Python CLI"})
        assert task_response.status_code == 200
        assert task_response.json()["id"]
        review_response = client.post(
            "/api/review",
            json={
                "task": "Build CLI with tests",
                "output": "Implemented a local-only CLI plan with tests, review notes, and no external API usage.",
            },
        )
        assert review_response.status_code == 200
        assert "completion_score" in review_response.json()
    print("smoke ok")


if __name__ == "__main__":
    main()
