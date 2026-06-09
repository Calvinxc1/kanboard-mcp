"""Board-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError
from .tasks import summarize_task

logger = logging.getLogger(__name__)

BOARD_ITEM_FIELDS = {
    "id",
    "name",
    "title",
    "project_id",
    "position",
    "is_active",
    "task_limit",
    "nb_open_tasks",
    "nb_columns",
    "nb_swimlanes",
}

BOARD_TASK_CONTEXT_FIELDS = {"project_id", "column_id", "swimlane_id"}
BOARD_COLUMN_CONTEXT_FIELDS = {"project_id"}


def summarize_board(board: Any) -> Any:
    """Return a compact board shape with summarized tasks per column."""
    if isinstance(board, list):
        return [summarize_board_item(item) for item in board]

    if not isinstance(board, dict):
        return board

    return summarize_board_item(board)


def summarize_board_item(item: dict[str, Any]) -> dict[str, Any]:
    """Return a board/swimlane/column dictionary with compact nested tasks."""
    summarized_item = {field: item[field] for field in BOARD_ITEM_FIELDS if field in item}

    tasks = item.get("tasks")
    if isinstance(tasks, list):
        for field in BOARD_COLUMN_CONTEXT_FIELDS:
            summarized_item.pop(field, None)
        summarized_item["tasks"] = summarize_board_tasks(tasks)

    columns = item.get("columns")
    if isinstance(columns, list):
        summarized_item["columns"] = summarize_board_columns(columns)

    return summarized_item


def summarize_board_columns(columns: list[Any]) -> list[Any]:
    """Return board columns with compact nested task cards."""
    summarized_columns = []
    for column in columns:
        if not isinstance(column, dict):
            summarized_columns.append(column)
            continue

        summarized_columns.append(summarize_board_item(column))

    return summarized_columns


def summarize_board_tasks(tasks: list[Any]) -> list[Any]:
    """Return task cards without IDs already implied by board nesting."""
    summarized_tasks = []
    for task in tasks:
        summarized_task = summarize_task(task)
        if isinstance(summarized_task, dict):
            for field in BOARD_TASK_CONTEXT_FIELDS:
                summarized_task.pop(field, None)
        summarized_tasks.append(summarized_task)

    return summarized_tasks


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register board-related tools."""

    @mcp.tool()
    def getBoard(project_id: int) -> dict[str, Any]:
        """Get board information for a project."""
        try:
            board = client.call_api(method_name="get_board", project_id=project_id)
            return {"success": True, "data": summarize_board(board)}
        except KanboardClientError as e:
            logger.error(f"Error getting board for project {project_id}: {e}")
            return {"success": False, "error": str(e)}
