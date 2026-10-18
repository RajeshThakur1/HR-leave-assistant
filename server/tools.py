"""MCP tool registration for the HR Leave server.

The actual business logic lives in server.db. This file makes the tool
surface safe and model-friendly: clear docstrings, validation, structured"""

from __future__ import annotations

import logging
import time
from typing import Literal
from server import db

from server.models import ToolResponse

LOGGER = logging.getLogger(__name__)


def _safe_tool_call(tool_name: str, operation):
    """Run a database operation and convert errors into a stable envelope.

    Params:
        tool_name: Name of the MCP tool.
        operation: Zero-argument callable containing the business logic.

    Returns:
        ToolResponse.
    """

    started_at = time.perf_counter()
    try:
        result = operation()
        duration_ms = round((time.perf_counter() - started_at) *1000,2)
        LOGGER.info("tool=%s success=true duration_ms=%s", tool_name, duration_ms)
        return ToolResponse(success=True, result=result)
    except ValueError as exct:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.exception("tool=%s success=false duration_ms=%s", tool_name, duration_ms)
        return ToolResponse(
            success=False,
            message="Unexpected server error. Ask the trainer to inspect container logs.",
            data=None,
            error_code="SERVER_ERROR",
        )


def register_tools(mcp) -> None:
    """List employees with sanitized fields only.

        Params:
            department: Optional department filter. Use "all" for every department.

        Returns:
            ToolResponse containing employee_id, name, department, role, and leave_balance.
        """
    @mcp.tool()
    def list_employee(department: str = "all") -> ToolResponse:
        """List employees with sanitized fields only.

        Params:
            department: Optional department filter. Use "all" for every department.

        Returns:
            ToolResponse containing employee_id, name, department, role, and leave_balance.
        """
        return _safe_tool_call(
            "list_employees",
            lambda: db.list_employees(department=department.strip() if department else "all"),
        )

    @mcp.tool()
    def get_leave_balance(employee_id: str) -> ToolResponse:
        """Get leave balance for one employee.

        Params:
            employee_id: Employee identifier in EMP### format.

        Returns:
            ToolResponse containing balance details.
        """

        return _safe_tool_call(
            "get_leave_balance",
            lambda: db.get_leave_balance(employee_id),
        )

    @mcp.tool()
    def check_leave_policy(
        employee_id: str,
        start_date: str,
        end_date: str,
        leave_type: Literal["Annual", "Sick", "Personal", "Unpaid"] = "Annual",
    ) -> ToolResponse:
        """Check whether a leave request is allowed without changing data.

        Params:
            employee_id: Employee identifier in EMP### format.
            start_date: Requested start date in YYYY-MM-DD format.
            end_date: Requested end date in YYYY-MM-DD format.
            leave_type: Annual, Sick, Personal, or Unpaid.

        Returns:
            ToolResponse containing allowed status, days requested, balance, and reasons.
        """

        return _safe_tool_call(
            "check_leave_policy",
            lambda: db.check_leave_policy(employee_id, start_date, end_date, leave_type),
        )
    @mcp.tool()
    def apply_leave(
        employee_id: str,
        start_date: str,
        end_date: str,
        leave_type: Literal["Annual", "Sick", "Personal", "Unpaid"] = "Annual",
        reason: str = "No reason provided",
    ) -> ToolResponse:
        """Apply leave after validating policy and balance.

        Params:
            employee_id: Employee identifier in EMP### format.
            start_date: Requested start date in YYYY-MM-DD format.
            end_date: Requested end date in YYYY-MM-DD format.
            leave_type: Annual, Sick, Personal, or Unpaid.
            reason: Short business reason for the request.

        Returns:
            ToolResponse containing the approved request and remaining balance.
        """

        return _safe_tool_call(
            "apply_leave",
            lambda: db.apply_leave(employee_id, start_date, end_date, leave_type, reason),
        )
    
    def get_department_summary(department: str) -> ToolResponse:
        """Summarize leave state for a department.

        Params:
            department: Engineering, People Ops, Sales, or Finance.

        Returns:
            ToolResponse containing headcount, average balance, low balances, and upcoming leave.
        """

        return _safe_tool_call(
            "get_department_summary",
            lambda: db.get_department_summary(department),
        )
    @mcp.tool()
    def recent_leave_requests(employee_id: str | None = None, limit: int = 5) -> ToolResponse:
        """List recent leave requests.

        Params:
            employee_id: Optional employee identifier in EMP### format.
            limit: Maximum rows to return, capped at 20.

        Returns:
            ToolResponse containing recent leave requests.
        """

        return _safe_tool_call(
            "recent_leave_requests",
            lambda: db.recent_leave_requests(employee_id=employee_id, limit=limit),
        )
    
    @mcp.tool()
    def recent_audit_events(limit: int = 10) -> ToolResponse:
        """Inspect recent audit events for operations troubleshooting.

        Params:
            limit: Maximum events to return, capped at 50.

        Returns:
            ToolResponse containing audit events without unnecessary PII.
        """

        return _safe_tool_call(
            "recent_audit_events",
            lambda: db.recent_audit_events(limit=limit),
        )



    