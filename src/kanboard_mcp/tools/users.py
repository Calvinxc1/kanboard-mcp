"""User-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError
from ..redaction import redact_user_record

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register user-related tools."""

    @mcp.tool()
    def getUser(user_id: int) -> dict[str, Any]:
        """Get a specific user by ID.

        Args:
            user_id: The ID of the user to retrieve
        """
        try:
            user = client.call_api(method_name="get_user", user_id=user_id)
            return {"success": True, "data": redact_user_record(user)}
        except KanboardClientError as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getUserByName(username: str) -> dict[str, Any]:
        """Get a specific user by username.

        Args:
            username: The username of the user to retrieve
        """
        try:
            user = client.call_api(method_name="get_user_by_name", username=username)
            return {"success": True, "data": redact_user_record(user)}
        except KanboardClientError as e:
            logger.error(f"Error getting user '{username}': {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getAllUsers() -> dict[str, Any]:
        """Get all users."""
        try:
            users = client.call_api(method_name="get_all_users")
            if isinstance(users, list):
                users = [redact_user_record(user) for user in users]
            return {"success": True, "data": users, "count": len(users) if users else 0}
        except KanboardClientError as e:
            logger.error(f"Error getting all users: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getMe() -> dict[str, Any]:
        """Get current user information."""
        try:
            user = client.call_api(method_name="get_me")
            return {"success": True, "data": redact_user_record(user)}
        except KanboardClientError as e:
            logger.error(f"Error getting current user info: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getMyDashboard() -> dict[str, Any]:
        """Get current user's dashboard."""
        try:
            dashboard = client.call_api(method_name="get_my_dashboard")
            return {"success": True, "data": dashboard}
        except KanboardClientError as e:
            logger.error(f"Error getting user dashboard: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getMyActivityStream() -> dict[str, Any]:
        """Get current user's activity stream."""
        try:
            activity = client.call_api(method_name="get_my_activity_stream")
            return {
                "success": True,
                "data": activity,
                "count": len(activity) if activity else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting user activity stream: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getMyProjectsList() -> dict[str, Any]:
        """Get current user's projects list."""
        try:
            projects = client.call_api(method_name="get_my_projects_list")
            return {
                "success": True,
                "data": projects,
                "count": len(projects) if projects else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting user projects list: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getMyOverdueTasks() -> dict[str, Any]:
        """Get current user's overdue tasks."""
        try:
            tasks = client.call_api(method_name="get_my_overdue_tasks")
            return {"success": True, "data": tasks, "count": len(tasks) if tasks else 0}
        except KanboardClientError as e:
            logger.error(f"Error getting user overdue tasks: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getMyProjects() -> dict[str, Any]:
        """Get current user's projects."""
        try:
            projects = client.call_api(method_name="get_my_projects")
            return {
                "success": True,
                "data": projects,
                "count": len(projects) if projects else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting user projects: {e}")
            return {"success": False, "error": str(e)}
