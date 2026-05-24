from conftest import ScriptedClient

from kanboard_mcp.tools.tags import register_tools


def test_set_task_tags_resolves_project_id_before_setting_tags(fake_mcp):
    client = ScriptedClient(responses=[{"id": "42", "project_id": "7"}, True])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["setTaskTags"](task_id=42, tags=["new", "homelab"])

    assert result == {"success": True, "data": {"updated": True}}
    assert client.calls == [
        {"args": (), "kwargs": {"method_name": "get_task", "task_id": 42}},
        {
            "args": (),
            "kwargs": {
                "method_name": "set_task_tags",
                "project_id": 7,
                "task_id": 42,
                "tags": ["new", "homelab"],
            },
        },
    ]


def test_set_task_tags_reports_missing_project_id(fake_mcp):
    client = ScriptedClient(responses=[{"id": "42"}])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["setTaskTags"](task_id=42, tags=["homelab"])

    assert result == {
        "success": False,
        "error": "Unable to resolve project_id for task 42",
    }
