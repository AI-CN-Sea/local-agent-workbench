from app.schemas.workbench import SkillInfo


def list_skills() -> list[SkillInfo]:
    return [
        SkillInfo(
            id="skill-requirement-analysis",
            name="需求分析",
            enabled=True,
            description="将用户输入整理为可确认的需求卡片。",
        ),
        SkillInfo(
            id="skill-outline-builder",
            name="大纲生成",
            enabled=True,
            description="生成任务执行大纲和审核点。",
        ),
        SkillInfo(
            id="skill-web-search",
            name="联网搜索",
            enabled=False,
            description="预留 Skill，当前不会执行真实联网搜索。",
        ),
    ]


def get_current_skill() -> SkillInfo:
    return list_skills()[0]
