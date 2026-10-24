"""LangChain client that lets an LLM use tools from the MCP server.

Start the MCP Server first:
    docker compose up -d --build

Then run 
    python -m client.mcp_client.py

    """

from __future__ import annotations
import asyncio
from pprint import pprint

from dotenv import load_dotenv
import os

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from client.provider_factory import MissingApiKeyError, get_mcp_client_config, get_model_identifier
load_dotenv()


DEFAULT_QUESTION = (
    "EMP001 wants annual leave from 2026-10-28 to 2026-11-02. "
    "Check their current balance, verify whether the request is allowed, "
    "and explain what action should be taken."
)

def _extract_final_text(response: object) -> str:
    """Extract final text from a LangChain agent response when possible.

    Params:
        response: Agent response object or dictionary.

    Returns:
        Final text or pretty string fallback.
    """
    if isinstance(response, dict) and "messages" in response:
        messages = response["messages"]
        if messages:
            last = messages[-1]
            content = getattr(last, "content", None)
            if isinstance(content, str):
                return content
            if content is not None:
                return str(content)
    return str(response)

async def main():
    """Connect LangChain to MCP tools and ask a business question.

    Params:
        None

    Returns:
        None
    """
    question = os.getenv("DEMO_QUESTION", DEFAULT_QUESTION)

    try:
        model_identifier = get_model_identifier()

    except MissingApiKeyError as e:
        print("\n Missing API Key:")
        print(e)
        return 

    client = MultiServerMCPClient(get_mcp_client_config())
    tools = await client.get_tools()


    print(f"Loaded {len(tools)} MCP tools into LangChain:")
    for tool in tools:
        print(f" - {tool.name}")
    agent = create_agent(model_identifier, tools)

    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful HR Leave assistant. Use MCP tools for facts."
                        "Do not invent balences, approval, employee details, or policy rules."

                    )
                    },

                    {
                        "role": "user",
                        "content": question
                    }
                
            ]
        }
    )
    print("\nFinal answer:")
    filan_response = _extract_final_text(response)

    print(filan_response)


if __name__ == "__main__":
    asyncio.run(main())

    




    


    


    
    






