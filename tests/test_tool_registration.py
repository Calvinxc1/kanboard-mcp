from conftest import FakeMCP, ScriptedClient

from kanboard_mcp.config import Config, KanboardConfig
from kanboard_mcp.server import create_server
from kanboard_mcp.tools import (
    boards,
    categories,
    columns,
    comments,
    files,
    links,
    projects,
    subtasks,
    swimlanes,
    tags,
    tasks,
    users,
)


def test_all_tool_modules_register_expected_tools():
    mcp = FakeMCP()
    client = ScriptedClient()

    for module in (
        boards,
        categories,
        columns,
        comments,
        files,
        links,
        projects,
        subtasks,
        swimlanes,
        tags,
        tasks,
        users,
    ):
        module.register_tools(mcp, client)

    assert set(mcp.tools) >= {
        "createTask",
        "updateTask",
        "moveTaskToColumnByName",
        "getTask",
        "setTaskTags",
        "getTaskTags",
        "createComment",
        "createSubtask",
        "getAllSubtasks",
        "updateComment",
        "changeColumnPosition",
        "changeSwimlanePosition",
        "getAllProjects",
        "getColumns",
        "getAllUsers",
        "createTaskFile",
        "createTaskLink",
    }


def test_default_core_profile_registers_subtask_helper_tools():
    config = Config(
        kanboard=KanboardConfig(
            url="http://example.invalid/jsonrpc.php",
            username="jsonrpc",
            password="redacted",
        )
    )

    server = create_server(config)

    tool_names = {tool.name for tool in server.mcp._tool_manager.list_tools()}
    assert {"createSubtask", "getAllSubtasks", "getMe"} <= tool_names
