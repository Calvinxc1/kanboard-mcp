from conftest import ScriptedClient

from kanboard_mcp.tools.columns import register_tools as register_column_tools
from kanboard_mcp.tools.swimlanes import register_tools as register_swimlane_tools


def test_change_column_position_uses_keyword_method_name(fake_mcp):
    client = ScriptedClient(responses=[True])
    register_column_tools(fake_mcp, client)

    result = fake_mcp.tools["changeColumnPosition"](
        project_id=1,
        column_id=8,
        position=2,
    )

    assert result == {"success": True, "data": {"moved": True}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {
                "method_name": "change_column_position",
                "project_id": 1,
                "column_id": 8,
                "position": 2,
            },
        }
    ]


def test_change_swimlane_position_uses_keyword_method_name(fake_mcp):
    client = ScriptedClient(responses=[True])
    register_swimlane_tools(fake_mcp, client)

    result = fake_mcp.tools["changeSwimlanePosition"](
        project_id=1,
        swimlane_id=3,
        position=2,
    )

    assert result == {"success": True, "data": {"moved": True}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {
                "method_name": "change_swimlane_position",
                "project_id": 1,
                "swimlane_id": 3,
                "position": 2,
            },
        }
    ]


def test_column_wrappers_cover_create_update_lookup_paths(fake_mcp):
    client = ScriptedClient(
        responses=[
            8,
            True,
            [{"id": "8", "title": "Doing"}],
            [{"id": "8", "title": "Doing"}],
            {"id": "8"},
        ]
    )
    register_column_tools(fake_mcp, client)

    assert fake_mcp.tools["addColumn"](
        project_id=1,
        title="Doing",
        task_limit=3,
        description="Active work",
    ) == {"success": True, "data": {"column_id": 8}}
    assert fake_mcp.tools["updateColumn"](
        column_id=8,
        title="In Progress",
        task_limit=4,
    ) == {"success": True, "data": {"updated": True}}
    assert fake_mcp.tools["getColumns"](project_id=1)["count"] == 1
    assert fake_mcp.tools["getColumnByName"](project_id=1, name="doing") == {
        "success": True,
        "data": {"id": "8", "title": "Doing"},
    }
    assert fake_mcp.tools["getColumn"](column_id=8) == {
        "success": True,
        "data": {"id": "8"},
    }


def test_get_column_by_name_reports_not_found(fake_mcp):
    client = ScriptedClient(responses=[[{"id": "1", "title": "Backlog"}]])
    register_column_tools(fake_mcp, client)

    assert fake_mcp.tools["getColumnByName"](project_id=1, name="Doing") == {
        "success": False,
        "error": "Column 'Doing' not found in project 1",
    }


def test_swimlane_wrappers_cover_create_update_and_list(fake_mcp):
    client = ScriptedClient(responses=[3, True, [{"id": "3"}]])
    register_swimlane_tools(fake_mcp, client)

    assert fake_mcp.tools["addSwimlane"](
        project_id=1,
        name="Ops",
        description="Operations",
    ) == {"success": True, "data": {"swimlane_id": 3}}
    assert fake_mcp.tools["updateSwimlane"](
        project_id=1,
        swimlane_id=3,
        name="Operations",
    ) == {"success": True, "data": {"updated": True}}
    assert fake_mcp.tools["getActiveSwimlanes"](project_id=1) == {
        "success": True,
        "data": [{"id": "3"}],
        "count": 1,
    }
