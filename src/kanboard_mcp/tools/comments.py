"""Comment-related tools for Kanboard MCP Server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import KanboardClient, KanboardClientError

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: KanboardClient) -> None:
    """Register comment-related tools."""

    @mcp.tool()
    def createComment(
        task_id: int, content: str, user_id: int | None = None
    ) -> dict[str, Any]:
        """Create a new comment on a task.

        Args:
            task_id: The ID of the task to comment on
            content: The content of the comment
            user_id: The ID of the user creating the comment (optional)
        """
        try:
            comment_data = {"task_id": task_id, "content": content}

            if user_id is not None:
                comment_data["user_id"] = user_id
            else:
                user = client.call_api(method_name="get_me")
                comment_data["user_id"] = int(user["id"])

            comment_id = client.call_api(method_name="create_comment", **comment_data)
            return {"success": True, "data": {"comment_id": comment_id}}
        except KanboardClientError as e:
            logger.error(f"Error creating comment: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getComment(comment_id: int) -> dict[str, Any]:
        """Get a specific comment by ID.

        Args:
            comment_id: The ID of the comment to retrieve
        """
        try:
            comment = client.call_api(method_name="get_comment", comment_id=comment_id)
            return {"success": True, "data": comment}
        except KanboardClientError as e:
            logger.error(f"Error getting comment {comment_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def getAllComments(task_id: int) -> dict[str, Any]:
        """Get all comments for a task.

        Args:
            task_id: The ID of the task to get comments for
        """
        try:
            comments = client.call_api(method_name="get_all_comments", task_id=task_id)
            return {
                "success": True,
                "data": comments,
                "count": len(comments) if comments else 0,
            }
        except KanboardClientError as e:
            logger.error(f"Error getting all comments for task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def updateComment(comment_id: int, content: str) -> dict[str, Any]:
        """Update an existing comment.

        Args:
            comment_id: The ID of the comment to update
            content: The new content of the comment
        """
        try:
            success = client.call_api(
                method_name="update_comment",
                id=comment_id,
                content=content,
            )
            return {"success": True, "data": {"updated": success}}
        except KanboardClientError as e:
            logger.error(f"Error updating comment {comment_id}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def removeComment(comment_id: int) -> dict[str, Any]:
        """Remove (delete) a comment.

        Args:
            comment_id: The ID of the comment to remove
        """
        try:
            success = client.call_api(
                method_name="remove_comment", comment_id=comment_id
            )
            return {"success": True, "data": {"removed": success}}
        except KanboardClientError as e:
            logger.error(f"Error removing comment {comment_id}: {e}")
            return {"success": False, "error": str(e)}
