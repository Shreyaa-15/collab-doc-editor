import sqlite3
import uuid
from datetime import datetime

DB_PATH = "collab.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            owner       TEXT NOT NULL,
            content     TEXT DEFAULT '',
            revision    INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS operations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id      TEXT NOT NULL,
            user_id     TEXT NOT NULL,
            revision    INTEGER NOT NULL,
            ops_json    TEXT NOT NULL,
            applied_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

# --- Documents ---

def create_document(title: str, owner: str) -> dict:
    conn = get_conn()
    doc_id = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO documents (id, title, owner) VALUES (?, ?, ?)",
        (doc_id, title, owner)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    conn.close()
    return dict(row)

def get_document(doc_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_documents() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM documents ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_document(doc_id: str, content: str, revision: int):
    conn = get_conn()
    conn.execute(
        "UPDATE documents SET content=?, revision=?, updated_at=? WHERE id=?",
        (content, revision, datetime.utcnow().isoformat(), doc_id)
    )
    conn.commit()
    conn.close()

# --- Operations log ---

def save_operation(doc_id: str, user_id: str, revision: int, ops_json: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO operations (doc_id, user_id, revision, ops_json) VALUES (?, ?, ?, ?)",
        (doc_id, user_id, revision, ops_json)
    )
    conn.commit()
    conn.close()

def get_operations_since(doc_id: str, revision: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM operations WHERE doc_id=? AND revision>=? ORDER BY revision ASC",
        (doc_id, revision)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]