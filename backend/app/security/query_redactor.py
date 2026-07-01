from app.security.payload_scanner import scan_payload


def redact_query(text: str) -> tuple[str, list]:
    findings = scan_payload(text)
    parts: list[str] = []
    cursor = 0

    for finding in sorted(findings, key=lambda item: (item.start, item.end)):
        if finding.start < cursor:
            continue
        replacement = f"[REDACTED:{finding.type}]"
        parts.append(text[cursor : finding.start])
        parts.append(replacement)
        cursor = finding.end

    parts.append(text[cursor:])
    return "".join(parts), findings
