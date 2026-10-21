"""
NEXUS AI - Enterprise Database Layer
Manages relational schema, migrations, user authentication, tickets,
ML predictions, event sourcing/audit history, ticket replies, and SLA policies.
"""

import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets.db")


def get_db_connection() -> sqlite3.Connection:
    """Establish connection to SQLite database with dictionary row factory and WAL mode."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite tables, run schema migrations, and seed initial accounts and policies."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            created_at TEXT NOT NULL
        )
        """
    )

    # 2. Tickets table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket TEXT NOT NULL,
            priority TEXT NOT NULL,
            category TEXT NOT NULL,
            department TEXT NOT NULL,
            deadline_detected TEXT,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            user_id INTEGER,
            assigned_agent TEXT DEFAULT 'Unassigned',
            sla_deadline TEXT,
            priority_override TEXT
        )
        """
    )

    # 3. Ticket Predictions table (stores raw ML inferences separately for auditing)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            predicted_priority TEXT NOT NULL,
            confidence REAL,
            model_version TEXT NOT NULL,
            requires_review INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
        )
        """
    )

    # 4. Ticket Events table (Audit Log / Event Sourcing)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER,
            author_name TEXT,
            event_type TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            reason TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
        )
        """
    )

    # 5. Ticket Replies table (Conversations between customers and agents)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER,
            author_name TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
        )
        """
    )

    # 6. SLA Policies table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sla_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            priority TEXT UNIQUE NOT NULL,
            response_hours INTEGER NOT NULL,
            resolution_hours INTEGER NOT NULL
        )
        """
    )

    # 7. Model Versions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS model_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            dataset_version TEXT NOT NULL,
            priority_accuracy REAL,
            priority_macro_f1 REAL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()

    # Migration check for existing SQLite databases
    cursor.execute("PRAGMA table_info(tickets)")
    existing_cols = [col["name"] for col in cursor.fetchall()]
    for new_col, col_type in [
        ("user_id", "INTEGER"),
        ("assigned_agent", "TEXT DEFAULT 'Unassigned'"),
        ("sla_deadline", "TEXT"),
        ("priority_override", "TEXT"),
        ("updated_at", "TEXT"),
    ]:
        if new_col not in existing_cols:
            cursor.execute(f"ALTER TABLE tickets ADD COLUMN {new_col} {col_type}")
    conn.commit()

    # Seed Default Users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ("admin", "admin@nexusticket.com", generate_password_hash("admin123"), "admin", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("agent_sarah", "sarah@nexusticket.com", generate_password_hash("agent123"), "agent", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("user1", "user1@company.com", generate_password_hash("user123"), "customer", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ]
        cursor.executemany(
            "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            default_users,
        )
        conn.commit()

    # Seed Default SLA Policies if empty
    cursor.execute("SELECT COUNT(*) FROM sla_policies")
    if cursor.fetchone()[0] == 0:
        default_sla = [
            ("High", 2, 4),
            ("Medium", 8, 24),
            ("Low", 24, 72),
        ]
        cursor.executemany(
            "INSERT INTO sla_policies (priority, response_hours, resolution_hours) VALUES (?, ?, ?)",
            default_sla,
        )
        conn.commit()

    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# USER AUTHENTICATION & MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def create_user(username: str, email: str, password: str, role: str = "customer") -> Optional[Dict[str, Any]]:
    """Register a new user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, email, password_hash, role, created_at),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Fetch user account by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch user account by ID without password hash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def verify_user_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user credentials."""
    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user["created_at"],
        }
    return None


def get_all_agents() -> List[str]:
    """Get list of active IT agent & admin usernames."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE role IN ('agent', 'admin')")
    rows = cursor.fetchall()
    conn.close()
    return [row["username"] for row in rows]


# ─────────────────────────────────────────────────────────────────────────────
# TICKET OPERATIONS & EVENT AUDIT TRAIL
# ─────────────────────────────────────────────────────────────────────────────

def add_ticket(
    ticket: str,
    priority: str,
    category: str,
    department: str,
    deadline_detected: Optional[str] = None,
    status: str = "Open",
    user_id: Optional[int] = None,
    assigned_agent: str = "Unassigned",
    sla_deadline: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert a new ticket into the database and record creation event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO tickets (ticket, priority, category, department, deadline_detected, status, created_at, updated_at, user_id, assigned_agent, sla_deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket, priority, category, department, deadline_detected, status, now_str, now_str, user_id, assigned_agent, sla_deadline),
    )
    conn.commit()
    ticket_id = cursor.lastrowid

    # Log Creation Event
    cursor.execute(
        """
        INSERT INTO ticket_events (ticket_id, user_id, author_name, event_type, old_value, new_value, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, user_id, "System", "CREATED", None, priority, "Initial ticket creation with ML inference", now_str),
    )
    conn.commit()
    conn.close()

    return get_ticket_by_id(ticket_id)


def record_prediction(
    ticket_id: int,
    predicted_priority: str,
    confidence: Optional[float],
    model_version: str,
    requires_review: bool,
) -> None:
    """Store the initial model prediction separately from user edits."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO ticket_predictions (ticket_id, predicted_priority, confidence, model_version, requires_review, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, predicted_priority, confidence, model_version, 1 if requires_review else 0, now_str),
    )
    conn.commit()
    conn.close()


def get_all_tickets(
    status_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    user_id: Optional[int] = None,
    assigned_agent: Optional[str] = None,
    priority_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve tickets sorted by latest first with filtering support."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT t.*, p.confidence, p.requires_review, p.model_version
        FROM tickets t
        LEFT JOIN ticket_predictions p ON t.id = p.ticket_id
        WHERE 1=1
    """
    params: List[Any] = []

    if status_filter and status_filter != "All":
        query += " AND t.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        query += " AND t.priority = ?"
        params.append(priority_filter)

    if user_id:
        query += " AND t.user_id = ?"
        params.append(user_id)

    if assigned_agent and assigned_agent != "All":
        query += " AND t.assigned_agent = ?"
        params.append(assigned_agent)

    if search_query:
        query += " AND (t.ticket LIKE ? OR t.category LIKE ? OR t.department LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])

    query += " ORDER BY t.id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_ticket_by_id(ticket_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single ticket by its ID including prediction details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.*, p.confidence, p.requires_review, p.model_version
        FROM tickets t
        LEFT JOIN ticket_predictions p ON t.id = p.ticket_id
        WHERE t.id = ?
        """,
        (ticket_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_ticket_status(ticket_id: int, new_status: str, author_name: str = "System", user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Update ticket status and log event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    old_status = row["status"]
    cursor.execute(
        "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
        (new_status, now_str, ticket_id),
    )

    cursor.execute(
        """
        INSERT INTO ticket_events (ticket_id, user_id, author_name, event_type, old_value, new_value, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, user_id, author_name, "STATUS_CHANGE", old_status, new_status, "Agent status update", now_str),
    )
    conn.commit()
    conn.close()
    return get_ticket_by_id(ticket_id)


def assign_ticket(ticket_id: int, agent_name: str, author_name: str = "System", user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Assign ticket to an agent and log event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT assigned_agent FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    old_agent = row["assigned_agent"]
    cursor.execute(
        "UPDATE tickets SET assigned_agent = ?, updated_at = ? WHERE id = ?",
        (agent_name, now_str, ticket_id),
    )

    cursor.execute(
        """
        INSERT INTO ticket_events (ticket_id, user_id, author_name, event_type, old_value, new_value, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, user_id, author_name, "ASSIGNMENT", old_agent, agent_name, f"Assigned to {agent_name}", now_str),
    )
    conn.commit()
    conn.close()
    return get_ticket_by_id(ticket_id)


def record_priority_override(
    ticket_id: int,
    new_priority: str,
    reason: str,
    author_name: str,
    user_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Manually override priority, record documented reason, and log audit event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT priority FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    old_priority = row["priority"]
    cursor.execute(
        """
        UPDATE tickets
        SET priority = ?, priority_override = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_priority, f"Overridden by {author_name}: {reason}", now_str, ticket_id),
    )

    cursor.execute(
        """
        INSERT INTO ticket_events (ticket_id, user_id, author_name, event_type, old_value, new_value, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, user_id, author_name, "PRIORITY_OVERRIDE", old_priority, new_priority, reason, now_str),
    )
    conn.commit()
    conn.close()
    return get_ticket_by_id(ticket_id)


# Backward-compatible wrapper
def update_ticket_priority(ticket_id: int, new_priority: str) -> Optional[Dict[str, Any]]:
    return record_priority_override(ticket_id, new_priority, "Manual UI override", "Admin")


def add_ticket_reply(ticket_id: int, author_name: str, message: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Append a reply message to a ticket."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO ticket_replies (ticket_id, user_id, author_name, message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ticket_id, user_id, author_name, message, now_str),
    )
    conn.commit()
    reply_id = cursor.lastrowid
    conn.close()

    return {
        "id": reply_id,
        "ticket_id": ticket_id,
        "author_name": author_name,
        "message": message,
        "created_at": now_str,
    }


def get_ticket_replies(ticket_id: int) -> List[Dict[str, Any]]:
    """Get all conversation replies for a ticket."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY id ASC",
        (ticket_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_ticket_events(ticket_id: int) -> List[Dict[str, Any]]:
    """Get full audit event timeline for a ticket."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM ticket_events WHERE ticket_id = ? ORDER BY id ASC",
        (ticket_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_ticket(ticket_id: int) -> bool:
    """Delete a ticket by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


def get_ticket_analytics() -> Dict[str, Any]:
    """Compute aggregate ticket statistics for dashboard metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tickets")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Open'")
    open_cnt = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'In Progress'")
    in_progress_cnt = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'")
    resolved_cnt = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE priority = 'High'")
    high_priority_cnt = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE priority_override IS NOT NULL")
    overrides_cnt = cursor.fetchone()[0]

    cursor.execute("SELECT category, COUNT(*) as cnt FROM tickets GROUP BY category")
    by_category = {row["category"]: row["cnt"] for row in cursor.fetchall()}

    cursor.execute("SELECT department, COUNT(*) as cnt FROM tickets GROUP BY department")
    by_department = {row["department"]: row["cnt"] for row in cursor.fetchall()}

    cursor.execute("SELECT priority, COUNT(*) as cnt FROM tickets GROUP BY priority")
    by_priority = {row["priority"]: row["cnt"] for row in cursor.fetchall()}

    conn.close()

    return {
        "total": total,
        "open": open_cnt,
        "in_progress": in_progress_cnt,
        "resolved": resolved_cnt,
        "high_priority": high_priority_cnt,
        "total_overrides": overrides_cnt,
        "by_category": by_category,
        "by_department": by_department,
        "by_priority": by_priority,
    }


def get_sla_policies() -> Dict[str, Dict[str, int]]:
    """Retrieve all SLA target hours."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT priority, response_hours, resolution_hours FROM sla_policies")
    rows = cursor.fetchall()
    conn.close()
    return {
        row["priority"]: {
            "response_hours": row["response_hours"],
            "resolution_hours": row["resolution_hours"],
        }
        for row in rows
    }
