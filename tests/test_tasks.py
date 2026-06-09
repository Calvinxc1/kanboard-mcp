import inspect

from conftest import ScriptedClient

from kanboard_mcp.client import KanboardClientError
from kanboard_mcp.tools.tasks import register_tools


def test_create_task_sends_required_and_optional_fields(fake_mcp):
    client = ScriptedClient(responses=[123])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["createTask"](
        project_id=1,
        title="Install rack shelf",
        description="Use short screws",
        owner_id=5,
        tags=["homelab", "hardware"],
        recurrence_status=1,
        recurrence_trigger=1,
        recurrence_timeframe=1,
        recurrence_basedate=0,
        recurrence_factor=3,
    )

    assert result == {"success": True, "data": {"task_id": 123}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {
                "method_name": "create_task",
                "project_id": 1,
                "title": "Install rack shelf",
                "description": "Use short screws",
                "owner_id": 5,
                "tags": ["homelab", "hardware"],
                "recurrence_status": 1,
                "recurrence_trigger": 1,
                "recurrence_timeframe": 1,
                "recurrence_basedate": 0,
                "recurrence_factor": 3,
            },
        }
    ]


def test_update_task_omits_unset_optional_fields(fake_mcp):
    client = ScriptedClient(responses=[True])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateTask"](task_id=42, title="New title")

    assert result == {"success": True, "data": {"updated": True}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {"method_name": "update_task", "id": 42, "title": "New title"},
        }
    ]


def test_update_task_passes_recurrence_fields(fake_mcp):
    client = ScriptedClient(responses=[True])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateTask"](
        task_id=90,
        recurrence_status=1,
        recurrence_trigger=1,
        recurrence_timeframe=1,
        recurrence_basedate=0,
        recurrence_factor=3,
    )

    assert result == {"success": True, "data": {"updated": True}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {
                "method_name": "update_task",
                "id": 90,
                "recurrence_status": 1,
                "recurrence_trigger": 1,
                "recurrence_timeframe": 1,
                "recurrence_basedate": 0,
                "recurrence_factor": 3,
            },
        }
    ]


def test_move_task_to_column_by_name_resolves_column_and_swimlane(fake_mcp):
    client = ScriptedClient(
        responses=[
            [{"id": "8", "title": "Doing"}],
            [{"id": "2", "name": "Default swimlane", "is_active": "1"}],
            True,
        ]
    )
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["moveTaskToColumnByName"](
        project_id=1,
        task_id=42,
        column_name="doing",
    )

    assert result == {
        "success": True,
        "data": {"moved": True, "column_id": 8, "swimlane_id": 2},
    }
    assert client.calls[-1] == {
        "args": (),
        "kwargs": {
            "method_name": "move_task_position",
            "project_id": 1,
            "task_id": 42,
            "column_id": 8,
            "position": 1,
            "swimlane_id": 2,
        },
    }


def test_move_task_to_column_by_name_reports_missing_column(fake_mcp):
    client = ScriptedClient(responses=[[{"id": "3", "title": "Backlog"}]])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["moveTaskToColumnByName"](
        project_id=1,
        task_id=42,
        column_name="Doing",
    )

    assert result == {
        "success": False,
        "error": "Column 'Doing' not found in project 1",
    }
    assert len(client.calls) == 1


def test_batch_create_tasks_returns_partial_failures(fake_mcp):
    client = ScriptedClient(responses=[101, KanboardClientError("boom")])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["batchCreateTasks"](
        [{"project_id": 1, "title": "one"}, {"project_id": 1, "title": "two"}]
    )

    assert result["success"] is False
    assert result["count"] == 2
    assert result["data"][0] == {"success": True, "data": {"task_id": 101}}
    assert result["data"][1]["success"] is False
    assert result["data"][1]["error"] == "boom"


def test_move_task_position_uses_keyword_method_name(fake_mcp):
    client = ScriptedClient(responses=[True])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["moveTaskPosition"](
        project_id=1,
        task_id=42,
        column_id=8,
        position=2,
        swimlane_id=3,
    )

    assert result == {"success": True, "data": {"moved": True}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {
                "method_name": "move_task_position",
                "project_id": 1,
                "task_id": 42,
                "column_id": 8,
                "position": 2,
                "swimlane_id": 3,
            },
        }
    ]


def test_batch_move_tasks_returns_partial_failures(fake_mcp):
    client = ScriptedClient(responses=[True, KanboardClientError("blocked")])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["batchMoveTasks"](
        [
            {
                "project_id": 1,
                "task_id": 1,
                "column_id": 2,
                "position": 1,
                "swimlane_id": 3,
            },
            {
                "project_id": 1,
                "task_id": 2,
                "column_id": 2,
                "position": 1,
                "swimlane_id": 3,
            },
        ]
    )

    assert result["success"] is False
    assert result["count"] == 2
    assert result["data"][0] == {"success": True, "data": {"moved": True}}
    assert result["data"][1]["error"] == "blocked"


def test_get_all_tasks_includes_status_only_when_provided(fake_mcp):
    full_task = {
        "id": 42,
        "title": "Wire rack",
        "column_id": 6,
        "swimlane_id": 1,
        "is_active": 0,
        "owner_id": 0,
        "category_id": 0,
        "priority": 2,
        "date_modification": 1780366986,
        "date_due": 0,
        "reference": "",
        "url": "https://kanboard.example.test/task/42",
        "recurrence_status": 0,
        "color": {"name": "Green", "background": "rgb(189, 244, 203)"},
    }
    client = ScriptedClient(responses=[[], [full_task]])
    register_tools(fake_mcp, client)

    assert fake_mcp.tools["getAllTasks"](project_id=1) == {
        "success": True,
        "data": [],
        "count": 0,
    }
    assert fake_mcp.tools["getAllTasks"](project_id=1, status_id=1) == {
        "success": True,
        "data": [
            {
                "id": 42,
                "title": "Wire rack",
                "column_id": 6,
                "swimlane_id": 1,
                "is_active": 0,
                "owner_id": 0,
                "category_id": 0,
                "priority": 2,
            }
        ],
        "count": 1,
    }
    assert [call["kwargs"] for call in client.calls] == [
        {"method_name": "get_all_tasks", "project_id": 1},
        {"method_name": "get_all_tasks", "project_id": 1, "status_id": 1},
    ]


def test_search_tasks_matches_kanboard_api_shape(fake_mcp):
    client = ScriptedClient(
        responses=[
            [
                {
                    "id": 42,
                    "title": "Wire rack",
                    "project_id": 1,
                    "column_id": 6,
                    "swimlane_id": 1,
                    "category_id": 0,
                    "priority": 0,
                    "date_modification": 1780366986,
                    "date_due": 0,
                    "reference": "",
                    "url": "https://kanboard.example.test/task/42",
                    "recurrence_status": 0,
                    "color": {"name": "Green"},
                }
            ]
        ]
    )
    register_tools(fake_mcp, client)

    signature = inspect.signature(fake_mcp.tools["searchTasks"])
    assert list(signature.parameters) == ["project_id", "query"]
    assert "do not pass status_id" in inspect.getdoc(fake_mcp.tools["searchTasks"])
    assert "tag:" not in inspect.getdoc(fake_mcp.tools["searchTasks"])
    assert "Free text searches task ID/title" in inspect.getdoc(
        fake_mcp.tools["searchTasks"]
    )

    result = fake_mcp.tools["searchTasks"](
        project_id=1,
        query="category:2 assignee:admin due:2026-06-01 status:open",
    )

    assert result == {
        "success": True,
        "data": [
            {
                "id": 42,
                "title": "Wire rack",
                "column_id": 6,
                "swimlane_id": 1,
                "category_id": 0,
                "priority": 0,
            }
        ],
        "count": 1,
    }
    assert client.calls == [
        {
            "args": (),
            "kwargs": {
                "method_name": "search_tasks",
                "project_id": 1,
                "query": "category:2 assignee:admin due:2026-06-01 status:open",
            },
        }
    ]


def test_task_read_and_status_wrappers(fake_mcp):
    client = ScriptedClient(
        responses=[
            {
                "id": 42,
                "title": "Build",
                "project_id": 1,
                "date_modification": 1780366986,
                "description": "Full task body",
                "reference": "",
                "date_due": 0,
                "is_active": 0,
                "category_id": 0,
                "priority": 0,
                "recurrence_status": 0,
                "recurrence_trigger": 1,
                "recurrence_timeframe": 1,
                "recurrence_basedate": 0,
                "recurrence_factor": 3,
                "color": {"name": "Green"},
            },
            [{"id": 10}, {"id": 11}],
            [{"id": 20}, {"id": 21}, {"id": 22}],
            {"id": 43, "title": "Reference", "color": {"name": "Blue"}},
            [{"id": 44, "title": "Late", "recurrence_factor": 1}],
            [{"id": 45, "title": "Late project", "external_uri": "ignored"}],
            True,
            True,
            True,
        ]
    )
    register_tools(fake_mcp, client)

    assert fake_mcp.tools["getTask"](task_id=42) == {
        "success": True,
        "data": {
            "id": 42,
            "title": "Build",
            "project_id": 1,
            "date_modification": 1780366986,
            "description": "Full task body",
            "is_active": 0,
            "category_id": 0,
            "priority": 0,
            "nb_comments": 2,
            "nb_subtasks": 3,
        },
    }
    assert fake_mcp.tools["getTaskByReference"](project_id=1, reference="REF") == {
        "success": True,
        "data": {"id": 43, "title": "Reference"},
    }
    assert fake_mcp.tools["getOverdueTasks"]() == {
        "success": True,
        "data": [{"id": 44, "title": "Late"}],
        "count": 1,
    }
    assert fake_mcp.tools["getOverdueTasksByProject"](project_id=1) == {
        "success": True,
        "data": [{"id": 45, "title": "Late project"}],
        "count": 1,
    }
    assert fake_mcp.tools["openTask"](task_id=42) == {
        "success": True,
        "data": {"opened": True},
    }
    assert fake_mcp.tools["closeTask"](task_id=42) == {
        "success": True,
        "data": {"closed": True},
    }
    assert fake_mcp.tools["removeTask"](task_id=42) == {
        "success": True,
        "data": {"removed": True},
    }


def test_get_task_returns_active_recurrence_fields(fake_mcp):
    client = ScriptedClient(
        responses=[
            {
                "id": 90,
                "title": "Quarterly maintenance",
                "project_id": 1,
                "date_due": "2026-06-30",
                "description": "Recurring maintenance",
                "recurrence_status": 1,
                "recurrence_trigger": 1,
                "recurrence_timeframe": 1,
                "recurrence_basedate": 0,
                "recurrence_factor": 3,
            },
            [],
            [],
        ]
    )
    register_tools(fake_mcp, client)

    assert fake_mcp.tools["getTask"](task_id=90) == {
        "success": True,
        "data": {
            "id": 90,
            "title": "Quarterly maintenance",
            "project_id": 1,
            "date_due": "2026-06-30",
            "description": "Recurring maintenance",
            "nb_comments": 0,
            "nb_subtasks": 0,
            "recurrence_status": 1,
            "recurrence_trigger": 1,
            "recurrence_timeframe": 1,
            "recurrence_basedate": 0,
            "recurrence_factor": 3,
        },
    }
def test_create_and_update_task_include_all_optional_fields(fake_mcp):
    client = ScriptedClient(responses=[42, True])
    register_tools(fake_mcp, client)

    fake_mcp.tools["createTask"](
        project_id=1,
        title="Build",
        description="desc",
        category_id=2,
        owner_id=3,
        creator_id=4,
        date_due="2026-06-01",
        color_id="blue",
        column_id=5,
        swimlane_id=6,
        priority=2,
        reference="REF",
        tags=["homelab"],
        recurrence_status=1,
        recurrence_trigger=1,
        recurrence_timeframe=1,
        recurrence_basedate=0,
        recurrence_factor=3,
    )
    fake_mcp.tools["updateTask"](
        task_id=42,
        title="Updated",
        description="desc",
        category_id=2,
        owner_id=3,
        date_due="2026-06-02",
        color_id="green",
        priority=1,
        reference="REF2",
        recurrence_status=1,
        recurrence_trigger=1,
        recurrence_timeframe=1,
        recurrence_basedate=0,
        recurrence_factor=3,
    )

    assert client.calls[0]["kwargs"] == {
        "method_name": "create_task",
        "project_id": 1,
        "title": "Build",
        "description": "desc",
        "category_id": 2,
        "owner_id": 3,
        "creator_id": 4,
        "date_due": "2026-06-01",
        "color_id": "blue",
        "column_id": 5,
        "swimlane_id": 6,
        "priority": 2,
        "reference": "REF",
        "tags": ["homelab"],
        "recurrence_status": 1,
        "recurrence_trigger": 1,
        "recurrence_timeframe": 1,
        "recurrence_basedate": 0,
        "recurrence_factor": 3,
    }
    assert client.calls[1]["kwargs"] == {
        "method_name": "update_task",
        "id": 42,
        "title": "Updated",
        "description": "desc",
        "category_id": 2,
        "owner_id": 3,
        "date_due": "2026-06-02",
        "color_id": "green",
        "priority": 1,
        "reference": "REF2",
        "recurrence_status": 1,
        "recurrence_trigger": 1,
        "recurrence_timeframe": 1,
        "recurrence_basedate": 0,
        "recurrence_factor": 3,
    }
