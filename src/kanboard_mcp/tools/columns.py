"""Column-related tools for Kanboard MCP Server."""

from typing import Any, Dict, List, Optional, Union
import logging

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError


logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register column-related tools."""

    @mcp.tool()
    def addColumn(
        project_id: int,
        title: str,
        task_limit: int = 0,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a column to a project.

        Args:
            project_id: The ID of the project
            title: The column title
            task_limit: Optional work-in-progress limit
            description: Optional column description
        """
        try:
            column_data = {
                "project_id": project_id,
                "title": title,
                "task_limit": task_limit,
            }
            if description is not None:
                column_data["description"] = description

            column_id = client.call_api("add_column", **column_data)
            return {
                "success": True,
                "data": {"column_id": column_id}
            }
        except KanboardClientError as e:
            logger.error(f"Error adding column '{title}' to project {project_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def updateColumn(
        column_id: int,
        title: Optional[str] = None,
        task_limit: Optional[int] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a column.

        Args:
            column_id: The ID of the column to update
            title: Optional new column title
            task_limit: Optional work-in-progress limit
            description: Optional column description
        """
        try:
            column_data = {"column_id": column_id}
            if title is not None:
                column_data["title"] = title
            if task_limit is not None:
                column_data["task_limit"] = task_limit
            if description is not None:
                column_data["description"] = description

            success = client.call_api("update_column", **column_data)
            return {
                "success": True,
                "data": {"updated": success}
            }
        except KanboardClientError as e:
            logger.error(f"Error updating column {column_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def changeColumnPosition(project_id: int, column_id: int, position: int) -> Dict[str, Any]:
        """Change a column's position in a project.

        Args:
            project_id: The ID of the project
            column_id: The ID of the column to move
            position: The new column position
        """
        try:
            success = client.call_api(
                "change_column_position",
                project_id=project_id,
                column_id=column_id,
                position=position,
            )
            return {
                "success": True,
                "data": {"moved": success}
            }
        except KanboardClientError as e:
            logger.error(f"Error moving column {column_id} in project {project_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def getColumns(project_id: int) -> Dict[str, Any]:
        """Get all columns for a project.

        Args:
            project_id: The ID of the project to get columns for
        """
        try:
            columns = client.call_api("get_columns", project_id=project_id)
            return {
                "success": True,
                "data": columns,
                "count": len(columns) if columns else 0
            }
        except KanboardClientError as e:
            logger.error(f"Error getting columns for project {project_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def getColumnByName(project_id: int, name: str) -> Dict[str, Any]:
        """Get a column by title within a project.

        Args:
            project_id: The ID of the project
            name: The column title to match
        """
        try:
            columns = client.call_api("get_columns", project_id=project_id)
            normalized_name = name.casefold()
            for column in columns or []:
                if str(column.get("title", "")).casefold() == normalized_name:
                    return {
                        "success": True,
                        "data": column
                    }

            return {
                "success": False,
                "error": f"Column '{name}' not found in project {project_id}"
            }
        except KanboardClientError as e:
            logger.error(f"Error finding column '{name}' in project {project_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def getColumn(column_id: int) -> Dict[str, Any]:
        """Get a specific column by ID.

        Args:
            column_id: The ID of the column to retrieve
        """
        try:
            column = client.call_api("get_column", column_id=column_id)
            return {
                "success": True,
                "data": column
            }
        except KanboardClientError as e:
            logger.error(f"Error getting column {column_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
