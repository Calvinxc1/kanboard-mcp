"""Link-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError

logger = logging.getLogger(__name__)

LINK_TYPE_SUMMARY_FIELDS = ("id", "label", "opposite_id", "opposite_label")
TASK_LINK_SUMMARY_FIELDS = (
    "id",
    "link_id",
    "label",
    "opposite_task_id",
    "opposite_title",
    "is_active",
)


def summarize_link_type(link: Any) -> Any:
    """Return compact link type fields for list responses."""
    if not isinstance(link, dict):
        return link

    return {
        field: link[field]
        for field in LINK_TYPE_SUMMARY_FIELDS
        if field in link and link[field] not in (None, "")
    }


def summarize_link_types(links: Any) -> Any:
    """Return compact link type projections while preserving non-list API results."""
    if not isinstance(links, list):
        return links

    return [summarize_link_type(link) for link in links]


def summarize_task_link(link: Any) -> Any:
    """Return compact task link fields for list responses."""
    if not isinstance(link, dict):
        return link

    return {
        field: link[field]
        for field in TASK_LINK_SUMMARY_FIELDS
        if field in link and link[field] not in (None, "")
    }


def summarize_task_links(links: Any) -> Any:
    """Return compact task link projections while preserving non-list API results."""
    if not isinstance(links, list):
        return links

    return [summarize_task_link(link) for link in links]


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register link-related tools."""

    @mcp.tool()
    def createTaskLink(
        task_id: int, opposite_task_id: int, link_id: int
    ) -> dict[str, Any]:
        """Create a link between two tasks."""
        try:
            success = client.call_api(
                method_name="create_task_link",
                task_id=task_id,
                opposite_task_id=opposite_task_id,
                link_id=link_id,
            )
            return {"success": True, "data": {"created": success}}
        except KanboardClientError as e:
            logger.error(f"Error creating task link: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def updateTaskLink(
        task_link_id: int, task_id: int, opposite_task_id: int, link_id: int
    ) -> dict[str, Any]:
        """Update an existing task link."""
        try:
            success = client.call_api(
                method_name="update_task_link",
                task_link_id=task_link_id,
                task_id=task_id,
                opposite_task_id=opposite_task_id,
                link_id=link_id,
            )
            return {"success": True, "data": {"updated": success}}
        except KanboardClientError as e:
            logger.error(f"Error updating task link {task_link_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getTaskLinkById(task_link_id: int) -> dict[str, Any]:
        """Get a specific task link by ID."""
        try:
            link = client.call_api(
                method_name="get_task_link_by_id", task_link_id=task_link_id
            )
            return {"success": True, "data": link}
        except KanboardClientError as e:
            logger.error(f"Error getting task link {task_link_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getAllTaskLinks(task_id: int) -> dict[str, Any]:
        """Get all links for a task."""
        try:
            links = client.call_api(method_name="get_all_task_links", task_id=task_id)
            return {
                "success": True,
                "data": summarize_task_links(links),
                "count": len(links) if links else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting all task links for task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def removeTaskLink(task_link_id: int) -> dict[str, Any]:
        """Remove (delete) a task link."""
        try:
            success = client.call_api(
                method_name="remove_task_link", task_link_id=task_link_id
            )
            return {"success": True, "data": {"removed": success}}
        except KanboardClientError as e:
            logger.error(f"Error removing task link {task_link_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getAllLinks() -> dict[str, Any]:
        """Get all available link types."""
        try:
            links = client.call_api(method_name="get_all_links")
            return {
                "success": True,
                "data": summarize_link_types(links),
                "count": len(links) if links else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting all links: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getOppositeLinkId(link_id: int) -> dict[str, Any]:
        """Get the opposite link ID for a given link."""
        try:
            opposite_id = client.call_api(
                method_name="get_opposite_link_id", link_id=link_id
            )
            return {"success": True, "data": {"opposite_link_id": opposite_id}}
        except KanboardClientError as e:
            logger.error(f"Error getting opposite link ID for {link_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getLinkByLabel(label: str) -> dict[str, Any]:
        """Get a link by its label."""
        try:
            link = client.call_api(method_name="get_link_by_label", label=label)
            return {"success": True, "data": link}
        except KanboardClientError as e:
            logger.error(f"Error getting link by label '{label}': {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getLinkById(link_id: int) -> dict[str, Any]:
        """Get a link by its ID."""
        try:
            link = client.call_api(method_name="get_link_by_id", link_id=link_id)
            return {"success": True, "data": link}
        except KanboardClientError as e:
            logger.error(f"Error getting link {link_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def createLink(label: str, opposite_label: str) -> dict[str, Any]:
        """Create a new link type."""
        try:
            link_id = client.call_api(
                method_name="create_link", label=label, opposite_label=opposite_label
            )
            return {"success": True, "data": {"link_id": link_id}}
        except KanboardClientError as e:
            logger.error(f"Error creating link: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def updateLink(link_id: int, label: str, opposite_label: str) -> dict[str, Any]:
        """Update an existing link type."""
        try:
            success = client.call_api(
                method_name="update_link",
                link_id=link_id,
                label=label,
                opposite_label=opposite_label,
            )
            return {"success": True, "data": {"updated": success}}
        except KanboardClientError as e:
            logger.error(f"Error updating link {link_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def removeLink(link_id: int) -> dict[str, Any]:
        """Remove (delete) a link type."""
        try:
            success = client.call_api(method_name="remove_link", link_id=link_id)
            return {"success": True, "data": {"removed": success}}
        except KanboardClientError as e:
            logger.error(f"Error removing link {link_id}: {e}")
            return {"success": False, "error": str(e)}
