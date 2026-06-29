from app.security.query_redactor import redact_query


def sanitize_log_message(message: str) -> str:
    redacted, _ = redact_query(message)
    return redacted
