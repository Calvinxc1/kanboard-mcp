"""Subtask-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError

logger = logging.getLogger(__name__)

SUBTASK_SUMMARY_FIELDS = (
    "id",
    "title",
    "status",
    "user_id",
    "username",
    "time_estimated",
    "time_spent",
)


def include_subtask_summary_field(value: Any) -> bool:
    """Return whether a subtask summary value carries useful information."""
    return value not in (None, "")


def summarize_subtask(subtask: Any) -> Any:
    """Return compact subtask fields for list responses."""
    if not isinstance(subtask, dict):
        return subtask

    return {
        field: subtask[field]
        for field in SUBTASK_SUMMARY_FIELDS
        if field in subtask and include_subtask_summary_field(subtask[field])
    }


def summarize_subtasks(subtasks: Any) -> Any:
    """Return compact subtask projections while preserving non-list API results."""
    if not isinstance(subtasks, list):
        return subtasks

    return [summarize_subtask(subtask) for subtask in subtasks]


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register subtask-related tools."""

    @mcp.tool()
    def createSubtask(
        task_id: int,
        title: str,
        user_id: int | None = None,
        time_estimated: int | None = None,
        time_spent: int | None = None,
        status: int | None = None,
    ) -> dict[str, Any]:
        """Create a new subtask."""
        try:
            subtask_data = {"task_id": task_id, "title": title}

            if user_id is not None:
                subtask_data["user_id"] = user_id
            if time_estimated is not None:
                subtask_data["time_estimated"] = time_estimated
            if time_spent is not None:
                subtask_data["time_spent"] = time_spent
            if status is not None:
                subtask_data["status"] = status

            subtask_id = client.call_api(method_name="create_subtask", **subtask_data)
            return {"success": True, "data": {"subtask_id": subtask_id}}
        except KanboardClientError as e:
            logger.error(f"Error creating subtask: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getSubtask(subtask_id: int) -> dict[str, Any]:
        """Get a specific subtask by ID."""
        try:
            subtask = client.call_api(method_name="get_subtask", subtask_id=subtask_id)
            return {"success": True, "data": subtask}
        except KanboardClientError as e:
            logger.error(f"Error getting subtask {subtask_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getAllSubtasks(task_id: int) -> dict[str, Any]:
        """Get all subtasks for a task."""
        try:
            subtasks = client.call_api(method_name="get_all_subtasks", task_id=task_id)
            return {
                "success": True,
                "data": summarize_subtasks(subtasks),
                "count": len(subtasks) if subtasks else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting all subtasks for task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def updateSubtask(
        subtask_id: int,
        title: str | None = None,
        user_id: int | None = None,
        time_estimated: int | None = None,
        time_spent: int | None = None,
        status: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing subtask."""
        try:
            subtask = client.call_api(method_name="get_subtask", subtask_id=subtask_id)
            task_id = subtask.get("task_id") if isinstance(subtask, dict) else None
            if task_id is None:
                raise KanboardClientError(
                    f"Unable to resolve task_id for subtask {subtask_id}"
                )

            subtask_data = {"id": subtask_id, "task_id": task_id}

            if title is not None:
                subtask_data["title"] = title
            if user_id is not None:
                subtask_data["user_id"] = user_id
            if time_estimated is not None:
                subtask_data["time_estimated"] = time_estimated
            if time_spent is not None:
                subtask_data["time_spent"] = time_spent
            if status is not None:
                subtask_data["status"] = status

            success = client.call_api(method_name="update_subtask", **subtask_data)
            return {"success": True, "data": {"updated": success}}
        except KanboardClientError as e:
            logger.error(f"Error updating subtask {subtask_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def removeSubtask(subtask_id: int) -> dict[str, Any]:
        """Remove (delete) a subtask."""
        try:
            success = client.call_api(
                method_name="remove_subtask", subtask_id=subtask_id
            )
            return {"success": True, "data": {"removed": success}}
        except KanboardClientError as e:
            logger.error(f"Error removing subtask {subtask_id}: {e}")
            return {"success": False, "error": str(e)}
