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

from langchain.agents import create_agent
from langchain.mcp_adapters.client import MultiServerMCPClient


load_dotenv()


