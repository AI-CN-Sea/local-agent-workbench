from app.schemas.security import (
    PayloadScanRequest,
    PayloadScanResponse,
    RedactRequest,
    RedactResponse,
    NetworkAuditLog,
    NetworkAuditLogCreate,
    SecurityPolicy,
    SecurityRequest,
    SecurityRequestResponse,
)
from app.database.service import create_network_audit_log, create_security_request_record, create_session
from app.schemas.workbench import SecurityNotice
from app.security.payload_scanner import scan_payload
from app.security.policy_engine import evaluate_security_request, list_security_policies
from app.security.privacy_classifier import classify_privacy
from app.security.query_redactor import redact_query


def get_security_notice() -> SecurityNotice:
    return SecurityNotice(
        level="info",
        message="默认不调用模型；仅允许经 Model Gateway 审查后的本机 Ollama 受控调用。",
        checks=[
            "外部 API：关闭",
            "网页搜索：关闭",
            "MCP：关闭",
            "本机模型：仅限白名单 localhost endpoint",
        ],
    )


def get_policies() -> list[SecurityPolicy]:
    return list_security_policies()


def scan_security_payload(request: PayloadScanRequest) -> PayloadScanResponse:
    findings = scan_payload(request.text)
    sensitivity = classify_privacy(findings)
    recommendations = sorted({item.recommendation for item in findings})
    return PayloadScanResponse(
        safe=sensitivity in {"normal", "low"},
        sensitivity=sensitivity,
        findings=findings,
        recommendations=recommendations,
    )


def redact_security_payload(request: RedactRequest) -> RedactResponse:
    redacted_text, findings = redact_query(request.text)
    return RedactResponse(redacted_text=redacted_text, findings=findings)


def create_security_request(request: SecurityRequest) -> SecurityRequestResponse:
    decision, audit_log = evaluate_security_request(request)
    session = create_session()
    try:
        create_security_request_record(
            session,
            project_id=request.project_id,
            action=request.action,
            reason=request.reason,
            resource=request.resource,
            payload_preview=request.payload_preview,
        )
        create_network_audit_log(
            session,
            project_id=audit_log.project_id,
            action=audit_log.action,
            destination=audit_log.destination,
            reason=audit_log.reason,
        )
    finally:
        session.close()
    return SecurityRequestResponse(
        request=request,
        decision=decision,
        audit_log=audit_log,
    )


def write_network_audit(request: NetworkAuditLogCreate) -> NetworkAuditLog:
    audit_log = NetworkAuditLog(
        project_id=request.project_id,
        action=request.action,
        destination=request.destination,
        allowed=False,
        reason=request.reason,
        mode="mock",
    )
    session = create_session()
    try:
        record = create_network_audit_log(
            session,
            project_id=audit_log.project_id,
            action=audit_log.action,
            destination=audit_log.destination,
            reason=audit_log.reason,
        )
    finally:
        session.close()

    return NetworkAuditLog(
        id=record.id,
        project_id=record.project_id,
        action=record.action,
        destination=record.destination,
        allowed=record.allowed,
        reason=record.reason,
        mode=record.mode,
        created_at=record.created_at,
    )
