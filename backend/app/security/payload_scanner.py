import re

from app.schemas.security import PayloadFinding

MAX_CONTINUOUS_TEXT_LENGTH = 800

PATTERNS: list[tuple[str, str, str, str, re.Pattern[str]]] = [
    (
        "api_key",
        "API Key",
        "critical",
        "移除密钥，并改用本地环境变量或安全凭据管理。",
        re.compile(r"(?i)\b(?:api[_-]?key|apikey|secret[_-]?key)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})"),
    ),
    (
        "token",
        "Token",
        "high",
        "移除 token，避免进入日志、记忆或模型上下文。",
        re.compile(r"(?i)\b(?:token|access[_-]?token|bearer)\b\s*[:= ]\s*['\"]?([A-Za-z0-9._\-]{20,})"),
    ),
    (
        "email",
        "邮箱",
        "medium",
        "确认是否需要保留邮箱；如非必要请脱敏。",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ),
    (
        "local_path",
        "本地路径",
        "medium",
        "避免暴露完整本地路径，可改为相对路径或文件名。",
        re.compile(r"(?i)(?:[A-Z]:\\(?:[^\\/:*?\"<>|\s\r\n]+\\?)+|/(?:Users|home|tmp|var|etc)/[^\s]+)"),
    ),
    (
        "url",
        "URL",
        "medium",
        "确认 URL 是否允许出现在请求中；当前系统不执行真实联网。",
        re.compile(r"https?://[^\s)>\"]+"),
    ),
    (
        "paper_experiment_result",
        "疑似论文实验结果",
        "medium",
        "确认实验结果是否已公开，必要时只保留统计摘要。",
        re.compile(
            r"(?i)(?:accuracy|f1|auc|bleu|rouge|loss|precision|recall|实验|准确率|召回率|消融|ablation)"
            r".{0,40}(?:\d{1,3}(?:\.\d+)?%?|\d+\.\d+)"
        ),
    ),
    (
        "unpublished_project_name",
        "疑似未公开项目名",
        "medium",
        "确认项目代号是否可公开；如不可公开请替换为泛化描述。",
        re.compile(r"(?i)(?:codename|internal project|confidential project|未公开项目|内部项目|项目代号)[:：\s]+[\w\-\u4e00-\u9fff]{2,40}"),
    ),
]


def scan_payload(text: str) -> list[PayloadFinding]:
    findings: list[PayloadFinding] = []

    for finding_type, label, severity, recommendation, pattern in PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1) if match.lastindex else match.group(0)
            findings.append(
                PayloadFinding(
                    type=finding_type,
                    label=label,
                    value=value,
                    start=match.start(),
                    end=match.end(),
                    severity=severity,
                    recommendation=recommendation,
                )
            )

    findings.extend(_find_long_continuous_text(text))
    return sorted(findings, key=lambda item: (item.start, item.end))


def _find_long_continuous_text(text: str) -> list[PayloadFinding]:
    findings: list[PayloadFinding] = []
    for match in re.finditer(r"\S{%d,}" % MAX_CONTINUOUS_TEXT_LENGTH, text):
        findings.append(
            PayloadFinding(
                type="long_continuous_text",
                label="过长连续文本",
                value=match.group(0)[:80],
                start=match.start(),
                end=match.end(),
                severity="low",
                recommendation="拆分过长连续文本，避免影响上下文窗口和日志可读性。",
            )
        )
    return findings
