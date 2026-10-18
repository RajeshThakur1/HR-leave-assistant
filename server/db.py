"""SQLite data layer for the HR Leave MCP practical.

The database is intentionally lightweight so the class can focus on MCP,
containerisation, and LLM connection rather than external database setup.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

from server.config import HR_DB_PATH, SEED_FILE_PATH


LOGGER = logging.getLogger(__name__)
EMPLOYEE_ID_RE = re.compile(r"^EMP\d{3}$")
ALLOWED_DEPARTMENTS = {"Engineering", "People Ops", "Sales", "Finance"}
ALLOWED_LEAVE_TYPES = {"Annual", "Sick", "Personal", "Unpaid"}


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection with dictionary-like rows.

    Params:
        None

    Returns:
        Context manager yielding a SQLite connection.
    """
    HR_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(HR_DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    finally:
        connection.close()



def init_database(seed_if_empty: bool=True) -> None:

    """Create tables and optionally seed sample employees.

    Params:
        seed_if_empty: Insert sample employees when the employee table is empty.

    Returns:
        None
    """
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL,
                leave_balance INTEGER NOT NULL DEFAULT 20,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leave_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                leave_type TEXT NOT NULL,
                days_requested INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                target_employee_id TEXT,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        if seed_if_empty:
                employee_count = cursor.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
                if employee_count == 0:
                    seed_database(cursor)
                    LOGGER.info("Seeded HR database at %s", HR_DB_PATH)



def seed_database(cursor: sqlite3.Cursor, seed_file: Path = SEED_FILE_PATH) -> None:
    """Insert seed employee data.

    Params:
        cursor: Active SQLite cursor.
        seed_file: JSON file containing sample employees.

    Returns:
        None
    """

    employees = json.loads(seed_file.read_text(encoding="utf-8"))
    for employee in employees:
        cursor.execute(
            """
            INSERT INTO employees (employee_id, name, email, department, role, leave_balance)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                employee["employee_id"],
                employee["name"],
                employee["email"],
                employee["department"],
                employee["role"],
                employee["leave_balance"],
            ),
        )
    cursor.execute(
        """
        INSERT INTO audit_log (event_type, actor, target_employee_id, details)
        VALUES (?, ?, ?, ?)
        """,
        ("seed", "system", None, "Initial sample employees inserted."),
    )



def reset_database() -> None:
    """Delete and recreate the SQLite database.

    Params:
        None

    Returns:
        None
    """

    if HR_DB_PATH.exists():
        HR_DB_PATH.unlink()
    init_database(seed_if_empty=True)

def validate_employee_id(employee_id: str) -> str:
    """Validate and normalize an employee ID.

    Params:
        employee_id: Raw employee ID.

    Returns:
        Uppercase employee ID.

    Raises:
        ValueError: If the ID format is invalid.
    """

    normalized = employee_id.strip().upper()
    if not EMPLOYEE_ID_RE.match(normalized):
        raise ValueError("Employee ID must match EMP###, for example EMP001.")
    return normalized


def parse_iso_date(value: str, field_name: str) -> date:
    """Parse an ISO date string.

    Params:
        value: Date value in YYYY-MM-DD format.
        field_name: Name used in validation error messages.

    Returns:
        Parsed date.

    Raises:
        ValueError: If the date cannot be parsed.
    """

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.") from exc


def business_days_between(start: date, end: date) -> int:
    """Count business days between two inclusive dates.

    Params:
        start: Start date.
        end: End date.

    Returns:
        Number of Monday-Friday days.
    """

    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def get_employee(employee_id: str) -> dict[str, Any] | None:
    """Fetch one sanitized employee record.

    Params:
        employee_id: Employee ID.

    Returns:
        Employee dictionary or None.
    """

    employee_id = validate_employee_id(employee_id)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT employee_id, name, department, role, leave_balance
            FROM employees
            WHERE employee_id = ?
            """,
            (employee_id,),
        ).fetchone()
    return dict(row) if row else None


def list_employees(department: str | None = None) -> list[dict[str, Any]]:
    """List sanitized employees, optionally by department.

    Params:
        department: Optional department filter.

    Returns:
        List of employee dictionaries.
    """

    with get_connection() as connection:
        if department and department != "all":
            rows = connection.execute(
                """
                SELECT employee_id, name, department, role, leave_balance
                FROM employees
                WHERE department = ?
                ORDER BY employee_id
                """,
                (department,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT employee_id, name, department, role, leave_balance
                FROM employees
                ORDER BY employee_id
                """
            ).fetchall()
    return [dict(row) for row in rows]

def get_leave_balance(employee_id: str) -> dict[str, Any]:
    """Return leave balance for one employee.

    Params:
        employee_id: Employee ID.

    Returns:
        Leave balance record.

    Raises:
        ValueError: If employee does not exist.
    """

    employee = get_employee(employee_id)
    if not employee:
        raise ValueError(f"No employee found for {employee_id}.")
    return {
        "employee_id": employee["employee_id"],
        "name": employee["name"],
        "department": employee["department"],
        "leave_balance": employee["leave_balance"],
    }


def check_leave_policy(employee_id: str, start_date: str, end_date: str, leave_type: str = "Annual") -> dict[str, Any]:
    """Check whether a leave request is allowed without changing data.

    Params:
        employee_id: Employee ID.
        start_date: Leave start date in YYYY-MM-DD format.
        end_date: Leave end date in YYYY-MM-DD format.
        leave_type: Leave category.

    Returns:
        Policy check dictionary.

    Raises:
        ValueError: If validation fails.
    """

    employee_id = validate_employee_id(employee_id)
    if leave_type not in ALLOWED_LEAVE_TYPES:
        raise ValueError(f"leave_type must be one of: {', '.join(sorted(ALLOWED_LEAVE_TYPES))}.")

    start = parse_iso_date(start_date, "start_date")
    end = parse_iso_date(end_date, "end_date")
    if end < start:
        raise ValueError("end_date cannot be before start_date.")
    if start < date.today():
        raise ValueError("Leave start date cannot be in the past.")

    days_requested = business_days_between(start, end)
    if days_requested <= 0:
        raise ValueError("Leave request must include at least one business day.")

    employee = get_leave_balance(employee_id)
    enough_balance = leave_type == "Unpaid" or employee["leave_balance"] >= days_requested

    with get_connection() as connection:
        overlap = connection.execute(
            """
            SELECT COUNT(*)
            FROM leave_requests
            WHERE employee_id = ?
              AND status IN ('Approved', 'Pending')
              AND NOT (end_date < ? OR start_date > ?)
            """,
            (employee_id, start_date, end_date),
        ).fetchone()[0]

    return {
        "employee_id": employee_id,
        "days_requested": days_requested,
        "current_balance": employee["leave_balance"],
        "leave_type": leave_type,
        "allowed": bool(enough_balance and overlap == 0),
        "reasons": [
            reason
            for reason in [
                None if enough_balance else "Insufficient leave balance.",
                None if overlap == 0 else "Overlaps with an existing leave request.",
            ]
            if reason
        ],
    }


def apply_leave(employee_id: str, start_date: str, end_date: str, leave_type: str, reason: str) -> dict[str, Any]:
    """Apply leave and update the employee balance.

    Params:
        employee_id: Employee ID.
        start_date: Leave start date in YYYY-MM-DD format.
        end_date: Leave end date in YYYY-MM-DD format.
        leave_type: Leave category.
        reason: Short reason for leave.

    Returns:
        Created leave request dictionary.

    Raises:
        ValueError: If validation or policy check fails.
    """

    policy = check_leave_policy(employee_id, start_date, end_date, leave_type)
    if not policy["allowed"]:
        raise ValueError("Leave request blocked: " + " ".join(policy["reasons"]))

    days_requested = int(policy["days_requested"])
    employee_id = validate_employee_id(employee_id)

    with get_connection() as connection:
        cursor = connection.cursor()
        new_balance = policy["current_balance"]
        if leave_type != "Unpaid":
            new_balance -= days_requested

        cursor.execute(
            """
            INSERT INTO leave_requests
            (employee_id, start_date, end_date, leave_type, days_requested, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (employee_id, start_date, end_date, leave_type, days_requested, reason[:200], "Approved"),
        )
        request_id = cursor.lastrowid
        cursor.execute(
            "UPDATE employees SET leave_balance = ? WHERE employee_id = ?",
            (new_balance, employee_id),
        )
        cursor.execute(
            """
            INSERT INTO audit_log (event_type, actor, target_employee_id, details)
            VALUES (?, ?, ?, ?)
            """,
            (
                "apply_leave",
                "mcp_tool",
                employee_id,
                json.dumps(
                    {
                        "request_id": request_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "leave_type": leave_type,
                        "days_requested": days_requested,
                    }
                ),
            ),
        )

    return {
        "request_id": request_id,
        "employee_id": employee_id,
        "start_date": start_date,
        "end_date": end_date,
        "leave_type": leave_type,
        "days_requested": days_requested,
        "status": "Approved",
        "remaining_balance": new_balance,
    }



def get_department_summary(department: str) -> dict[str, Any]:
    """Return a department-level leave summary.

    Params:
        department: Department name.

    Returns:
        Department summary dictionary.

    Raises:
        ValueError: If the department is invalid or empty.
    """

    department = department.strip()
    if department not in ALLOWED_DEPARTMENTS:
        raise ValueError(f"Department must be one of: {', '.join(sorted(ALLOWED_DEPARTMENTS))}.")

    employees = list_employees(department=department)
    if not employees:
        raise ValueError(f"No employees found in {department}.")

    with get_connection() as connection:
        upcoming_rows = connection.execute(
            """
            SELECT employee_id, start_date, end_date, leave_type, days_requested, status
            FROM leave_requests
            WHERE employee_id IN (SELECT employee_id FROM employees WHERE department = ?)
              AND end_date >= ?
            ORDER BY start_date
            LIMIT 10
            """,
            (department, date.today().isoformat()),
        ).fetchall()

    balances = [employee["leave_balance"] for employee in employees]
    return {
        "department": department,
        "headcount": len(employees),
        "average_balance": round(sum(balances) / len(balances), 2),
        "lowest_balance_employees": sorted(
            [
                {
                    "employee_id": employee["employee_id"],
                    "name": employee["name"],
                    "leave_balance": employee["leave_balance"],
                }
                for employee in employees
            ],
            key=lambda item: item["leave_balance"],
        )[:3],
        "upcoming_leave_requests": [dict(row) for row in upcoming_rows],
    }


def recent_leave_requests(employee_id: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """Return recent leave requests.

    Params:
        employee_id: Optional employee ID filter.
        limit: Maximum rows to return.

    Returns:
        List of recent leave request dictionaries.
    """

    limit = max(1, min(int(limit), 20))
    with get_connection() as connection:
        if employee_id:
            employee_id = validate_employee_id(employee_id)
            rows = connection.execute(
                """
                SELECT request_id, employee_id, start_date, end_date, leave_type, days_requested, status, created_at
                FROM leave_requests
                WHERE employee_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (employee_id, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT request_id, employee_id, start_date, end_date, leave_type, days_requested, status, created_at
                FROM leave_requests
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return [dict(row) for row in rows]


def recent_audit_events(limit: int = 10) -> list[dict[str, Any]]:
    """Return recent audit events without exposing employee email addresses.

    Params:
        limit: Maximum rows to return.

    Returns:
        List of audit event dictionaries.
    """

    limit = max(1, min(int(limit), 50))
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_type, actor, target_employee_id, details, created_at
            FROM audit_log
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
