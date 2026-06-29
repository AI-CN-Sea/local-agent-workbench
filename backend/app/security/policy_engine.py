from app.schemas.security import (
    NetworkAuditLog,
    ReviewResult,
    SecurityPolicy,
    SecurityRequest,
)


def list_security_policies() -> list[SecurityPolicy]:
    return [
        SecurityPolicy(
            id="policy-no-real-network",
            name="禁止真实联网",
            description="当前版本所有网络请求只能走 mock 网关，不允许访问外部服务。",
        ),
        SecurityPolicy(
            id="policy-no-model-provider",
            name="禁止外部模型 API",
            description="本机 Ollama 只能通过 Model Gateway 白名单和安全审查调用。",
        ),
        SecurityPolicy(
            id="policy-sensitive-payload-scan",
            name="敏感载荷扫描",
            description="进入工具、记忆或模型上下文前先扫描 API Key、token、邮箱、路径和 URL。",
        ),
        SecurityPolicy(
            id="policy-user-approval",
            name="敏感操作需确认",
            description="高风险请求默认进入 pending 状态，等待用户显式确认。",
        ),
    ]


def evaluate_security_request(request: SecurityRequest) -> tuple[ReviewResult, NetworkAuditLog]:
    approved = False
    findings = [
        "当前安全策略只允许 mock 响应。",
        "外部联网、外部模型 API、MCP 调用均未启用；本机模型只能走 Model Gateway。",
    ]

    decision = ReviewResult(
        target_id=request.id,
        reviewer="policy-engine",
        approved=approved,
        severity="info",
        findings=findings,
        recommendations=["如需启用真实外部能力，应先增加审批、审计和配置隔离。"],
    )
    audit_log = NetworkAuditLog(
        project_id=request.project_id,
        action=request.action,
        destination=request.resource or "mock://local-security-policy",
        allowed=False,
        reason="network_gateway 当前只允许 mock，不执行真实联网。",
    )
    return decision, audit_log
