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
        ("skill-requirement-analysis", "Requirement Analysis Skill", "writing", "Build requirement confirmation cards and identify missing information.", "Confirm objective, inputs, outputs, constraints, and acceptance criteria before execution."),
        ("skill-planning", "Planning Skill", "others", "Split a task into small reviewable steps.", "Steps must be pausable, auditable, and safe by default."),
        ("skill-writing", "Writing Skill", "writing", "Create structured prose for local-only workflows.", "Do not invent citations or sources; mark uncertain content for user review."),
        ("skill-coding", "Coding Skill", "code", "Draft coding plans, patches, and test notes.", "Do not modify files unless the user requests it; explain scope, tests, and risk."),
        ("skill-research-summary", "Research Summary Skill", "research", "Summarize user-provided research context without web search.", "No external search or MCP; clearly separate provided facts from assumptions."),
        ("skill-document-helper", "Document Helper Skill", "writing", "Prepare document outlines, checklists, and formatting plans.", "Metadata-only helper; do not parse uploaded files automatically."),
        ("skill-drawing-prompt", "Drawing Prompt Skill", "drawing", "Draft visual prompts and figure planning notes.", "Do not call external image or design tools from the backend."),
        ("skill-research-verification", "Research Verification Skill", "research", "Track local evidence and verification gaps.", "Web Search and MCP remain disabled unless future explicit approval is implemented."),
        ("skill-formatting", "Formatting Skill", "others", "Organize output structure and formatting.", "Keep headings, lists, and tables concise and consistent."),
        ("skill-review", "Review Skill", "others", "Check completeness, safety, and acceptance criteria.", "Report missing items, risks, and concrete next actions."),
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
