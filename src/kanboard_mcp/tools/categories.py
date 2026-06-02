"""Category-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register category-related tools."""

    @mcp.tool()
    def createCategory(
        project_id: int, name: str, color_id: str | None = None
    ) -> dict[str, Any]:
        """Create a category in a project.

        Args:
            project_id: The ID of the project
            name: The category name
            color_id: Optional Kanboard color ID
        """
        try:
            category_data = {
                "project_id": project_id,
                "name": name,
            }
            if color_id is not None:
                category_data["color_id"] = color_id

            category_id = client.call_api(
                method_name="create_category", **category_data
            )
            return {"success": True, "data": {"category_id": category_id}}
        except KanboardClientError as e:
            logger.error(
                f"Error creating category '{name}' in project {project_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def updateCategory(
        category_id: int, name: str | None = None, color_id: str | None = None
    ) -> dict[str, Any]:
        """Update a category.

        Args:
            category_id: The ID of the category to update
            name: Optional new category name
            color_id: Optional Kanboard color ID
        """
        try:
            category_data = {"id": category_id}
            if name is not None:
                category_data["name"] = name
            if color_id is not None:
                category_data["color_id"] = color_id

            success = client.call_api(method_name="update_category", **category_data)
            return {"success": True, "data": {"updated": success}}
        except KanboardClientError as e:
            logger.error(f"Error updating category {category_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getCategory(category_id: int) -> dict[str, Any]:
        """Get a specific category by ID.

        Args:
            category_id: The ID of the category to retrieve
        """
        try:
            category = client.call_api(
                method_name="get_category", category_id=category_id
            )
            return {"success": True, "data": category}
        except KanboardClientError as e:
            logger.error(f"Error getting category {category_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getAllCategories(project_id: int) -> dict[str, Any]:
        """Get all categories for a project.

        Args:
            project_id: The ID of the project to get categories for
        """
        try:
            categories = client.call_api(
                method_name="get_all_categories", project_id=project_id
            )
            return {
                "success": True,
                "data": categories,
                "count": len(categories) if categories else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting all categories for project {project_id}: {e}")
            return {"success": False, "error": str(e)}
