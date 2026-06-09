"""Project-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError

logger = logging.getLogger(__name__)

PROJECT_SUMMARY_FIELDS = (
    "id",
    "name",
    "identifier",
    "is_active",
    "description",
    "priority_start",
    "priority_end",
)
PROJECT_ZERO_VALUE_FIELDS = {"priority_start", "priority_end"}


def include_project_summary_field(field: str, value: Any) -> bool:
    """Return whether a project summary field carries useful information."""
    if value in (None, ""):
        return False
    return value != 0 or field in PROJECT_ZERO_VALUE_FIELDS


def summarize_project(project: Any) -> Any:
    """Return the compact project projection used by project list reads."""
    if not isinstance(project, dict):
        return project

    return {
        field: project[field]
        for field in PROJECT_SUMMARY_FIELDS
        if field in project and include_project_summary_field(field, project[field])
    }


def summarize_projects(projects: Any) -> Any:
    """Return compact project projections while preserving non-list API results."""
    if not isinstance(projects, list):
        return projects

    return [summarize_project(project) for project in projects]


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register project-related tools."""

    @mcp.tool()
    def createProject(
        name: str,
        description: str | None = None,
        owner_id: int | None = None,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        """Create a new project."""
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
        """Update a project."""
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
            summarized_projects = summarize_projects(projects)
            return {
                "success": True,
                "data": summarized_projects,
                "count": len(projects) if projects else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting all projects: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getProjectById(project_id: int) -> dict[str, Any]:
        """Get a specific project by ID."""
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
        """Get a specific project by name."""
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
        """Get activity for a specific project."""
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
        """Get activities for a specific project."""
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
