from __future__ import annotations
import os

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "HR Leave MCP Server")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "dev-token-change-me").strip()


HR_DB_PATH = Path(os.getenv("HR_DB_PATH", str(DEFAULT_DATA_DIR / "hr_leave.db")))
SEED_FILE_PATH = Path(os.getenv("SEED_FILE_PATH", str(DEFAULT_DATA_DIR / "seed_employees.json")))

LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO").upper()


def configure_logging() -> None:
    """Configure simple structured-enough logs for classroom demos.

    Params:
        None

    Returns:
        None
    """

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
