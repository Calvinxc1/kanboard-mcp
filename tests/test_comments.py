from conftest import ScriptedClient

from kanboard_mcp.tools.comments import register_tools


def test_create_comment_resolves_current_user_when_user_id_omitted(fake_mcp):
    client = ScriptedClient(responses=[{"id": "9"}, 88])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["createComment"](task_id=42, content="Done")

    assert result == {"success": True, "data": {"comment_id": 88}}
    assert client.calls == [
        {"args": (), "kwargs": {"method_name": "get_me"}},
        {
            "args": (),
            "kwargs": {
                "method_name": "create_comment",
                "task_id": 42,
                "content": "Done",
                "user_id": 9,
            },
        },
    ]


def test_update_comment_uses_kanboard_comment_id_parameter(fake_mcp):
    client = ScriptedClient(responses=[True])
    register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateComment"](comment_id=7, content="Revised")

    assert result == {"success": True, "data": {"updated": True}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {
                "method_name": "update_comment",
                "id": 7,
                "content": "Revised",
            },
        }
    ]


def test_comment_read_and_remove_wrappers(fake_mcp):
    client = ScriptedClient(responses=[{"id": 7}, [{"id": 7}], True])
    register_tools(fake_mcp, client)

    assert fake_mcp.tools["getComment"](comment_id=7) == {
        "success": True,
        "data": {"id": 7},
    }
    assert fake_mcp.tools["getAllComments"](task_id=42) == {
        "success": True,
        "data": [{"id": 7}],
        "count": 1,
    }
    assert fake_mcp.tools["removeComment"](comment_id=7) == {
        "success": True,
        "data": {"removed": True},
    }
    assert [call["kwargs"] for call in client.calls] == [
        {"method_name": "get_comment", "comment_id": 7},
        {"method_name": "get_all_comments", "task_id": 42},
        {"method_name": "remove_comment", "comment_id": 7},
    ]
