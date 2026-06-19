"""Main MCP server implementation for Kanboard API."""

import logging
import sys
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .client import create_client
from .config import Config, load_config
from .redaction import redact_user_record
from .tools import (
    boards,
    categories,
    columns,
    comments,
    files,
    links,
    projects,
    subtasks,
    swimlanes,
    tags,
    tasks,
    users,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TOOL_MODULES = {
    "projects": projects,
    "tasks": tasks,
    "categories": categories,
    "columns": columns,
    "boards": boards,
    "comments": comments,
    "users": users,
    "links": links,
    "subtasks": subtasks,
    "swimlanes": swimlanes,
    "tags": tags,
    "files": files,
}

CORE_TOOL_NAMES = frozenset(
    {
        "getTask",
        "searchTasks",
        "getAllTasks",
        "createTask",
        "updateTask",
        "moveTaskToColumnByName",
        "openTask",
        "closeTask",
        "getAllCategories",
        "createComment",
        "getAllComments",
        "createSubtask",
        "getSubtask",
        "getAllSubtasks",
        "updateSubtask",
        "removeSubtask",
        "createTaskLink",
        "updateTaskLink",
        "getTaskLinkById",
        "getAllTaskLinks",
        "removeTaskLink",
        "getAllLinks",
        "getLinkByLabel",
        "getLinkById",
        "getOppositeLinkId",
        "getAllProjects",
        "getColumns",
        "getBoard",
        "getMe",
        "test_connection",
        "get_config_info",
    }
)


class ToolProfileMCP:
    """MCP registration proxy that only exposes enabled tool names."""

    def __init__(self, mcp: FastMCP, enabled_tool_names: frozenset[str] | None):
        self._mcp = mcp
        self._enabled_tool_names = enabled_tool_names

    def tool(self):
        def decorator(func):
            if self._enabled_tool_names is None or func.__name__ in self._enabled_tool_names:
                return self._mcp.tool()(func)
            return func

        return decorator


class KanboardMCPServer:
    """Kanboard MCP Server implementation."""

    def __init__(self, config: Config):
        """Initialize the MCP server with configuration."""
        self.config = config
        self.client = create_client(config)
        self.mcp = FastMCP(config.server.server_name)

        # Set up logging level
        if config.server.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")

        # Register tools
        self._register_tools()

        # Add connection test tool
        self._register_connection_tools()

    def _register_tools(self) -> None:
        """Register all Kanboard API tools."""
        enabled_tool_names = self._enabled_tool_names()
        mcp = ToolProfileMCP(self.mcp, enabled_tool_names)
        module_names = (
            self.config.server.enabled_tool_modules
            if self.config.server.enabled_tool_modules is not None
            else tuple(TOOL_MODULES)
        )

        for module_name in module_names:
            module = TOOL_MODULES[module_name]
            if hasattr(module, "register_tools"):
                module.register_tools(mcp, self.client)
                logger.info(f"Registered tools from {module.__name__}")

    def _enabled_tool_names(self) -> frozenset[str] | None:
        """Return the configured MCP tool allowlist, or None for all tools."""
        if self.config.server.tool_profile == "core":
            return CORE_TOOL_NAMES
        return None

    def _register_connection_tools(self) -> None:
        """Register connection and server management tools."""

        mcp = ToolProfileMCP(self.mcp, self._enabled_tool_names())

        @mcp.tool()
        def test_connection() -> dict[str, Any]:
            """Test connection to Kanboard server and return status."""
            try:
                result = self.client.test_connection()
                return {
                    "success": True,
                    "data": {
                        "connected": bool(
                            isinstance(result, dict) and result.get("connected")
                        ),
                        "username": (
                            result.get("username") if isinstance(result, dict) else None
                        ),
                        "server_url": (
                            result.get("server_url")
                            if isinstance(result, dict)
                            else None
                        ),
                    },
                }
            except Exception as e:
                logger.error(f"Connection test failed: {e}")
                return {"success": False, "error": str(e)}

        @mcp.tool()
        def get_server_info() -> dict[str, Any]:
            """Get Kanboard server information and capabilities."""
            try:
                result = self.client.get_server_info()
                if isinstance(result, dict) and "user_info" in result:
                    result = {
                        **result,
                        "user_info": redact_user_record(result["user_info"]),
                    }
                return {"success": True, "data": result}
            except Exception as e:
                logger.error(f"Failed to get server info: {e}")
                return {"success": False, "error": str(e)}

        @mcp.tool()
        def get_config_info() -> dict[str, Any]:
            """Get current configuration information (without sensitive data)."""
            return {
                "success": True,
                "data": {
                    "server_name": self.config.server.server_name,
                    "server_version": self.config.server.server_version,
                    "debug": self.config.server.debug,
                    "max_retries": self.config.server.max_retries,
                    "retry_delay": self.config.server.retry_delay,
                    "kanboard_url": self.config.kanboard.url,
                    "kanboard_username": self.config.kanboard.username,
                    "verify_ssl": self.config.kanboard.verify_ssl,
                    "timeout": self.config.kanboard.timeout,
                    "tool_profile": self.config.server.tool_profile,
                    "enabled_tool_modules": self.config.server.enabled_tool_modules,
                    "python_executable": sys.executable,
                    "server_module_path": __file__,
                    "boards_module_path": boards.__file__,
                },
            }

    def run(self) -> None:
        """Run the MCP server."""
        try:
            logger.info(
                f"Starting {self.config.server.server_name} v{self.config.server.server_version}"
            )
            logger.info(f"Connecting to Kanboard at {self.config.kanboard.url}")

            # Test connection on startup
            connection_result = self.client.test_connection()
            if connection_result.get("connected"):
                logger.info("Successfully connected to Kanboard")
            else:
                logger.error(
                    f"Failed to connect to Kanboard: {connection_result.get('error')}"
                )
                raise ConnectionError(
                    f"Cannot connect to Kanboard: {connection_result.get('error')}"
                )

            # Run the server
            self.mcp.run()

        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


def create_server(config: Config | None = None) -> KanboardMCPServer:
    """Create a new Kanboard MCP server instance."""
    if config is None:
        config = load_config()

    return KanboardMCPServer(config)


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Load configuration
        config = load_config()

        # Create and run server
        server = create_server(config)
        server.run()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Please check your environment variables.", file=sys.stderr)
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
