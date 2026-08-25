"""
Antordrishti — SQLite Database Service
Persistent storage for cases, evidence items, recent files, and workspace state.
"""

import os
import sqlite3
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger("antordrishti")

# Default database location
_DB_DIR = os.path.join(os.path.expanduser("~"), ".antordrishti")
_DB_PATH = os.path.join(_DB_DIR, "antordrishti.db")


def _get_connection(db_path: str = _DB_PATH) -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


class DatabaseService:
    """SQLite-backed persistence for Antordrishti."""

    def __init__(self, db_path: str = _DB_PATH):
        self._db_path = db_path
        self._conn = _get_connection(db_path)
        self._init_schema()
        logger.info(f"Database initialized: {db_path}")

    def _init_schema(self):
        """Create tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                examiner TEXT NOT NULL DEFAULT '',
                organization TEXT DEFAULT '',
                description TEXT DEFAULT '',
                reference_number TEXT DEFAULT '',
                date TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'Open',
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evidence_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                evidence_type TEXT DEFAULT 'Original Evidence',
                source TEXT DEFAULT '',
                file_path TEXT DEFAULT '',
                sha256 TEXT DEFAULT '',
                md5 TEXT DEFAULT '',
                status TEXT DEFAULT 'Pending',
                notes TEXT DEFAULT '',
                reviewed INTEGER DEFAULT 0,
                relevant INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recent_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL DEFAULT '',
                file_type TEXT DEFAULT '',
                opened_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workspace_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence_items(case_id);
            CREATE INDEX IF NOT EXISTS idx_recent_opened ON recent_files(opened_at DESC);
        """)
        self._conn.commit()

    # ── Case Operations ──────────────────────────────────────

    def create_case(self, case_data: Dict[str, Any]) -> bool:
        """Insert a new case. Returns True on success."""
        try:
            now = datetime.now().isoformat()
            self._conn.execute(
                """INSERT INTO cases
                   (case_id, title, examiner, organization, description,
                    reference_number, date, notes, status, created_at, modified_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    case_data.get("case_id", ""),
                    case_data.get("title", ""),
                    case_data.get("examiner_name", ""),
                    case_data.get("organization", ""),
                    case_data.get("description", ""),
                    case_data.get("reference_number", ""),
                    case_data.get("date", ""),
                    case_data.get("notes", ""),
                    case_data.get("status", "Open"),
                    now, now
                )
            )
            self._conn.commit()
            logger.info(f"Case created in DB: {case_data.get('case_id')}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Case ID already exists: {case_data.get('case_id')}")
            return False
        except Exception as e:
            logger.error(f"Error creating case: {e}")
            return False

    def get_cases(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all cases, optionally filtered by status."""
        try:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM cases WHERE status = ? ORDER BY modified_at DESC",
                    (status,)
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM cases ORDER BY modified_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching cases: {e}")
            return []

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single case by case_id."""
        try:
            row = self._conn.execute(
                "SELECT * FROM cases WHERE case_id = ?", (case_id,)
            ).fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching case {case_id}: {e}")
            return None

    def update_case(self, case_id: str, updates: Dict[str, Any]) -> bool:
        """Update a case's fields."""
        try:
            allowed = {"title", "examiner", "organization", "description",
                       "reference_number", "date", "notes", "status"}
            filtered = {k: v for k, v in updates.items() if k in allowed}
            if not filtered:
                return False

            filtered["modified_at"] = datetime.now().isoformat()
            set_clause = ", ".join(f"{k} = ?" for k in filtered)
            values = list(filtered.values()) + [case_id]

            self._conn.execute(
                f"UPDATE cases SET {set_clause} WHERE case_id = ?", values
            )
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {e}")
            return False

    def delete_case(self, case_id: str) -> bool:
        """Delete a case and its evidence items."""
        try:
            self._conn.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))
            self._conn.commit()
            logger.info(f"Case deleted: {case_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting case {case_id}: {e}")
            return False

    def get_case_count(self) -> int:
        """Return total number of cases."""
        try:
            row = self._conn.execute("SELECT COUNT(*) FROM cases").fetchone()
            return row[0] if row else 0
        except Exception:
            return 0

    def generate_case_id(self) -> str:
        """Auto-generate a Case ID in format CASE-YYYY-NNN."""
        year = datetime.now().strftime("%Y")
        count = self.get_case_count() + 1
        return f"CASE-{year}-{count:03d}"

    # ── Evidence Operations ──────────────────────────────────

    def add_evidence(self, evidence_data: Dict[str, Any]) -> bool:
        """Insert an evidence item."""
        try:
            now = datetime.now().isoformat()
            self._conn.execute(
                """INSERT INTO evidence_items
                   (case_id, evidence_id, name, evidence_type, source,
                    file_path, sha256, md5, status, notes, reviewed, relevant, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evidence_data.get("case_id", ""),
                    evidence_data.get("evidence_id", ""),
                    evidence_data.get("name", ""),
                    evidence_data.get("evidence_type", "Original Evidence"),
                    evidence_data.get("source", ""),
                    evidence_data.get("file_path", ""),
                    evidence_data.get("sha256", ""),
                    evidence_data.get("md5", ""),
                    evidence_data.get("status", "Pending"),
                    evidence_data.get("notes", ""),
                    1 if evidence_data.get("reviewed") else 0,
                    1 if evidence_data.get("relevant") else 0,
                    now
                )
            )
            self._conn.commit()
            logger.info(f"Evidence added: {evidence_data.get('evidence_id')}")
            return True
        except Exception as e:
            logger.error(f"Error adding evidence: {e}")
            return False

    def get_evidence_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieve all evidence items for a case."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM evidence_items WHERE case_id = ? ORDER BY created_at",
                (case_id,)
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching evidence for {case_id}: {e}")
            return []

    def get_evidence_count_for_case(self, case_id: str) -> int:
        """Return evidence count for a case."""
        try:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM evidence_items WHERE case_id = ?",
                (case_id,)
            ).fetchone()
            return row[0] if row else 0
        except Exception:
            return 0

    def generate_evidence_id(self, case_id: str) -> str:
        """Auto-generate evidence ID: EVD-001, EVD-002, etc."""
        count = self.get_evidence_count_for_case(case_id) + 1
        return f"EVD-{count:03d}"

    def update_evidence(self, evidence_id: str, case_id: str,
                        updates: Dict[str, Any]) -> bool:
        """Update an evidence item's fields."""
        try:
            allowed = {"name", "evidence_type", "source", "status",
                       "notes", "reviewed", "relevant", "sha256", "md5"}
            filtered = {k: v for k, v in updates.items() if k in allowed}
            if not filtered:
                return False

            set_clause = ", ".join(f"{k} = ?" for k in filtered)
            values = list(filtered.values()) + [evidence_id, case_id]

            self._conn.execute(
                f"UPDATE evidence_items SET {set_clause} "
                f"WHERE evidence_id = ? AND case_id = ?",
                values
            )
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating evidence {evidence_id}: {e}")
            return False

    def delete_evidence(self, evidence_id: str, case_id: str) -> bool:
        """Delete an evidence item."""
        try:
            self._conn.execute(
                "DELETE FROM evidence_items WHERE evidence_id = ? AND case_id = ?",
                (evidence_id, case_id)
            )
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting evidence {evidence_id}: {e}")
            return False

    # ── Recent Files ─────────────────────────────────────────

    def add_recent_file(self, file_path: str, file_name: str = "",
                        file_type: str = "") -> bool:
        """Track a recently opened file. Maintains max 20 entries."""
        try:
            now = datetime.now().isoformat()
            if not file_name:
                file_name = os.path.basename(file_path)

            # Remove duplicate if exists
            self._conn.execute(
                "DELETE FROM recent_files WHERE file_path = ?", (file_path,)
            )

            self._conn.execute(
                """INSERT INTO recent_files (file_path, file_name, file_type, opened_at)
                   VALUES (?, ?, ?, ?)""",
                (file_path, file_name, file_type, now)
            )

            # Keep only last 20
            self._conn.execute(
                """DELETE FROM recent_files WHERE id NOT IN
                   (SELECT id FROM recent_files ORDER BY opened_at DESC LIMIT 20)"""
            )
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding recent file: {e}")
            return False

    def get_recent_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent files ordered by most recent first."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM recent_files ORDER BY opened_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching recent files: {e}")
            return []

    def clear_recent_files(self) -> bool:
        """Clear all recent file entries."""
        try:
            self._conn.execute("DELETE FROM recent_files")
            self._conn.commit()
            return True
        except Exception:
            return False

    # ── Workspace State ──────────────────────────────────────

    def save_workspace_state(self, key: str, value: Any) -> bool:
        """Save a workspace state key-value pair. Value is JSON-serialized."""
        try:
            json_val = json.dumps(value) if not isinstance(value, str) else value
            self._conn.execute(
                """INSERT INTO workspace_state (key, value)
                   VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET value = ?""",
                (key, json_val, json_val)
            )
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving workspace state '{key}': {e}")
            return False

    def load_workspace_state(self, key: str, default: Any = None) -> Any:
        """Load a workspace state value by key. Returns parsed JSON or default."""
        try:
            row = self._conn.execute(
                "SELECT value FROM workspace_state WHERE key = ?", (key,)
            ).fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    return row[0]
            return default
        except Exception as e:
            logger.error(f"Error loading workspace state '{key}': {e}")
            return default

    def clear_workspace_state(self) -> bool:
        """Clear all workspace state."""
        try:
            self._conn.execute("DELETE FROM workspace_state")
            self._conn.commit()
            return True
        except Exception:
            return False

    # ── Cleanup ───────────────────────────────────────────────

    def close(self):
        """Close the database connection."""
        try:
            self._conn.close()
            logger.info("Database connection closed.")
        except Exception:
            pass


# ── Module-level singleton ───────────────────────────────────

_instance: Optional[DatabaseService] = None


def get_db() -> DatabaseService:
    """Get the global DatabaseService singleton."""
    global _instance
    if _instance is None:
        _instance = DatabaseService()
    return _instance
