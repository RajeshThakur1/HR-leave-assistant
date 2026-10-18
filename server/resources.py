"""MCP resources exposed by the HR Leave server."""

from __future__ import annotations

from server import db

LEAVE_POLICY_MARKDOWN = """
# HR Leave Policy

- Annual leave is deducted from the employee's available balance.
- Sick leave is deducted from the employee's available balance.
- Personal leave is deducted from the employee's available balance.
- Unpaid leave can be recorded even when paid leave balance is insufficient.
- Weekends are not counted as business leave days.
- Requests cannot start in the past.
- Overlapping approved or pending requests are blocked.
- This demo auto-approves valid requests so the class can focus on MCP mechanics.
""".strip()

SCHEMA_MARKDOWN = """
# HR Leave Database Schema

## employees
- employee_id: stable employee identifier such as EMP001
- name: display name
- email: stored internally; not exposed by MCP tools
- department: Engineering, People Ops, Sales, or Finance
- role: job title
- leave_balance: available paid leave days

## leave_requests
- request_id: unique request ID
- employee_id: employee linked to request
- start_date / end_date: YYYY-MM-DD
- leave_type: Annual, Sick, Personal, or Unpaid
- days_requested: business-day count
- status: Approved in this classroom demo

## audit_log
- records system actions without exposing unnecessary PII
""".strip()

def register_resources(mcp) -> None:
    """Register MCP resources on a FastMCP server.

    Params:
        mcp: FastMCP server instance.

    Returns:
        None
    """
    @mcp.resource("hr-schema://tables")
    def get_database_schema() -> str:
        """Return a safe schema overview for the HR leave database.

        Params:
            None

        Returns:
            Markdown schema text.
        """

        return SCHEMA_MARKDOWN
    
    @mcp.resource("employee://{employee_id}/summary")
    def get_employee_summary(employee_id: str) -> str:
        """Return a sanitized employee summary resource.

        Params:
            employee_id: Employee ID in EMP### format.

        Returns:
            Markdown employee summary.
        """

        employee = db.get_employee(employee_id)
        if not employee:
            return f"No employee found for {employee_id}."
        return (
            f"# Employee Summary: {employee['employee_id']}\n\n"
            f"- Name: {employee['name']}\n"
            f"- Department: {employee['department']}\n"
            f"- Role: {employee['role']}\n"
            f"- Leave balance: {employee['leave_balance']} days\n"
            "\nEmail is intentionally not exposed through this MCP resource."
        )



