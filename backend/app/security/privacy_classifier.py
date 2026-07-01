from app.schemas.security import PayloadFinding


def classify_privacy(findings: list[PayloadFinding]) -> str:
    if any(item.severity == "critical" for item in findings):
        return "critical"
    if any(item.severity == "high" for item in findings):
        return "high"
    if any(item.severity == "medium" for item in findings):
        return "medium"
    if findings:
        return "low"
    return "normal"
