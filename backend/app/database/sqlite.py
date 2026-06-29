from pathlib import Path
from sqlite3 import Connection, connect

DATABASE_FILE = Path("local_agent_workbench.db")


def get_connection() -> Connection:
    """Return a SQLite connection for future repositories."""
    return connect(DATABASE_FILE)
