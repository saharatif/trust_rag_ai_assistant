# Database connection and lifecycle management.
# Handles SQLite for local development and PostgreSQL for production.

import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class Database:
    """Manages database connections and initialization."""

    def __init__(self, db_url: str = "sqlite:///trustrag.db"):
        """Initialize database connection.

        Args:
            db_url: Connection string. Default is local SQLite.
                   Format: "sqlite:///path/to/db.db" or
                   "postgresql://user:pass@host/dbname"
        """
        self.db_url = db_url
        self.connection: sqlite3.Connection | None = None

    async def connect(self) -> None:
        """Establish database connection and initialize schema."""
        if self.db_url.startswith("sqlite:"):
            # SQLite connection
            db_path = self.db_url.replace("sqlite:///", "")
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            await self._init_schema_sqlite()
            logger.info(f"Connected to SQLite database at {db_path}")

        elif self.db_url.startswith("postgresql"):
            # PostgreSQL connection — requires psycopg2 (not included for local dev)
            logger.error("PostgreSQL support requires psycopg2. Not yet implemented.")
            raise NotImplementedError("PostgreSQL support not yet implemented")

        else:
            raise ValueError(f"Unsupported database URL: {self.db_url}")

    async def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    async def _init_schema_sqlite(self) -> None:
        """Initialize SQLite schema from schema.sql."""
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            logger.error(f"Schema file not found at {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        schema_sql = schema_path.read_text()

        cursor = self.connection.cursor()
        cursor.executescript(schema_sql)
        self.connection.commit()

        logger.info("Database schema initialized")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return the cursor."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor

    def execute_many(self, query: str, params_list: list[tuple]) -> None:
        """Execute a query multiple times with different parameters."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        self.connection.commit()

    def execute_one(self, query: str, params: tuple = ()) -> dict | None:
        """Execute a query and return a single row as a dict."""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def execute_all(self, query: str, params: tuple = ()) -> list[dict]:
        """Execute a query and return all rows as dicts."""
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def commit(self) -> None:
        """Commit pending transactions."""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """Rollback pending transactions."""
        if self.connection:
            self.connection.rollback()


# Global database instance
_db: Database | None = None


async def init_db(db_url: str = "sqlite:///trustrag.db") -> Database:
    """Initialize the global database instance."""
    global _db
    _db = Database(db_url)
    await _db.connect()
    return _db


def get_db() -> Database:
    """Get the current database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


@asynccontextmanager
async def db_context() -> AsyncGenerator[Database, None]:
    """Context manager for database operations."""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
