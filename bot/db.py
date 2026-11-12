"""SQLite storage: processed invoices and a run history table."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT PRIMARY KEY,
    vendor TEXT NOT NULL,
    email TEXT NOT NULL,
    amount REAL NOT NULL,
    invoice_date TEXT NOT NULL,
    loaded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bot_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    input_file TEXT NOT NULL,
    total_rows INTEGER DEFAULT 0,
    loaded_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    message TEXT
);
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution_note TEXT
);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def start_run(conn, started_at, input_file):
    cur = conn.execute(
        "INSERT INTO bot_runs (started_at, input_file, status) VALUES (?, ?, 'RUNNING')",
        (started_at, input_file))
    conn.commit()
    return cur.lastrowid


def finish_run(conn, run_id, finished_at, total, loaded, failed, status, message=""):
    conn.execute(
        "UPDATE bot_runs SET finished_at=?, total_rows=?, loaded_rows=?, failed_rows=?, "
        "status=?, message=? WHERE run_id=?",
        (finished_at, total, loaded, failed, status, message, run_id))
    conn.commit()


def invoice_exists(conn, invoice_id):
    return conn.execute("SELECT 1 FROM invoices WHERE invoice_id=?", (invoice_id,)).fetchone() is not None


def insert_invoice(conn, row, loaded_at):
    conn.execute(
        "INSERT INTO invoices VALUES (:invoice_id, :vendor, :email, :amount, :invoice_date, :loaded_at)",
        {**row, "loaded_at": loaded_at})


def recent_runs(conn, limit=10):
    return conn.execute("SELECT * FROM bot_runs ORDER BY run_id DESC LIMIT ?", (limit,)).fetchall()


def create_ticket(conn, run_id, severity, title, details, created_at):
    cur = conn.execute(
        "INSERT INTO tickets (run_id, severity, title, details, created_at) VALUES (?, ?, ?, ?, ?)",
        (run_id, severity, title, details, created_at))
    conn.commit()
    return cur.lastrowid


def list_tickets(conn, status=None):
    if status:
        return conn.execute("SELECT * FROM tickets WHERE status=? ORDER BY ticket_id DESC", (status.upper(),)).fetchall()
    return conn.execute("SELECT * FROM tickets ORDER BY ticket_id DESC").fetchall()


def resolve_ticket(conn, ticket_id, note, resolved_at):
    cur = conn.execute(
        "UPDATE tickets SET status='RESOLVED', resolution_note=?, resolved_at=? "
        "WHERE ticket_id=? AND status='OPEN'", (note, resolved_at, ticket_id))
    conn.commit()
    return cur.rowcount == 1


def get_run(conn, run_id):
    return conn.execute("SELECT * FROM bot_runs WHERE run_id=?", (run_id,)).fetchone()


def list_invoices(conn, limit=100):
    return conn.execute("SELECT * FROM invoices ORDER BY loaded_at DESC LIMIT ?", (limit,)).fetchall()
