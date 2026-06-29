from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.database.models import Base


def _sqlite_path_from_url(database_url: str) -> Path:
    if database_url.startswith("sqlite:///./"):
        return Path(database_url.removeprefix("sqlite:///"))
    if database_url.startswith("sqlite:///"):
        return Path(database_url.removeprefix("sqlite:///"))
    return Path("local_agent_workbench.db")


DATABASE_PATH = _sqlite_path_from_url(settings.database_url)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def get_session() -> Generator[Session, None, None]:
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_session() -> Session:
    init_db()
    return SessionLocal()


def _ensure_sqlite_columns() -> None:
    migrations = {
        "skills": [
            ("category", "VARCHAR(40) DEFAULT 'others' NOT NULL"),
            ("rules", "TEXT DEFAULT '' NOT NULL"),
            ("status", "VARCHAR(40) DEFAULT 'draft' NOT NULL"),
            ("updated_at", "DATETIME"),
        ],
        "memory_items": [
            ("status", "VARCHAR(40) DEFAULT 'pending' NOT NULL"),
            ("updated_at", "DATETIME"),
        ],
        "task_contracts": [
            ("task_steps_json", "TEXT DEFAULT '[]' NOT NULL"),
            ("metadata_json", "TEXT DEFAULT '{}' NOT NULL"),
        ],
        "agent_steps": [
            ("requires_user_approval", "BOOLEAN DEFAULT 0 NOT NULL"),
            ("execution_metadata_json", "TEXT DEFAULT '{}' NOT NULL"),
            ("pipeline_step_id", "TEXT"),
            ("step_name", "TEXT"),
            ("step_type", "TEXT"),
            ("model_role", "TEXT"),
            ("selected_provider_id", "TEXT"),
            ("selected_model_id", "TEXT"),
            ("cost_estimate", "TEXT"),
            ("latency_ms", "INTEGER"),
            ("quality_score", "INTEGER"),
            ("started_at", "DATETIME"),
            ("finished_at", "DATETIME"),
        ],
        "agent_runs": [
            ("model_provider_id", "TEXT"),
            ("model_name", "TEXT"),
        ],
        "model_invocation_logs": [
            ("model_id", "TEXT"),
            ("skill_id", "TEXT"),
            ("step_id", "TEXT"),
            ("pipeline_step_id", "TEXT"),
            ("provider_type", "TEXT"),
            ("input_tokens", "INTEGER DEFAULT 0 NOT NULL"),
            ("output_tokens", "INTEGER DEFAULT 0 NOT NULL"),
            ("estimated_cost", "FLOAT DEFAULT 0.0 NOT NULL"),
            ("latency_ms", "INTEGER"),
            ("success", "BOOLEAN DEFAULT 0 NOT NULL"),
            ("error_code", "TEXT"),
            ("retry_count", "INTEGER DEFAULT 0 NOT NULL"),
            ("schema_valid", "BOOLEAN DEFAULT 0 NOT NULL"),
            ("sanitized_input_hash", "TEXT"),
            ("output_hash", "TEXT"),
            ("blocked_reason", "TEXT"),
        ],
    }

    with engine.begin() as connection:
        for table_name, columns in migrations.items():
            existing = {
                row[1]
                for row in connection.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
            }
            for column_name, ddl in columns:
                if column_name not in existing:
                    connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")
        connection.exec_driver_sql("UPDATE skills SET updated_at = created_at WHERE updated_at IS NULL")
        connection.exec_driver_sql("UPDATE memory_items SET updated_at = created_at WHERE updated_at IS NULL")
        _seed_default_skills(connection)


def _seed_default_skills(connection) -> None:
    default_skills = [
        ("skill-requirement-analysis", "Requirement Analysis Skill", "writing", "整理需求确认卡片和缺失信息。", "先确认目标、输入、输出、约束和验收标准；不确定处标记为待确认。"),
        ("skill-planning", "Planning Skill", "others", "把任务拆为可审核步骤。", "步骤必须小、可暂停、可审核；高风险动作需要用户确认。"),
        ("skill-writing", "Writing Skill", "writing", "生成结构化中文或英文内容。", "先确认读者和格式；不得编造引用；不确定处标记为待确认。"),
        ("skill-coding", "Coding Skill", "code", "生成代码建议或补丁说明。", "默认不直接写文件；说明影响范围、测试和风险。"),
        ("skill-drawing-prompt", "Drawing Prompt Skill", "drawing", "生成绘图或视觉提示词。", "只生成本地可审查提示，不调用外部绘图工具。"),
        ("skill-research-verification", "Research Verification Skill", "research", "整理本地资料和待验证点。", "Web Search 和 MCP 默认关闭；不得伪造来源。"),
        ("skill-formatting", "Formatting Skill", "others", "整理输出结构和格式。", "保持标题、列表、表格简洁一致，避免过度格式化。"),
        ("skill-review", "Review Skill", "others", "检查完整性、安全和验收标准。", "逐项检查约束、风险和未完成项，输出明确结论。"),
    ]
    now_sql = "CURRENT_TIMESTAMP"
    for skill_id, name, category, description, rules in default_skills:
        exists = connection.exec_driver_sql("SELECT 1 FROM skills WHERE id = ?", (skill_id,)).fetchone()
        if exists:
            continue
        connection.exec_driver_sql(
            """
            INSERT INTO skills
            (id, name, category, description, rules, status, enabled, permissions_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', 1, '["model_invoke"]', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (skill_id, name, category, description, rules),
        )
