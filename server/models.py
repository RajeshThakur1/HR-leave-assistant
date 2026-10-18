"""Typed response models used by the MCP tools.

FastMCP can infer tool schemas from type hints. Returning consistent models
also helps the LLM reason about success, failure, and next steps.
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


LeaveType = Literal["Annual", "Sick", "Personal", "Unpaid"]


class ToolResponse(BaseModel):
    """Common response envelope for all tools.

    Params:
        success: Whether the operation succeeded.
        message: Human-readable summary.
        data: Structured data for the model/client to inspect.
        error_code: Stable error code when success is false.

    Returns:
        ToolResponse instance.
    """

    success: bool = Field(description="Whether the tool call succeeded.")
    message: str = Field(description="Human-readable summary of the result.")
    data: Any | None = Field(default=None, description="Structured payload.")
    error_code: str | None = Field(default=None, description="Stable error code for failures.")


class EmployeeRecord(BaseModel):
    """Sanitized employee record returned to clients.

    Params:
        employee_id: Internal employee identifier.
        name: Employee display name.
        department: Department name.
        role: Role title.
        leave_balance: Available leave days.

    Returns:
        EmployeeRecord instance.
    """

    employee_id: str
    name: str
    department: str
    role: str
    leave_balance: int


class LeaveApplication(BaseModel):
    """Structured leave application output.

    Params:
        request_id: Database ID for the request.
        employee_id: Employee ID.
        start_date: Leave start date.
        end_date: Leave end date.
        leave_type: Type of leave.
        days_requested: Number of business days.
        status: Request status.
        remaining_balance: Updated leave balance.

    Returns:
        LeaveApplication instance.
    """

    request_id: int
    employee_id: str
    start_date: str
    end_date: str
    leave_type: LeaveType
    days_requested: int
    status: str
    remaining_balance: int


class DepartmentSummary(BaseModel):
    """Aggregated leave summary for a department.

    Params:
        department: Department name.
        headcount: Number of employees.
        average_balance: Average available leave balance.
        lowest_balance_employees: Employees with low balances.
        upcoming_leave_requests: Upcoming approved/pending requests.

    Returns:
        DepartmentSummary instance.
    """

    department: str
    headcount: int
    average_balance: float
    lowest_balance_employees: list[dict[str, Any]]
    upcoming_leave_requests: list[dict[str, Any]]
