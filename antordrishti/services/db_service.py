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
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            );
            
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
                imported_at TEXT DEFAULT '',
                file_type TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ocr_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_id TEXT NOT NULL,
                case_id TEXT NOT NULL DEFAULT '',
                page_number INTEGER NOT NULL DEFAULT 1,
                detected_language TEXT DEFAULT '',
                language_confidence REAL DEFAULT 0,
                detected_script TEXT DEFAULT '',
                script_confidence REAL DEFAULT 0,
                ocr_confidence REAL DEFAULT 0,
                ocr_quality TEXT DEFAULT '',
                extracted_text TEXT DEFAULT '',
                raw_text TEXT DEFAULT '',
                normalized_text TEXT DEFAULT '',
                ocr_engine TEXT DEFAULT '',
                model TEXT DEFAULT '',
                processing_time REAL DEFAULT 0,
                preprocessing_info TEXT DEFAULT '',
                integrity_snapshot TEXT DEFAULT '',
                examination_started TEXT DEFAULT '',
                examination_completed TEXT DEFAULT '',
                ocr_provenance TEXT DEFAULT '',
                processed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ocr_regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ocr_result_id INTEGER NOT NULL,
                page_number INTEGER DEFAULT 1,
                region_id TEXT DEFAULT '',
                box_x INTEGER DEFAULT 0,
                box_y INTEGER DEFAULT 0,
                box_w INTEGER DEFAULT 0,
                box_h INTEGER DEFAULT 0,
                text TEXT DEFAULT '',
                confidence REAL DEFAULT 0,
                engine TEXT DEFAULT '',
                FOREIGN KEY (ocr_result_id) REFERENCES ocr_results(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ocr_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ocr_result_id INTEGER NOT NULL,
                evidence_id TEXT DEFAULT '',
                case_id TEXT DEFAULT '',
                engine TEXT DEFAULT '',
                language_model TEXT DEFAULT '',
                preprocessing_variant TEXT DEFAULT '',
                preprocessing_config TEXT DEFAULT '',
                confidence REAL DEFAULT 0,
                text TEXT DEFAULT '',
                processing_time REAL DEFAULT 0,
                status TEXT DEFAULT '',
                started_at TEXT DEFAULT '',
                completed_at TEXT DEFAULT '',
                integrity_sha256 TEXT DEFAULT '',
                FOREIGN KEY (ocr_result_id) REFERENCES ocr_results(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS processing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_id TEXT NOT NULL,
                case_id TEXT NOT NULL DEFAULT '',
                operation TEXT NOT NULL DEFAULT '',
                parameters TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS case_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                evidence_id TEXT DEFAULT '',
                event_type TEXT NOT NULL,
                description TEXT DEFAULT '',
                timestamp TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ocr_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ocr_run_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL DEFAULT 1,
                raw_text TEXT DEFAULT '',
                normalized_text TEXT DEFAULT '',
                ocr_confidence REAL DEFAULT 0,
                word_count INTEGER DEFAULT 0,
                char_count INTEGER DEFAULT 0,
                detected_language TEXT DEFAULT '',
                detected_script TEXT DEFAULT '',
                FOREIGN KEY (ocr_run_id) REFERENCES ocr_runs(id) ON DELETE CASCADE
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
            CREATE INDEX IF NOT EXISTS idx_evidence_path ON evidence_items(file_path);
            CREATE INDEX IF NOT EXISTS idx_ocr_evidence ON ocr_results(evidence_id);
            CREATE INDEX IF NOT EXISTS idx_history_evidence ON processing_history(evidence_id);
            CREATE INDEX IF NOT EXISTS idx_recent_opened ON recent_files(opened_at DESC);
        """)
        self._ensure_column("evidence_items", "imported_at", "TEXT DEFAULT ''")
        self._ensure_column("evidence_items", "file_type", "TEXT DEFAULT ''")
        self._ensure_column("evidence_items", "file_size", "INTEGER DEFAULT 0")

        self._ensure_column("ocr_results", "raw_text", "TEXT DEFAULT ''")
        self._ensure_column("ocr_results", "normalized_text", "TEXT DEFAULT ''")
        self._ensure_column("ocr_results", "model", "TEXT DEFAULT ''")
        self._ensure_column("ocr_results", "processing_time", "REAL DEFAULT 0")
        self._ensure_column("ocr_results", "preprocessing_info", "TEXT DEFAULT ''")
        self._ensure_column("ocr_results", "integrity_snapshot", "TEXT DEFAULT ''")
        self._ensure_column("ocr_results", "examination_started", "TEXT DEFAULT ''")
        self._ensure_column("ocr_results", "examination_completed", "TEXT DEFAULT ''")
        self._ensure_column("ocr_results", "ocr_provenance", "TEXT DEFAULT ''")

        self._ensure_column("ocr_runs", "evidence_id", "TEXT DEFAULT ''")
        self._ensure_column("ocr_runs", "case_id", "TEXT DEFAULT ''")
        self._ensure_column("ocr_runs", "preprocessing_config", "TEXT DEFAULT ''")
        self._ensure_column("ocr_runs", "started_at", "TEXT DEFAULT ''")
        self._ensure_column("ocr_runs", "completed_at", "TEXT DEFAULT ''")
        self._ensure_column("ocr_runs", "integrity_sha256", "TEXT DEFAULT ''")
        
        self._ensure_column("ocr_regions", "page_number", "INTEGER DEFAULT 1")
        self._ensure_column("ocr_regions", "region_id", "TEXT DEFAULT ''")

        self._conn.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        """Add a column for older local databases if it is missing."""
        rows = self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {row["name"] for row in rows}
        if column not in existing:
            self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

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

    def add_case_event(self, case_id: str, evidence_id: str, event_type: str, description: str = "") -> bool:
        """Add an event to the case timeline."""
        try:
            now = datetime.now().isoformat()
            self._conn.execute(
                """INSERT INTO case_events
                   (case_id, evidence_id, event_type, description, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (case_id, evidence_id, event_type, description, now)
            )
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding case event: {e}")
            return False
            
    def get_case_events(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieve events for a case."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM case_events WHERE case_id = ? ORDER BY timestamp ASC",
                (case_id,)
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching events for case {case_id}: {e}")
            return []

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
                    file_path, sha256, md5, status, notes, reviewed, relevant,
                    created_at, imported_at, file_type, file_size)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                    now,
                    evidence_data.get("imported_at", now),
                    evidence_data.get("file_type", ""),
                    int(evidence_data.get("file_size", 0) or 0),
                )
            )
            self._conn.commit()
            logger.info(f"Evidence added: {evidence_data.get('evidence_id')}")
            return True
        except Exception as e:
            logger.error(f"Error adding evidence: {e}")
            return False

    def get_evidence_by_path(self, case_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Return an evidence item for a case/path pair if already imported."""
        try:
            row = self._conn.execute(
                "SELECT * FROM evidence_items WHERE case_id = ? AND file_path = ?",
                (case_id, file_path)
            ).fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching evidence by path: {e}")
            return None

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
                       "notes", "reviewed", "relevant", "sha256", "md5",
                       "file_type", "file_size", "imported_at"}
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
        """Track a recently opened file. Maintains max 15 entries."""
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

            # Keep only last 15
            self._conn.execute(
                """DELETE FROM recent_files WHERE id NOT IN
                   (SELECT id FROM recent_files ORDER BY opened_at DESC LIMIT 15)"""
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

    # ── OCR and Processing History ───────────────────────────

    def save_ocr_result(self, case_id: str, evidence_id: str, result: Any) -> bool:
        """Persist a complete OCR result, replacing older OCR rows for evidence."""
        try:
            now = datetime.now().isoformat()
            self._conn.execute(
                "DELETE FROM ocr_results WHERE case_id = ? AND evidence_id = ?",
                (case_id, evidence_id)
            )
            for page in getattr(result, "page_results", []):
                lang = getattr(page, "language_result", None)
                script = getattr(page, "script_result", None)
                cursor = self._conn.execute(
                    """INSERT INTO ocr_results
                       (evidence_id, case_id, page_number, detected_language,
                        language_confidence, detected_script, script_confidence,
                        ocr_confidence, ocr_quality, extracted_text, raw_text,
                        normalized_text, ocr_engine, model, processing_time,
                        preprocessing_info, integrity_snapshot, examination_started,
                        examination_completed, ocr_provenance, processed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        evidence_id,
                        case_id,
                        getattr(page, "page_number", 1),
                        getattr(lang, "language", "") if lang else "",
                        float(getattr(lang, "confidence", 0.0) if lang else 0.0),
                        getattr(script, "script", "") if script else "",
                        float(getattr(script, "confidence", 0.0) if script else 0.0),
                        float(getattr(page, "ocr_confidence", 0.0)),
                        getattr(lang, "ocr_quality", "") if lang else "",
                        getattr(page, "text", ""),
                        getattr(page, "raw_text", ""),
                        getattr(page, "normalized_text", ""),
                        getattr(page, "ocr_engine_used", "") or getattr(result, "ocr_engine_used", ""),
                        getattr(page, "ocr_model_used", ""),
                        float(getattr(result, "processing_time_seconds", 0.0)),
                        json.dumps([{"name": s.name, "applied": s.applied} for s in getattr(page, "processing_steps", [])]),
                        getattr(result, "integrity_snapshot", ""),
                        getattr(result, "examination_started", ""),
                        getattr(result, "examination_completed", ""),
                        json.dumps(getattr(page, "ocr_provenance", {})),
                        now,
                    )
                )
                result_id = cursor.lastrowid
                
                for region in getattr(page, "word_regions", []):
                    self._conn.execute(
                        """INSERT INTO ocr_regions
                           (ocr_result_id, box_x, box_y, box_w, box_h, text, confidence, engine)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (result_id, region.box[0], region.box[1], region.box[2], region.box[3],
                         region.text, float(region.confidence), region.engine)
                    )
                
                for run in getattr(page, "ocr_runs", []):
                    self._conn.execute(
                        """INSERT INTO ocr_runs
                           (ocr_result_id, engine, language_model, preprocessing_variant,
                            confidence, text, processing_time, status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (result_id, run.engine, run.language_model, run.preprocessing_variant,
                         float(run.confidence), run.text, float(run.processing_time), run.status)
                    )
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving OCR result: {e}")
            return False

    def get_ocr_runs_for_evidence(self, evidence_id: str) -> List[Dict[str, Any]]:
        """Retrieve all OCR runs associated with an evidence item."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM ocr_runs WHERE evidence_id = ? ORDER BY id ASC",
                (evidence_id,)
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching OCR runs for evidence {evidence_id}: {e}")
            return []
            
    def get_ocr_regions_for_run(self, ocr_run_id: int) -> List[Dict[str, Any]]:
        """Retrieve all regions for a specific OCR run."""
        try:
            # We join through ocr_results for backwards compatibility if needed, 
            # but ideally ocr_regions would map directly to ocr_runs in the future.
            # Wait, ocr_regions maps to ocr_results right now. For phase 2 it maps to ocr_result_id.
            # In the new design, they should ideally be linked to runs, but let's query via result ID for now 
            # or add a run_id column later. 
            pass # We will refine this after updating models if necessary.
        except Exception:
            pass
        return []

    def add_processing_history(
        self,
        case_id: str,
        evidence_id: str,
        operation: str,
        parameters: Any = None,
    ) -> bool:
        """Append an evidence processing history entry."""
        try:
            params = json.dumps(parameters or {}, ensure_ascii=False)
            self._conn.execute(
                """INSERT INTO processing_history
                   (evidence_id, case_id, operation, parameters, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (evidence_id, case_id, operation, params, datetime.now().isoformat())
            )
            self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding processing history: {e}")
            return False

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
