
def register_prompts(mcp):
    """Register MCP prompt templates.

    Params:
        mcp: FastMCP server instance.

    Returns:
        None
    """

    @mcp.prompt(title="Leave Request Assistant")
    def leave_request_assistant(employee_id: str, date_range: str) -> str:
        """Prompt template for assessing a leave request.

            Params:
                employee_id: Employee ID.
                date_range: Requested date range.

            Returns:
                Prompt string.
            """
        return (
            "You are an HR leave assistant. Use the available MCP tools to check "
            f"the leave balance and policy for {employee_id}. The requested range is {date_range}. "
            "Do not approve a request unless the tool result says the policy check is allowed. "
            "Explain the result in plain language."
        )


    @mcp.prompt(title="Manager Leave Dashboard")
    def manager_leave_dashboard(department: str) -> str:
        """Prompt template for manager-level reporting.

        Params:
            department: Department name.

        Returns:
            Prompt string.
        """

        return (
            f"Prepare a concise manager dashboard for the {department} department. "
            "Use MCP tools/resources to summarize headcount, low balances, and upcoming leave. "
            "Avoid exposing email addresses or unnecessary personal details."
        )

