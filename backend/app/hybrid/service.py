from datetime import UTC, datetime
from pathlib import Path

from app.schemas.hybrid import (
    AdaptiveRoutingAlternative,
    ArtifactCenterItem,
    DesktopToolProfile,
    HybridArchitectureState,
    ModelCapabilityScore,
    ModelEvaluationLogView,
    ModelProfile,
    ModelRoutingRecommendation,
    PrivacyGatewayResult,
    ProviderCostStats,
    ProviderDescriptor,
    ProviderFetchStrategy,
    ProviderQuotaWindow,
    ProviderUsageSnapshot,
    SkillPackageMetadata,
    SkillPipeline,
    SkillPipelineStep,
    SkillRegistryItem,
)
from app.database.crud import create_record
from app.database.models import (
    AgentDeliverableRecord,
    AgentRunRecord,
    ModelEvaluationLogRecord,
    ModelInvocationLogRecord,
    TaskContractRecord,
)
from app.database.session import create_session
from app.security.payload_scanner import scan_payload
from app.security.query_redactor import redact_query

from sqlalchemy import select

PROVIDER_TYPES = ["local_ollama", "remote_api", "desktop_tool", "mock"]
OLLAMA_ENDPOINTS = ["http://127.0.0.1:11434", "http://localhost:11434"]
REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_PACKAGE_ROOT = REPO_ROOT / "skills"


def utc_now() -> datetime:
    return datetime.now(UTC)


def list_provider_descriptors() -> list[ProviderDescriptor]:
    return [
        ProviderDescriptor(
            provider_id="provider-local-ollama",
            provider_type="local_ollama",
            display_name="Local Ollama",
            description="Only real callable provider in the current stage; restricted to localhost 11434.",
            base_url="http://127.0.0.1:11434",
            enabled=True,
            status="reserved_active",
            privacy_mode="local_only",
            auth_policy="none",
            quota_policy="local_mock",
            pricing_policy="local_zero_cost_mock",
            health_policy="local_probe_only",
            allowed_fetch_strategies=["local_probe", "local_invoke", "mock"],
            supports_invoke=True,
            supports_status_fetch=True,
            supports_local_probe=True,
            notes="No API key, cookie, OAuth, CLI token, or external fetch is used.",
        ),
        ProviderDescriptor(
            provider_id="provider-mock-remote",
            provider_type="remote_api",
            display_name="Remote API Placeholder",
            description="Future multi-API provider descriptor. Current implementation is mock only.",
            base_url=None,
            enabled=False,
            status="mock_reserved_disabled",
            privacy_mode="redacted_context_only",
            auth_policy="reserved_disabled",
            quota_policy="mock_only",
            pricing_policy="mock_only",
            health_policy="mock_only",
            allowed_fetch_strategies=["mock"],
            supports_status_fetch=True,
            notes="No external API call, API key, OAuth, cookie, CLI token, usage fetch, cost fetch, or quota fetch is enabled.",
        ),
        ProviderDescriptor(
            provider_id="provider-mock-desktop",
            provider_type="desktop_tool",
            display_name="Desktop Tool Placeholder",
            description="Future controlled desktop/local software layer. Current implementation is mock only.",
            enabled=False,
            status="mock_reserved_disabled",
            privacy_mode="local_only",
            auth_policy="none",
            quota_policy="not_applicable",
            pricing_policy="not_applicable",
            health_policy="mock_only",
            allowed_fetch_strategies=["mock"],
            notes="No desktop software, shell, browser, file write, or automation is executed.",
        ),
        ProviderDescriptor(
            provider_id="provider-mock-fallback",
            provider_type="mock",
            display_name="Mock Fallback",
            description="Rule-based fallback provider for offline UI and pipeline testing.",
            enabled=True,
            status="active",
            privacy_mode="local_only",
            auth_policy="none",
            quota_policy="mock_only",
            pricing_policy="mock_only",
            health_policy="mock_only",
            allowed_fetch_strategies=["mock"],
            supports_invoke=False,
            notes="Returns mock metadata only.",
        ),
    ]


def list_provider_fetch_strategies() -> list[ProviderFetchStrategy]:
    now = utc_now()
    rows: list[ProviderFetchStrategy] = [
        ProviderFetchStrategy(
            strategy_id="strategy-ollama-local-probe",
            provider_id="provider-local-ollama",
            strategy_kind="local_probe",
            enabled=True,
            available=True,
            priority=1,
            safety_level="local_only",
            requires_user_permission=False,
            last_checked_at=now,
        ),
        ProviderFetchStrategy(
            strategy_id="strategy-ollama-mock",
            provider_id="provider-local-ollama",
            strategy_kind="mock",
            enabled=True,
            available=True,
            priority=90,
            safety_level="safe_mock",
            requires_user_permission=False,
            last_checked_at=now,
        ),
        ProviderFetchStrategy(
            strategy_id="strategy-remote-mock",
            provider_id="provider-mock-remote",
            strategy_kind="mock",
            enabled=True,
            available=True,
            priority=100,
            safety_level="mock_only",
            requires_user_permission=False,
            last_checked_at=now,
            disabled_reason="Remote API is a reserved placeholder; no external fetch is enabled.",
        ),
        ProviderFetchStrategy(
            strategy_id="strategy-desktop-mock",
            provider_id="provider-mock-desktop",
            strategy_kind="mock",
            enabled=True,
            available=True,
            priority=100,
            safety_level="mock_only",
            requires_user_permission=False,
            last_checked_at=now,
            disabled_reason="Desktop tools are reserved placeholders; no desktop execution is enabled.",
        ),
    ]
    reserved_kinds = ["api_token", "oauth", "cli", "browser_cookie", "web_dashboard"]
    for provider_id in ["provider-local-ollama", "provider-mock-remote", "provider-mock-desktop"]:
        for index, kind in enumerate(reserved_kinds, start=200):
            rows.append(
                ProviderFetchStrategy(
                    strategy_id=f"strategy-{provider_id}-{kind}",
                    provider_id=provider_id,
                    strategy_kind=kind,
                    enabled=False,
                    available=False,
                    priority=index,
                    safety_level="reserved_disabled",
                    requires_user_permission=True,
                    disabled_reason=f"{kind} strategy is reserved and disabled. No credential, cookie, token, CLI, or dashboard fetch is performed.",
                )
            )
    return rows


def list_provider_usage_snapshots() -> list[ProviderUsageSnapshot]:
    now = utc_now()
    session = create_session()
    try:
        records = list(session.scalars(select(ModelInvocationLogRecord).order_by(ModelInvocationLogRecord.created_at.desc()).limit(500)))
    finally:
        session.close()
    if not records:
        return [
            ProviderUsageSnapshot(
                provider_id="provider-local-ollama",
                model_id="local_qwen3_8b",
                date=now.date().isoformat(),
                request_count=0,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                success_count=0,
                failure_count=0,
                blocked_count=0,
                avg_latency_ms=0,
                created_at=now,
            ),
            ProviderUsageSnapshot(
                provider_id="provider-mock-remote",
                model_id="mock_reasoning_model",
                date=now.date().isoformat(),
                blocked_count=0,
                created_at=now,
            ),
        ]
    buckets: dict[tuple[str, str | None, str], dict[str, int]] = {}
    for record in records:
        provider_id = record.provider_id or f"provider-type-{record.provider_type or 'mock'}"
        key = (provider_id, record.model_id, record.created_at.date().isoformat())
        bucket = buckets.setdefault(
            key,
            {
                "request_count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "success_count": 0,
                "failure_count": 0,
                "blocked_count": 0,
                "latency_total": 0,
                "latency_count": 0,
            },
        )
        bucket["request_count"] += 1
        bucket["input_tokens"] += record.input_tokens or 0
        bucket["output_tokens"] += record.output_tokens or 0
        bucket["success_count"] += 1 if record.success else 0
        bucket["failure_count"] += 0 if record.success else 1
        bucket["blocked_count"] += 1 if record.blocked else 0
        if record.latency_ms is not None:
            bucket["latency_total"] += record.latency_ms
            bucket["latency_count"] += 1
    return [
        ProviderUsageSnapshot(
            provider_id=provider_id,
            model_id=model_id,
            date=date,
            request_count=bucket["request_count"],
            input_tokens=bucket["input_tokens"],
            output_tokens=bucket["output_tokens"],
            total_tokens=bucket["input_tokens"] + bucket["output_tokens"],
            success_count=bucket["success_count"],
            failure_count=bucket["failure_count"],
            blocked_count=bucket["blocked_count"],
            avg_latency_ms=int(bucket["latency_total"] / bucket["latency_count"]) if bucket["latency_count"] else 0,
            created_at=now,
        )
        for (provider_id, model_id, date), bucket in sorted(buckets.items(), key=lambda item: item[0][2], reverse=True)
    ][:50]


def list_provider_cost_stats() -> list[ProviderCostStats]:
    now = utc_now()
    session = create_session()
    try:
        records = list(session.scalars(select(ModelInvocationLogRecord).order_by(ModelInvocationLogRecord.created_at.desc()).limit(500)))
    finally:
        session.close()
    if not records:
        return [
            ProviderCostStats(
                provider_id="provider-local-ollama",
                model_id="local_qwen3_8b",
                skill_id="requirement_analysis",
                step_type="local_requirement_analysis",
                estimated_cost=0.0,
                cost_level="local_zero_cost_mock",
                currency="USD",
                period="session_mock",
                created_at=now,
            ),
            ProviderCostStats(
                provider_id="provider-mock-remote",
                model_id="mock_reasoning_model",
                skill_id="architecture_analysis",
                step_type="architecture_planning",
                estimated_cost=0.0,
                cost_level="remote_disabled_mock",
                currency="USD",
                period="future_reserved",
                created_at=now,
            ),
        ]
    buckets: dict[tuple[str, str | None, str | None, str | None], dict[str, float]] = {}
    for record in records:
        provider_id = record.provider_id or f"provider-type-{record.provider_type or 'mock'}"
        key = (provider_id, record.model_id, record.skill_id, record.pipeline_step_id or record.step_id or record.mode)
        bucket = buckets.setdefault(key, {"input_tokens": 0.0, "output_tokens": 0.0, "estimated_cost": 0.0})
        bucket["input_tokens"] += record.input_tokens or 0
        bucket["output_tokens"] += record.output_tokens or 0
        bucket["estimated_cost"] += record.estimated_cost or 0.0
    return [
        ProviderCostStats(
            provider_id=provider_id,
            model_id=model_id,
            skill_id=skill_id,
            step_type=step_type,
            input_tokens=int(bucket["input_tokens"]),
            output_tokens=int(bucket["output_tokens"]),
            estimated_cost=float(bucket["estimated_cost"]),
            cost_level="local_zero_cost" if provider_id and "local" in provider_id else "mock_or_reserved",
            currency="USD",
            period="rolling_local_logs",
            created_at=now,
        )
        for (provider_id, model_id, skill_id, step_type), bucket in list(buckets.items())[:50]
    ]


def list_provider_quota_windows() -> list[ProviderQuotaWindow]:
    return [
        ProviderQuotaWindow(
            provider_id="provider-local-ollama",
            window_type="session",
            quota_limit=0,
            quota_used=0,
            quota_remaining=0,
            reset_at=None,
            status="local_unmetered_mock",
            source="local",
        ),
        ProviderQuotaWindow(
            provider_id="provider-mock-remote",
            window_type="unknown",
            quota_limit=0,
            quota_used=0,
            quota_remaining=0,
            reset_at=None,
            status="remote_fetch_disabled",
            source="remote_disabled",
        ),
        ProviderQuotaWindow(
            provider_id="provider-mock-desktop",
            window_type="unknown",
            quota_limit=0,
            quota_used=0,
            quota_remaining=0,
            reset_at=None,
            status="desktop_execution_disabled",
            source="mock",
        ),
    ]


def list_model_profiles() -> list[ModelProfile]:
    return [
        ModelProfile(
            model_id="local_qwen3_8b",
            provider_id="provider-local-ollama",
            provider_type="local_ollama",
            model_name="qwen3:8b",
            display_name="Local Qwen3 8B",
            supports_reasoning=True,
            supports_writing=True,
            supports_json=True,
            context_window=8192,
            cost_level="local",
            latency_level="medium",
            reliability_level="medium",
            initial_rank=10,
            notes="Local requirement analysis, privacy first-pass, summarization, routing.",
        ),
        ModelProfile(
            model_id="local_qwen_coder_7b",
            provider_id="provider-local-ollama",
            provider_type="local_ollama",
            model_name="qwen2.5-coder:7b",
            display_name="Local Qwen Coder 7B",
            supports_code=True,
            supports_reasoning=True,
            supports_json=True,
            context_window=8192,
            cost_level="local",
            latency_level="medium",
            reliability_level="medium",
            initial_rank=20,
            notes="Local code explanation, Codex instruction drafting, simple review.",
        ),
        ModelProfile(
            model_id="mock_reasoning_model",
            provider_id="provider-mock-remote",
            provider_type="remote_api",
            model_name="mock-reasoning",
            display_name="Mock Reasoning Model",
            supports_reasoning=True,
            supports_json=True,
            context_window=32768,
            cost_level="high",
            latency_level="medium",
            initial_rank=60,
            notes="Mock placeholder for future external reasoning APIs. No real network call.",
        ),
        ModelProfile(
            model_id="mock_claude_code_model",
            provider_id="provider-mock-remote",
            provider_type="remote_api",
            model_name="mock-code-specialist",
            display_name="Mock Code Specialist",
            supports_code=True,
            supports_reasoning=True,
            supports_json=True,
            context_window=32768,
            cost_level="high",
            initial_rank=55,
            notes="Future code specialist role placeholder; not bound to any real vendor.",
        ),
        ModelProfile(
            model_id="mock_writing_model",
            provider_id="provider-mock-remote",
            provider_type="remote_api",
            model_name="mock-writing",
            display_name="Mock Writing Model",
            supports_writing=True,
            supports_json=True,
            context_window=32768,
            cost_level="medium",
            initial_rank=65,
            notes="Future writing/report/PPT copy model placeholder.",
        ),
        ModelProfile(
            model_id="mock_diagram_model",
            provider_id="provider-mock-remote",
            provider_type="remote_api",
            model_name="mock-diagram",
            display_name="Mock Diagram Model",
            supports_diagram=True,
            supports_json=True,
            context_window=16384,
            cost_level="medium",
            initial_rank=70,
            notes="Future diagram/PlantUML/Mermaid/Visio structure model placeholder.",
        ),
        ModelProfile(
            model_id="mock_reviewer_model",
            provider_id="provider-mock-remote",
            provider_type="remote_api",
            model_name="mock-reviewer",
            display_name="Mock Reviewer Model",
            supports_reasoning=True,
            supports_json=True,
            context_window=32768,
            cost_level="medium",
            initial_rank=50,
            notes="Future quality/safety reviewer placeholder.",
        ),
    ]


def list_capability_scores() -> list[ModelCapabilityScore]:
    rows: list[ModelCapabilityScore] = []
    for profile in list_model_profiles():
        for skill_id, step_type in [
            ("requirement_analysis", "local_requirement_analysis"),
            ("code_development", "code_implementation"),
            ("code_review_plan", "code_review"),
            ("document_generation", "document_draft"),
            ("diagram_generation", "diagram_plan"),
        ]:
            capability = 0.78 if profile.provider_type == "local_ollama" and "local" in step_type else 0.55
            rows.append(
                ModelCapabilityScore(
                    model_id=profile.model_id,
                    skill_id=skill_id,
                    step_type=step_type,
                    capability_score=capability,
                    quality_score=capability,
                    cost_efficiency_score=0.9 if profile.provider_type == "local_ollama" else 0.45,
                    latency_score=0.7,
                    reliability_score=0.65,
                    privacy_score=0.95 if profile.provider_type == "local_ollama" else 0.35,
                    schema_following_score=0.65,
                    user_acceptance_score=0.5,
                    sample_count=0,
                )
            )
    return rows


def list_skill_registry() -> list[SkillRegistryItem]:
    base_rules = ["No external API unless explicitly enabled later.", "No uploaded file content is injected automatically."]
    return [
        _skill("requirement_analysis", "Requirement Analysis", "planning", ["local_ollama", "mock"], base_rules),
        _skill("privacy_redaction", "Privacy Redaction", "security", ["local_ollama", "mock"], base_rules),
        _skill("codex_instruction_generation", "Codex Instruction Generation", "code", ["local_ollama", "mock"], base_rules),
        _skill("code_development", "Code Development", "code", ["local_ollama", "remote_api", "mock"], base_rules),
        _skill("code_review_plan", "Code Review Plan", "code", ["local_ollama", "remote_api", "mock"], base_rules),
        _skill("architecture_analysis", "Architecture Analysis", "analysis", ["local_ollama", "remote_api", "mock"], base_rules),
        _skill("document_generation", "Document Generation", "writing", ["local_ollama", "remote_api", "mock"], base_rules),
        _skill("paper_writing", "Paper Writing", "writing", ["local_ollama", "remote_api", "mock"], base_rules),
        _skill("ppt_generation", "PPT Generation", "presentation", ["local_ollama", "remote_api", "desktop_tool", "mock"], base_rules, desktop=True),
        _skill("diagram_generation", "Diagram Generation", "diagram", ["local_ollama", "remote_api", "desktop_tool", "mock"], base_rules, desktop=True),
        _skill("desktop_tool_plan", "Desktop Tool Plan", "desktop", ["desktop_tool", "mock"], base_rules, desktop=True),
    ]


def list_skill_pipelines() -> list[SkillPipeline]:
    pipelines = [_pipeline_for_skill(item.skill_id, item.skill_name) for item in list_skill_registry()]
    return pipelines


def get_skill_pipeline(skill_id: str) -> SkillPipeline:
    for pipeline in list_skill_pipelines():
        if pipeline.skill_id == skill_id:
            return pipeline
    return _pipeline_for_skill("requirement_analysis", "Requirement Analysis")


def analyze_privacy(text: str) -> PrivacyGatewayResult:
    findings = scan_payload(text)
    redacted, redaction_findings = redact_query(text)
    all_findings = [*findings, *redaction_findings]
    finding_types = {item.type for item in all_findings}
    severe = {item.severity for item in all_findings}
    if severe & {"critical"} or {"api_key", "token"} & finding_types:
        level = "P4"
    elif severe & {"high"} or {"local_path", "url", "email"} & finding_types:
        level = "P3"
    elif finding_types:
        level = "P2"
    else:
        level = "P1" if len(text.strip()) > 0 else "P0"
    external_allowed = level in {"P0", "P1"}
    requires_redaction = level in {"P2", "P3", "P4"} or bool(redaction_findings)
    blocked_reasons = ["P4 content must stay local"] if level == "P4" else []
    return PrivacyGatewayResult(
        privacy_level=level,
        external_allowed=external_allowed,
        requires_redaction=requires_redaction,
        sanitized_prompt=redacted[:1200],
        redaction_notes=[f"{item.type}:{item.severity}" for item in all_findings[:12]],
        api_safe_context=redacted[:600] if external_allowed else "External API disabled for this privacy level.",
        local_only_context=not external_allowed,
        risk_level="high" if level == "P4" else "medium" if level in {"P2", "P3"} else "normal",
        execution_allowed=level != "P4",
        blocked_reasons=blocked_reasons,
    )


def select_skill(task_text: str) -> str:
    text = task_text.lower()
    if any(term in text for term in ["code", "python", "typescript", "fastapi", "react", "bug", "代码", "修复"]):
        return "code_development"
    if any(term in text for term in ["ppt", "powerpoint", "slide", "演示"]):
        return "ppt_generation"
    if any(term in text for term in ["paper", "论文", "experiment", "latex"]):
        return "paper_writing"
    if any(term in text for term in ["diagram", "mermaid", "visio", "流程图", "图"]):
        return "diagram_generation"
    if any(term in text for term in ["doc", "report", "文档", "报告"]):
        return "document_generation"
    return "requirement_analysis"


def recommend_models(
    *,
    selected_skill: str,
    privacy: PrivacyGatewayResult,
) -> list[ModelRoutingRecommendation]:
    pipeline = get_skill_pipeline(selected_skill)
    recommendations = []
    for step in pipeline.steps:
        routing = score_model_route(selected_skill=selected_skill, step=step, privacy=privacy)
        model = next((item for item in list_model_profiles() if item.model_id == routing.recommended_model_id), _pick_model(step, privacy))
        recommendations.append(
            ModelRoutingRecommendation(
                selected_skill=selected_skill,
                step_type=step.step_type,
                model_role=step.model_role,
                recommended_provider_type=model.provider_type,
                recommended_provider_id=model.provider_id,
                recommended_model=model.model_name,
                recommended_model_id=model.model_id,
                reason=f"{_route_reason(model, privacy, step)} {routing.reason}",
                cost_level=model.cost_level,
                historical_quality_score=0.0,
                latency_level=model.latency_level,
                final_score=routing.final_score,
                alternatives=[item.model_dump() for item in routing.alternatives],
            )
        )
    return recommendations


def score_model_route(
    *,
    selected_skill: str,
    step: SkillPipelineStep,
    privacy: PrivacyGatewayResult,
) -> "AdaptiveRoutingResult":
    from app.schemas.hybrid import AdaptiveRoutingResult

    scores = list_capability_scores()
    descriptors = {item.provider_id: item for item in list_provider_descriptors()}
    profile_scores: list[tuple[float, ModelProfile, str]] = []
    for profile in list_model_profiles():
        score = next(
            (
                item
                for item in scores
                if item.model_id == profile.model_id
                and (item.skill_id == selected_skill or item.step_type == step.step_type)
            ),
            None,
        )
        if score is None:
            score = ModelCapabilityScore(model_id=profile.model_id, skill_id=selected_skill, step_type=step.step_type)
        provider = descriptors.get(profile.provider_id)
        provider_enabled = bool(provider and provider.enabled)
        external_allowed = privacy.external_allowed
        if profile.provider_type == "remote_api" and not external_allowed:
            external_penalty = 0.25
        else:
            external_penalty = 1.0
        provider_factor = 1.0 if provider_enabled or profile.provider_type == "mock" else 0.75
        role_bonus = 0.08 if step.default_provider_type == profile.provider_type else 0.0
        final_score = (
            score.capability_score * 0.22
            + score.quality_score * 0.16
            + score.cost_efficiency_score * 0.12
            + score.latency_score * 0.1
            + score.reliability_score * 0.1
            + score.privacy_score * 0.14
            + score.schema_following_score * 0.1
            + score.user_acceptance_score * 0.06
            + role_bonus
        ) * provider_factor * external_penalty
        reason = (
            f"score={final_score:.2f}; capability={score.capability_score:.2f}; "
            f"privacy={score.privacy_score:.2f}; cost={score.cost_efficiency_score:.2f}; "
            f"provider_enabled={provider_enabled}; external_allowed={external_allowed}; step_type={step.step_type}"
        )
        profile_scores.append((round(final_score, 4), profile, reason))
    profile_scores.sort(key=lambda item: item[0], reverse=True)
    best_score, best_profile, best_reason = profile_scores[0]
    alternatives = [
        AdaptiveRoutingAlternative(
            model_id=profile.model_id,
            provider_id=profile.provider_id,
            provider_type=profile.provider_type,
            score=score,
            reason=reason,
        )
        for score, profile, reason in profile_scores[1:4]
    ]
    return AdaptiveRoutingResult(
        recommended_model_id=best_profile.model_id,
        recommended_provider_id=best_profile.provider_id,
        final_score=best_score,
        reason=best_reason,
        alternatives=alternatives,
    )


def build_task_contract_metadata(task_text: str, task_type: str | None = None) -> dict[str, object]:
    selected_skill = select_skill(f"{task_type or ''} {task_text}")
    pipeline = get_skill_pipeline(selected_skill)
    privacy = analyze_privacy(task_text)
    recommendations = recommend_models(selected_skill=selected_skill, privacy=privacy)
    requires_confirmation = privacy.requires_redaction or any(step.requires_user_confirmation for step in pipeline.steps)
    return {
        "selected_skill": selected_skill,
        "recommended_executor": "hybrid_local_controlled_pipeline",
        "pipeline_steps": [step.model_dump() for step in pipeline.steps],
        "model_roles": [step.model_role for step in pipeline.steps],
        "recommended_models": [item.model_dump() for item in recommendations],
        "privacy_level": privacy.privacy_level,
        "external_allowed": privacy.external_allowed,
        "requires_redaction": privacy.requires_redaction,
        "sanitized_prompt": privacy.sanitized_prompt,
        "redaction_notes": privacy.redaction_notes,
        "api_safe_context": privacy.api_safe_context,
        "local_only_context": privacy.local_only_context,
        "estimated_cost_level": _estimated_cost(recommendations),
        "requires_user_confirmation": requires_confirmation,
        "risk_level": privacy.risk_level,
        "execution_allowed": privacy.execution_allowed,
        "blocked_reasons": privacy.blocked_reasons,
    }


def architecture_state() -> HybridArchitectureState:
    return HybridArchitectureState(
        provider_types=PROVIDER_TYPES,
        provider_descriptors=list_provider_descriptors(),
        provider_fetch_strategies=list_provider_fetch_strategies(),
        provider_usage_snapshots=list_provider_usage_snapshots(),
        provider_cost_stats=list_provider_cost_stats(),
        provider_quota_windows=list_provider_quota_windows(),
        model_profiles=list_model_profiles(),
        capability_scores=list_capability_scores(),
        model_evaluation_logs=list_model_evaluation_logs(limit=20),
        skill_registry=list_skill_registry(),
        skill_pipelines=list_skill_pipelines(),
        skill_packages=list_skill_packages(),
        artifact_center=list_artifact_center(),
        desktop_tools=list_desktop_tools(),
    )


def list_model_evaluation_logs(limit: int = 50) -> list[ModelEvaluationLogView]:
    session = create_session()
    try:
        _ensure_mock_model_evaluation_logs(session)
        statement = select(ModelEvaluationLogRecord).order_by(ModelEvaluationLogRecord.created_at.desc()).limit(limit)
        return [_model_evaluation_log_view(record) for record in session.scalars(statement)]
    finally:
        session.close()


def list_desktop_tools() -> list[DesktopToolProfile]:
    names = ["VS Code", "PyCharm", "PowerPoint", "Visio", "Photoshop", "Python", "Git", "Browser", "File Manager"]
    return [
        DesktopToolProfile(
            tool_id=name.lower().replace(" ", "_"),
            name=name,
            installed=False,
            enabled=False,
            allowed_actions=[],
            forbidden_actions=["execute", "write_file", "delete_file", "network"],
            requires_user_confirmation=True,
        )
        for name in names
    ]


def list_skill_packages() -> list[SkillPackageMetadata]:
    packages: list[SkillPackageMetadata] = []
    if not SKILL_PACKAGE_ROOT.exists():
        return packages
    package_ids = sorted(
        path.name
        for path in SKILL_PACKAGE_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "_shared"
    )
    for package_id in package_ids:
        package_path = SKILL_PACKAGE_ROOT / package_id
        skill_md_path = package_path / "SKILL.md"
        manifest_path = package_path / "manifest.yaml"
        static_path = package_path / "static"
        references_path = package_path / "references"
        shared_path = package_path / "_shared"
        collection_shared_path = SKILL_PACKAGE_ROOT / "_shared"
        skill_text = _read_text_preview(skill_md_path, 1600)
        manifest_text = _read_text_preview(manifest_path, 1600)
        manifest = _parse_simple_manifest(manifest_text)
        packages.append(
            SkillPackageMetadata(
                package_id=package_id,
                name=str(manifest.get("name") or package_id.replace("-", " ").title()),
                path=str(package_path.relative_to(REPO_ROOT)),
                skill_md_found=skill_md_path.exists(),
                manifest_found=manifest_path.exists(),
                static_found=static_path.exists() and static_path.is_dir(),
                references_found=references_path.exists() and references_path.is_dir(),
                shared_found=(shared_path.exists() and shared_path.is_dir()) or (collection_shared_path.exists() and collection_shared_path.is_dir()),
                static_files=_list_relative_files(static_path, package_path, limit=12),
                reference_files=_list_relative_files(references_path, package_path, limit=12),
                manifest=manifest,
                description=str(manifest.get("description") or _first_non_heading_line(skill_text)),
                rules_preview=_truncate(skill_text, 500),
                allowed_tools_effective=[],
                scripts_enabled=False,
                load_status="loaded_readonly" if skill_md_path.exists() or manifest_path.exists() else "missing_placeholder",
                safety_notes=[
                    "Read-only metadata loader.",
                    "Scripts, Bash, WebSearch, MCP, allowed-tools, and file execution are disabled.",
                ],
            )
        )
    return packages


def list_artifact_center(project_id: str | None = None, conversation_id: str | None = None) -> list[ArtifactCenterItem]:
    now = utc_now()
    session = create_session()
    try:
        items: list[ArtifactCenterItem] = []
        task_statement = select(TaskContractRecord).order_by(TaskContractRecord.created_at.desc()).limit(20)
        deliverable_statement = select(AgentDeliverableRecord).order_by(AgentDeliverableRecord.created_at.desc()).limit(20)
        run_statement = select(AgentRunRecord).order_by(AgentRunRecord.created_at.desc()).limit(20)
        if project_id:
            task_statement = select(TaskContractRecord).where(TaskContractRecord.project_id == project_id).order_by(TaskContractRecord.created_at.desc()).limit(20)
            deliverable_statement = select(AgentDeliverableRecord).where(AgentDeliverableRecord.project_id == project_id).order_by(AgentDeliverableRecord.created_at.desc()).limit(20)
            run_statement = select(AgentRunRecord).where(AgentRunRecord.project_id == project_id).order_by(AgentRunRecord.created_at.desc()).limit(20)
        if conversation_id:
            task_statement = select(TaskContractRecord).where(TaskContractRecord.conversation_id == conversation_id).order_by(TaskContractRecord.created_at.desc()).limit(20)
            deliverable_statement = select(AgentDeliverableRecord).where(AgentDeliverableRecord.conversation_id == conversation_id).order_by(AgentDeliverableRecord.created_at.desc()).limit(20)
            run_statement = select(AgentRunRecord).where(AgentRunRecord.conversation_id == conversation_id).order_by(AgentRunRecord.created_at.desc()).limit(20)
        for task in session.scalars(task_statement):
            items.append(
                ArtifactCenterItem(
                    artifact_id=f"artifact-task-{task.id}",
                    project_id=task.project_id,
                    conversation_id=task.conversation_id,
                    artifact_type="task_contract",
                    title=task.title,
                    summary=f"Task contract status: {task.status}",
                    content_preview=_truncate(task.objective, 500),
                    status=task.status,
                    created_at=task.created_at,
                )
            )
        for run in session.scalars(run_statement):
            items.append(
                ArtifactCenterItem(
                    artifact_id=f"artifact-run-{run.id}",
                    project_id=run.project_id,
                    conversation_id=run.conversation_id,
                    agent_run_id=run.id,
                    artifact_type="agent_run",
                    title=f"Agent Run {run.status}",
                    summary=f"Run for task_contract={run.task_contract_id}; current_step_index={run.current_step_index}",
                    content_preview="Run monitor metadata only; no generated files are exposed.",
                    status=run.status,
                    created_at=run.created_at,
                )
            )
        for deliverable in session.scalars(deliverable_statement):
            items.append(
                ArtifactCenterItem(
                    artifact_id=f"artifact-deliverable-{deliverable.id}",
                    project_id=deliverable.project_id,
                    conversation_id=deliverable.conversation_id,
                    agent_run_id=None,
                    step_id=None,
                    artifact_type="agent_deliverable",
                    title=f"{deliverable.agent_name} Deliverable",
                    summary=_truncate(deliverable.summary, 500),
                    content_preview=_truncate(deliverable.artifacts_json, 500),
                    status=deliverable.status,
                    created_at=deliverable.created_at,
                )
            )
        if items:
            return sorted(items, key=lambda item: item.created_at, reverse=True)[:60]
    finally:
        session.close()
    return [
        ArtifactCenterItem(
            artifact_id="artifact-mock-codex-instruction",
            project_id=None,
            conversation_id=None,
            agent_run_id=None,
            step_id=None,
            artifact_type="codex_instruction",
            title="Mock Codex Instruction Plan",
            summary="Placeholder artifact describing future Codex task instructions; no file is generated.",
            content_preview="Generate structured instructions after user approval. Do not write files automatically.",
            file_path=None,
            status="mock_only",
            created_at=now,
        ),
        ArtifactCenterItem(
            artifact_id="artifact-mock-document-outline",
            project_id=None,
            conversation_id=None,
            agent_run_id=None,
            step_id=None,
            artifact_type="document_outline",
            title="Mock Document Outline",
            summary="Placeholder document outline artifact for future writing pipeline.",
            content_preview="Sections, acceptance criteria, review notes. No DOCX/PDF/PPT is parsed or generated.",
            file_path=None,
            status="mock_only",
            created_at=now,
        ),
        ArtifactCenterItem(
            artifact_id="artifact-mock-diagram-spec",
            project_id=None,
            conversation_id=None,
            agent_run_id=None,
            step_id=None,
            artifact_type="diagram_spec",
            title="Mock Diagram Spec",
            summary="Placeholder diagram specification for future controlled diagram workflow.",
            content_preview="Mermaid/Visio plan metadata only; no desktop tool execution.",
            file_path=None,
            status="mock_only",
            created_at=now,
        ),
    ]


def _skill(skill_id: str, name: str, task_type: str, providers: list[str], rules: list[str], *, desktop: bool = False) -> SkillRegistryItem:
    return SkillRegistryItem(
        skill_id=skill_id,
        skill_name=name,
        task_type=task_type,
        description=f"{name} skill placeholder for hybrid local-controlled routing.",
        input_schema={"type": "object", "required": ["objective"]},
        output_schema={"type": "object", "required": ["summary", "artifacts", "review"]},
        allowed_provider_types=providers,
        allow_remote_api="remote_api" in providers,
        allow_desktop_tool=desktop,
        requires_redaction=True,
        requires_user_confirmation=desktop,
        safety_rules=rules,
    )


def _pipeline_for_skill(skill_id: str, skill_name: str) -> SkillPipeline:
    if skill_id == "code_development":
        steps = [
            _step("local_requirement_analysis", "Local Requirement Analysis", "local_requirement_analysis", "local_requirement_analyzer", "local_ollama"),
            _step("architecture_planning", "Architecture Planning", "architecture_planning", "architecture_reasoner", "mock", depends=["local_requirement_analysis"]),
            _step("code_implementation", "Code Implementation", "code_implementation", "code_specialist", "mock", depends=["architecture_planning"], review=True),
            _step("code_review", "Code Review", "code_review", "reviewer", "mock", depends=["code_implementation"], review=True),
            _step("local_safety_check", "Local Safety Check", "local_safety_check", "local_safety_guard", "local_ollama", depends=["code_review"], confirm=True),
        ]
    elif skill_id in {"ppt_generation", "diagram_generation", "desktop_tool_plan"}:
        steps = [
            _step("local_requirement_analysis", "Local Requirement Analysis", "local_requirement_analysis", "local_requirement_analyzer", "local_ollama"),
            _step("structure_generation", "Structure Generation", "structure_generation", "structure_planner", "mock", depends=["local_requirement_analysis"]),
            _step("desktop_tool_plan", "Desktop Tool Plan", "desktop_tool_plan", "desktop_tool_planner", "desktop_tool", depends=["structure_generation"], confirm=True),
            _step("local_safety_check", "Local Safety Check", "local_safety_check", "local_safety_guard", "local_ollama", depends=["desktop_tool_plan"], confirm=True),
        ]
    else:
        steps = [
            _step("local_requirement_analysis", "Local Requirement Analysis", "local_requirement_analysis", "local_requirement_analyzer", "local_ollama"),
            _step("draft_generation", "Draft Generation", "draft_generation", "content_specialist", "mock", depends=["local_requirement_analysis"]),
            _step("review", "Review", "review", "reviewer", "mock", depends=["draft_generation"], review=True),
        ]
    return SkillPipeline(skill_id=skill_id, skill_name=skill_name, steps=steps)


def _step(
    step_id: str,
    name: str,
    step_type: str,
    role: str,
    provider_type: str,
    *,
    depends: list[str] | None = None,
    review: bool = False,
    confirm: bool = False,
) -> SkillPipelineStep:
    return SkillPipelineStep(
        step_id=step_id,
        step_name=name,
        step_type=step_type,
        model_role=role,
        depends_on=depends or [],
        allow_parallel=False,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        privacy_policy="local_only" if provider_type in {"local_ollama", "desktop_tool"} else "redacted_context_only",
        cost_limit="low" if provider_type == "local_ollama" else "medium",
        requires_review=review,
        requires_user_confirmation=confirm,
        default_provider_type=provider_type,
        candidate_model_roles=[role],
    )


def _pick_model(step: SkillPipelineStep, privacy: PrivacyGatewayResult) -> ModelProfile:
    profiles = list_model_profiles()
    if privacy.local_only_context or step.default_provider_type == "local_ollama":
        return next(item for item in profiles if item.model_id == "local_qwen3_8b")
    if step.model_role == "code_specialist":
        return next(item for item in profiles if item.model_id == "mock_claude_code_model")
    if "diagram" in step.step_type:
        return next(item for item in profiles if item.model_id == "mock_diagram_model")
    if "review" in step.step_type:
        return next(item for item in profiles if item.model_id == "mock_reviewer_model")
    return next(item for item in profiles if item.model_id == "mock_reasoning_model")


def _route_reason(model: ModelProfile, privacy: PrivacyGatewayResult, step: SkillPipelineStep) -> str:
    if model.provider_type == "local_ollama":
        return f"Local-first route for {privacy.privacy_level} privacy and {step.model_role}."
    return "Mock remote_api placeholder; no external call is enabled."


def _estimated_cost(recommendations: list[ModelRoutingRecommendation]) -> str:
    if any(item.cost_level == "high" for item in recommendations):
        return "medium_mock"
    return "low"


def _read_text_preview(path: Path, limit: int) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        resolved = path.resolve()
        if SKILL_PACKAGE_ROOT.resolve() not in resolved.parents and resolved != SKILL_PACKAGE_ROOT.resolve():
            return ""
        return path.read_text(encoding="utf-8")[:limit]
    except OSError:
        return ""


def _parse_simple_manifest(text: str) -> dict[str, object]:
    manifest: dict[str, object] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key in {"id", "name", "description", "version", "category", "status"}:
            manifest[key] = value
    return manifest


def _list_relative_files(path: Path, base_path: Path, *, limit: int) -> list[str]:
    if not path.exists() or not path.is_dir():
        return []
    try:
        root = SKILL_PACKAGE_ROOT.resolve()
        resolved = path.resolve()
        if root not in resolved.parents and resolved != root:
            return []
        files: list[str] = []
        for child in sorted(path.rglob("*")):
            if child.is_file():
                files.append(str(child.relative_to(base_path)).replace("\\", "/"))
            if len(files) >= limit:
                break
        return files
    except OSError:
        return []


def _first_non_heading_line(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("#").strip()
        if line:
            return line[:240]
    return ""


def _truncate(text: str, limit: int) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit].rstrip()


def _ensure_mock_model_evaluation_logs(session) -> None:
    existing = session.scalars(select(ModelEvaluationLogRecord).limit(1)).first()
    if existing is not None:
        return
    for model_id, skill_id, step_type, quality, schema_score, notes in [
        ("local_qwen3_8b", "requirement_analysis", "local_requirement_analysis", 0.72, 0.62, "Mock baseline for local requirement analysis."),
        ("local_qwen_coder_7b", "code_development", "code_implementation", 0.68, 0.58, "Mock baseline for local code-oriented planning."),
        ("mock_reviewer_model", "code_review_plan", "code_review", 0.55, 0.55, "Mock remote_api reviewer placeholder; no external call."),
    ]:
        create_record(
            session,
            ModelEvaluationLogRecord(
                invocation_id=None,
                model_id=model_id,
                skill_id=skill_id,
                step_type=step_type,
                reviewer_model_id="mock_reviewer_model",
                quality_score=quality,
                schema_score=schema_score,
                safety_score=0.9 if model_id.startswith("local_") else 0.45,
                cost_score=0.9 if model_id.startswith("local_") else 0.35,
                latency_score=0.65,
                user_accepted=False,
                final_used=model_id == "local_qwen3_8b",
                reviewer_notes=notes,
            ),
        )


def _model_evaluation_log_view(record: ModelEvaluationLogRecord) -> ModelEvaluationLogView:
    return ModelEvaluationLogView(
        id=record.id,
        invocation_id=record.invocation_id,
        model_id=record.model_id,
        skill_id=record.skill_id,
        step_type=record.step_type,
        reviewer_model_id=record.reviewer_model_id,
        quality_score=record.quality_score,
        schema_score=record.schema_score,
        safety_score=record.safety_score,
        cost_score=record.cost_score,
        latency_score=record.latency_score,
        user_accepted=record.user_accepted,
        final_used=record.final_used,
        reviewer_notes=record.reviewer_notes,
        created_at=record.created_at,
    )
