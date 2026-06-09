"""Task-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError

logger = logging.getLogger(__name__)

TASK_SUMMARY_FIELDS = (
    "id",
    "title",
    "column_id",
    "swimlane_id",
    "position",
    "is_active",
    "owner_id",
    "category_id",
    "priority",
    "date_due",
    "color_id",
    "reference",
)

TASK_DETAIL_FIELDS = (
    *TASK_SUMMARY_FIELDS,
    "project_id",
    "date_modification",
    "description",
    "nb_comments",
    "nb_subtasks",
)
TASK_EMPTY_SENTINEL_FIELDS = {"reference"}
TASK_ZERO_SENTINEL_FIELDS = {"date_due"}


def include_task_field(field: str, value: Any) -> bool:
    """Return whether a task projection field carries useful information."""
    if value is None:
        return False
    if value == "" and field in TASK_EMPTY_SENTINEL_FIELDS:
        return False
    if value == 0 and field in TASK_ZERO_SENTINEL_FIELDS:
        return False
    return True


def summarize_task(task: Any) -> Any:
    """Return the compact task projection used by read/list/search tools."""
    if not isinstance(task, dict):
        return task

    return {
        field: task[field]
        for field in TASK_SUMMARY_FIELDS
        if field in task and include_task_field(field, task[field])
    }


def detail_task(task: Any) -> Any:
    """Return the single-task projection including body and useful counts."""
    if not isinstance(task, dict):
        return task

    return {
        field: task[field]
        for field in TASK_DETAIL_FIELDS
        if field in task and include_task_field(field, task[field])
    }


def enrich_task_counts(task: Any, task_id: int, client: KanboardClient) -> Any:
    """Populate comment/subtask counts when Kanboard's get_task omits them."""
    if not isinstance(task, dict):
        return task

    enriched_task = dict(task)
    if "nb_comments" not in enriched_task:
        comments = client.call_api(method_name="get_all_comments", task_id=task_id)
        enriched_task["nb_comments"] = len(comments) if comments else 0
    if "nb_subtasks" not in enriched_task:
        subtasks = client.call_api(method_name="get_all_subtasks", task_id=task_id)
        enriched_task["nb_subtasks"] = len(subtasks) if subtasks else 0
    return enriched_task


def summarize_tasks(tasks: Any) -> Any:
    """Return compact task projections while preserving non-list API results."""
    if not isinstance(tasks, list):
        return tasks

    return [summarize_task(task) for task in tasks]


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register task-related tools."""

    @mcp.tool()
    def moveTaskPosition(
        project_id: int, task_id: int, column_id: int, position: int, swimlane_id: int
    ) -> dict[str, Any]:
        """Move a task to a board position."""
        try:
            success = client.call_api(
                method_name="move_task_position",
                project_id=project_id,
                task_id=task_id,
                column_id=column_id,
                position=position,
                swimlane_id=swimlane_id,
            )
            return {"success": True, "data": {"moved": success}}
        except KanboardClientError as e:
            logger.error(f"Error moving task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def moveTaskToColumnByName(
        project_id: int,
        task_id: int,
        column_name: str,
        position: int = 1,
        swimlane_name: str = "Default swimlane",
    ) -> dict[str, Any]:
        """Move a task to a column by resolving column and swimlane names."""
        try:
            columns = client.call_api(method_name="get_columns", project_id=project_id)
            column_id = None
            for column in columns or []:
                if str(column.get("title", "")).casefold() == column_name.casefold():
                    column_id = int(column["id"])
                    break

            if column_id is None:
                return {
                    "success": False,
                    "error": f"Column '{column_name}' not found in project {project_id}",
                }

            swimlane_id = None
            swimlanes = client.call_api(
                method_name="get_active_swimlanes", project_id=project_id
            )
            normalized_swimlane = swimlane_name.casefold()
            for swimlane in swimlanes or []:
                if str(swimlane.get("name", "")).casefold() == normalized_swimlane:
                    swimlane_id = int(swimlane["id"])
                    break

            if swimlane_id is None and swimlane_name == "Default swimlane":
                for swimlane in swimlanes or []:
                    if str(swimlane.get("is_active", "1")) == "1":
                        swimlane_id = int(swimlane["id"])
                        break

            if swimlane_id is None:
                return {
                    "success": False,
                    "error": f"Swimlane '{swimlane_name}' not found in project {project_id}",
                }

            success = client.call_api(
                method_name="move_task_position",
                project_id=project_id,
                task_id=task_id,
                column_id=column_id,
                position=position,
                swimlane_id=swimlane_id,
            )
            return {
                "success": True,
                "data": {
                    "moved": success,
                    "column_id": column_id,
                    "swimlane_id": swimlane_id,
                },
            }
        except KanboardClientError as e:
            logger.error(f"Error moving task {task_id} to column '{column_name}': {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def batchCreateTasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """Create multiple tasks by looping create_task."""
        results = []
        for task_data in tasks:
            try:
                task_id = client.call_api(method_name="create_task", **task_data)
                results.append({"success": True, "data": {"task_id": task_id}})
            except KanboardClientError as e:
                logger.error(f"Error batch creating task: {e}")
                results.append({"success": False, "error": str(e), "input": task_data})

        return {
            "success": all(result["success"] for result in results),
            "data": results,
            "count": len(results),
        }

    @mcp.tool()
    def batchMoveTasks(moves: list[dict[str, int]]) -> dict[str, Any]:
        """Move multiple tasks by looping move_task_position."""
        results = []
        for move_data in moves:
            try:
                success = client.call_api(method_name="move_task_position", **move_data)
                results.append({"success": True, "data": {"moved": success}})
            except KanboardClientError as e:
                logger.error(f"Error batch moving task: {e}")
                results.append({"success": False, "error": str(e), "input": move_data})

        return {
            "success": all(result["success"] for result in results),
            "data": results,
            "count": len(results),
        }

    @mcp.tool()
    def getAllTasks(project_id: int, status_id: int | None = None) -> dict[str, Any]:
        """Get all tasks for a project."""
        try:
            if status_id is not None:
                tasks = client.call_api(
                    method_name="get_all_tasks",
                    project_id=project_id,
                    status_id=status_id,
                )
            else:
                tasks = client.call_api(
                    method_name="get_all_tasks", project_id=project_id
                )

            return {
                "success": True,
                "data": summarize_tasks(tasks),
                "count": len(tasks) if tasks else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting all tasks for project {project_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getTask(task_id: int) -> dict[str, Any]:
        """Get a specific task by ID."""
        try:
            task = client.call_api(method_name="get_task", task_id=task_id)
            task = enrich_task_counts(task, task_id, client)
            return {"success": True, "data": detail_task(task)}
        except KanboardClientError as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getTaskByReference(project_id: int, reference: str) -> dict[str, Any]:
        """Get a specific task by reference."""
        try:
            task = client.call_api(
                method_name="get_task_by_reference",
                project_id=project_id,
                reference=reference,
            )
            return {"success": True, "data": summarize_task(task)}
        except KanboardClientError as e:
            logger.error(
                f"Error getting task with reference '{reference}' in project {project_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getOverdueTasks() -> dict[str, Any]:
        """Get all overdue tasks."""
        try:
            tasks = client.call_api(method_name="get_overdue_tasks")
            return {
                "success": True,
                "data": summarize_tasks(tasks),
                "count": len(tasks) if tasks else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting overdue tasks: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getOverdueTasksByProject(project_id: int) -> dict[str, Any]:
        """Get overdue tasks for a specific project."""
        try:
            tasks = client.call_api(
                method_name="get_overdue_tasks_by_project", project_id=project_id
            )
            return {
                "success": True,
                "data": summarize_tasks(tasks),
                "count": len(tasks) if tasks else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting overdue tasks for project {project_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def createTask(
        project_id: int,
        title: str,
        description: str | None = None,
        category_id: int | None = None,
        owner_id: int | None = None,
        creator_id: int | None = None,
        date_due: str | None = None,
        color_id: str | None = None,
        column_id: int | None = None,
        swimlane_id: int | None = None,
        priority: int | None = None,
        reference: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a task. Dates use YYYY-MM-DD; priority uses the project range."""
        try:
            task_data = {
                "project_id": project_id,
                "title": title,
            }

            # Add optional parameters
            if description is not None:
                task_data["description"] = description
            if category_id is not None:
                task_data["category_id"] = category_id
            if owner_id is not None:
                task_data["owner_id"] = owner_id
            if creator_id is not None:
                task_data["creator_id"] = creator_id
            if date_due is not None:
                task_data["date_due"] = date_due
            if color_id is not None:
                task_data["color_id"] = color_id
            if column_id is not None:
                task_data["column_id"] = column_id
            if swimlane_id is not None:
                task_data["swimlane_id"] = swimlane_id
            if priority is not None:
                task_data["priority"] = priority
            if reference is not None:
                task_data["reference"] = reference
            if tags is not None:
                task_data["tags"] = tags

            task_id = client.call_api(method_name="create_task", **task_data)
            return {"success": True, "data": {"task_id": task_id}}
        except KanboardClientError as e:
            logger.error(f"Error creating task: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def updateTask(
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        category_id: int | None = None,
        owner_id: int | None = None,
        date_due: str | None = None,
        color_id: str | None = None,
        priority: int | None = None,
        reference: str | None = None,
    ) -> dict[str, Any]:
        """Update a task. Dates use YYYY-MM-DD; priority uses the project range."""
        try:
            task_data = {"id": task_id}

            # Add optional parameters
            if title is not None:
                task_data["title"] = title
            if description is not None:
                task_data["description"] = description
            if category_id is not None:
                task_data["category_id"] = category_id
            if owner_id is not None:
                task_data["owner_id"] = owner_id
            if date_due is not None:
                task_data["date_due"] = date_due
            if color_id is not None:
                task_data["color_id"] = color_id
            if priority is not None:
                task_data["priority"] = priority
            if reference is not None:
                task_data["reference"] = reference

            success = client.call_api(method_name="update_task", **task_data)
            return {"success": True, "data": {"updated": success}}
        except KanboardClientError as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def openTask(task_id: int) -> dict[str, Any]:
        """Open a task (set status to open)."""
        try:
            success = client.call_api(method_name="open_task", task_id=task_id)
            return {"success": True, "data": {"opened": success}}
        except KanboardClientError as e:
            logger.error(f"Error opening task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def closeTask(task_id: int) -> dict[str, Any]:
        """Close a task (set status to closed)."""
        try:
            success = client.call_api(method_name="close_task", task_id=task_id)
            return {"success": True, "data": {"closed": success}}
        except KanboardClientError as e:
            logger.error(f"Error closing task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def removeTask(task_id: int) -> dict[str, Any]:
        """Remove (delete) a task."""
        try:
            success = client.call_api(method_name="remove_task", task_id=task_id)
            return {"success": True, "data": {"removed": success}}
        except KanboardClientError as e:
            logger.error(f"Error removing task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def searchTasks(
        project_id: int,
        query: str,
    ) -> dict[str, Any]:
        """Search tasks in a project with Kanboard search syntax.

        This tool accepts only project_id and query. Put all filters inside
        query; do not pass status_id, category_id, owner_id, due_date, or
        description as separate parameters. Free text searches task ID/title.
        Use explicit filters for other fields, for example:
        status:open dependency bounds
        status:closed category:1234
        description:"runtime dependencies" category:1234 assignee:username
        due:2026-06-01

        """
        try:
            tasks = client.call_api(
                method_name="search_tasks", project_id=project_id, query=query
            )
            return {
                "success": True,
                "data": summarize_tasks(tasks),
                "count": len(tasks) if tasks else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error searching tasks: {e}")
            return {"success": False, "error": str(e)}
