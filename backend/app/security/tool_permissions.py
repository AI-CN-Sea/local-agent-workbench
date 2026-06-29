HIGH_RISK_TOOLS = {
    "external_api",
    "web_search",
    "mcp",
    "file_read",
    "file_write",
    "file_delete",
    "shell",
    "python_exec",
    "code_modify",
    "email_send",
    "github_write",
    "zotero_write",
    "ppt_edit",
    "vscode_control",
}

TOOL_RISK_EXPLANATIONS = {
    "external_api": "External API calls can leak private prompts, files, or project data.",
    "web_search": "Web search can disclose queries and introduce untrusted remote content.",
    "mcp": "MCP tools may access external systems or perform privileged actions.",
    "file_read": "File reads can expose local project or user data.",
    "file_write": "File writes can modify project state.",
    "file_delete": "File deletes can destroy user data.",
    "shell": "Shell execution can run arbitrary local commands.",
    "python_exec": "Python execution can access files, network, or process state.",
    "code_modify": "Code modification changes project behavior and may introduce unsafe logic.",
    "email_send": "Email sending can exfiltrate data to third parties.",
    "github_write": "GitHub write operations can publish or alter repository content.",
    "zotero_write": "Zotero write operations can modify research libraries.",
    "ppt_edit": "Presentation editing can alter user documents.",
    "vscode_control": "Editor control can modify files or execute actions in the user workspace.",
}


def is_high_risk_tool(tool_name: str) -> bool:
    return tool_name.strip().lower() in HIGH_RISK_TOOLS


def requires_user_approval(tool_name: str) -> bool:
    return is_high_risk_tool(tool_name)


def explain_tool_risk(tool_name: str) -> str:
    normalized = tool_name.strip().lower()
    if normalized in TOOL_RISK_EXPLANATIONS:
        return TOOL_RISK_EXPLANATIONS[normalized]
    return "This tool is not currently classified as high risk by the local permission model."
