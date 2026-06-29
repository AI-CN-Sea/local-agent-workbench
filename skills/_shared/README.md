# Shared Skill Layer

This directory is reserved for reusable skill fragments, policies, schemas, and style guides.

Current safety boundary:

- Metadata may be loaded by SkillRegistry.
- No scripts are executed.
- No external API, Web Search, MCP, shell, desktop tool, or uploaded file parsing is enabled.
- Uploaded file contents must not be written into prompts, memory, skills, or logs.
