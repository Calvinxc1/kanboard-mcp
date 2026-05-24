"""Swimlane-related tools for Kanboard MCP Server."""

from typing import Any, Dict, Optional
import logging

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError


logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register swimlane-related tools."""

    @mcp.tool()
    def addSwimlane(
        project_id: int,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a swimlane to a project.

        Args:
            project_id: The ID of the project
            name: The swimlane name
            description: Optional swimlane description
        """
        try:
            swimlane_data = {
                "project_id": project_id,
                "name": name,
            }
            if description is not None:
                swimlane_data["description"] = description

            swimlane_id = client.call_api(method_name="add_swimlane", **swimlane_data)
            return {
                "success": True,
                "data": {"swimlane_id": swimlane_id}
            }
        except KanboardClientError as e:
            logger.error(f"Error adding swimlane '{name}' to project {project_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def updateSwimlane(
        project_id: int,
        swimlane_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a swimlane.

        Args:
            project_id: The ID of the project
            swimlane_id: The ID of the swimlane to update
            name: Optional new swimlane name
            description: Optional new swimlane description
        """
        try:
            swimlane_data = {
                "project_id": project_id,
                "swimlane_id": swimlane_id,
            }
            if name is not None:
                swimlane_data["name"] = name
            if description is not None:
                swimlane_data["description"] = description

            success = client.call_api(method_name="update_swimlane", **swimlane_data)
            return {
                "success": True,
                "data": {"updated": success}
            }
        except KanboardClientError as e:
            logger.error(f"Error updating swimlane {swimlane_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def changeSwimlanePosition(
        project_id: int,
        swimlane_id: int,
        position: int
    ) -> Dict[str, Any]:
        """Change a swimlane's position in a project.

        Args:
            project_id: The ID of the project
            swimlane_id: The ID of the swimlane to move
            position: The new swimlane position
        """
        try:
            success = client.call_api(
                "change_swimlane_position",
                project_id=project_id,
                swimlane_id=swimlane_id,
                position=position,
            )
            return {
                "success": True,
                "data": {"moved": success}
            }
        except KanboardClientError as e:
            logger.error(f"Error moving swimlane {swimlane_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def getActiveSwimlanes(project_id: int) -> Dict[str, Any]:
        """Get active swimlanes for a project.

        Args:
            project_id: The ID of the project
        """
        try:
            swimlanes = client.call_api(method_name="get_active_swimlanes", project_id=project_id)
            return {
                "success": True,
                "data": swimlanes,
                "count": len(swimlanes) if swimlanes else 0
            }
        except KanboardClientError as e:
            logger.error(f"Error getting active swimlanes for project {project_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
