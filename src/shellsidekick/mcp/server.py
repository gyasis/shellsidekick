"""FastMCP server initialization for ShellSidekick."""

from fastmcp import FastMCP

from shellsidekick.utils.logging import setup_logging
from shellsidekick.core.storage import init_storage

# Initialize FastMCP server
mcp = FastMCP(
    name="ShellSidekick",
    on_duplicate_tools="error"  # Strict mode: prevent duplicate tool names
)

# Import tools to register them with the MCP server
# This must happen after mcp is initialized
from shellsidekick.mcp.tools import session  # noqa: E402, F401
from shellsidekick.mcp.tools import detection  # noqa: E402, F401
from shellsidekick.mcp.tools import history  # noqa: E402, F401


def main():
    """Entry point for the MCP server."""
    setup_logging("INFO")
    init_storage()  # Initialize storage directories
    mcp.run()


if __name__ == "__main__":
    main()
