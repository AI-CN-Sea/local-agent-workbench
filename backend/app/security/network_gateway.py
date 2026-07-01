from app.schemas.security import NetworkAuditLog


def mock_network_request(action: str, destination: str) -> NetworkAuditLog:
    return NetworkAuditLog(
        action=action,
        destination=destination,
        allowed=False,
        reason="mock network gateway: real network calls are disabled.",
    )
