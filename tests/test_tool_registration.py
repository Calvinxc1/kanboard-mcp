from conftest import FakeMCP, ScriptedClient

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
        "updateComment",
        "changeColumnPosition",
        "changeSwimlanePosition",
        "getAllProjects",
        "getColumns",
        "getAllUsers",
        "createTaskFile",
        "createTaskLink",
    }
