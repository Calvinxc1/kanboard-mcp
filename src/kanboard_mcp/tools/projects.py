"""Project-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register project-related tools."""

    @mcp.tool()
    def createProject(
        name: str,
        description: str | None = None,
        owner_id: int | None = None,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        """Create a new project.

        Args:
            name: The project name
            description: Optional project description
            owner_id: Optional owner user ID
            identifier: Optional project identifier
        """
        try:
            project_data = {"name": name}
            if description is not None:
                project_data["description"] = description
            if owner_id is not None:
                project_data["owner_id"] = owner_id
            if identifier is not None:
                project_data["identifier"] = identifier

            project_id = client.call_api(method_name="create_project", **project_data)
            return {"success": True, "data": {"project_id": project_id}}
        except KanboardClientError as e:
            logger.error(f"Error creating project '{name}': {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def updateProject(
        project_id: int,
        name: str | None = None,
        description: str | None = None,
        owner_id: int | None = None,
        identifier: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        priority_default: int | None = None,
        priority_start: int | None = None,
        priority_end: int | None = None,
    ) -> dict[str, Any]:
        """Update a project.

        Args:
            project_id: The ID of the project to update
            name: Optional new project name
            description: Optional new project description
            owner_id: Optional owner user ID
            identifier: Optional project identifier
            start_date: Optional project start date
            end_date: Optional project end date
            priority_default: Optional default priority for new tasks
            priority_start: Optional lowest priority value for the project
            priority_end: Optional highest priority value for the project
        """
        try:
            project_data = {"project_id": project_id}
            optional_fields = {
                "name": name,
                "description": description,
                "owner_id": owner_id,
                "identifier": identifier,
                "start_date": start_date,
                "end_date": end_date,
                "priority_default": int(priority_default)
                if priority_default is not None
                else None,
                "priority_start": int(priority_start)
                if priority_start is not None
                else None,
                "priority_end": int(priority_end) if priority_end is not None else None,
            }
            project_data.update(
                {
                    field: value
                    for field, value in optional_fields.items()
                    if value is not None
                }
            )

            success = client.call_api(method_name="update_project", **project_data)
            priority_updates = {
                field: project_data[field]
                for field in ("priority_default", "priority_start", "priority_end")
                if field in project_data
            }
            if success and priority_updates:
                updated_project = client.call_api(
                    method_name="get_project_by_id", project_id=project_id
                )
                mismatches = {}
                for field, expected in priority_updates.items():
                    actual = updated_project.get(field) if updated_project else None
                    try:
                        actual_matches = actual is not None and int(actual) == expected
                    except (TypeError, ValueError):
                        actual_matches = False
                    if not actual_matches:
                        mismatches[field] = {
                            "expected": expected,
                            "actual": actual,
                        }
                if mismatches:
                    return {
                        "success": False,
                        "error": (
                            "Kanboard accepted updateProject but did not persist "
                            "priority fields"
                        ),
                        "data": {"updated": success, "mismatches": mismatches},
                    }
            return {"success": True, "data": {"updated": success}}
        except KanboardClientError as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getAllProjects() -> dict[str, Any]:
        """Get all projects from Kanboard."""
        try:
            projects = client.call_api(method_name="get_all_projects")
            return {
                "success": True,
                "data": projects,
                "count": len(projects) if projects else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting all projects: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getProjectById(project_id: int) -> dict[str, Any]:
        """Get a specific project by ID.

        Args:
            project_id: The ID of the project to retrieve
        """
        try:
            project = client.call_api(
                method_name="get_project_by_id", project_id=project_id
            )
            return {"success": True, "data": project}
        except KanboardClientError as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getProjectByName(project_name: str) -> dict[str, Any]:
        """Get a specific project by name.

        Args:
            project_name: The name of the project to retrieve
        """
        try:
            project = client.call_api(
                method_name="get_project_by_name", project_name=project_name
            )
            return {"success": True, "data": project}
        except KanboardClientError as e:
            logger.error(f"Error getting project '{project_name}': {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getProjectActivity(project_id: int) -> dict[str, Any]:
        """Get activity for a specific project.

        Args:
            project_id: The ID of the project to get activity for
        """
        try:
            activity = client.call_api(
                method_name="get_project_activity", project_id=project_id
            )
            return {
                "success": True,
                "data": activity,
                "count": len(activity) if activity else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting project activity for {project_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getProjectActivities(project_id: int) -> dict[str, Any]:
        """Get activities for a specific project.

        Args:
            project_id: The ID of the project to get activities for
        """
        try:
            activities = client.call_api(
                method_name="get_project_activities", project_id=project_id
            )
            return {
                "success": True,
                "data": activities,
                "count": len(activities) if activities else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting project activities for {project_id}: {e}")
            return {"success": False, "error": str(e)}
