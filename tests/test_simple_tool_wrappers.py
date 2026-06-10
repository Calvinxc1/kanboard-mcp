import pytest
from conftest import ScriptedClient

from kanboard_mcp.client import KanboardClientError
from kanboard_mcp.tools import (
    boards,
    categories,
    files,
    links,
    projects,
    subtasks,
    tags,
    users,
)


@pytest.mark.parametrize(
    (
        "module",
        "tool_name",
        "tool_kwargs",
        "api_response",
        "expected",
        "expected_kwargs",
    ),
    [
        (
            boards,
            "getBoard",
            {"project_id": 1},
            {
                "columns": [
                    {
                        "id": 6,
                        "title": "Doing",
                        "project_id": 1,
                        "tasks": [
                            {
                                "id": 42,
                                "title": "Wire rack",
                                "project_id": 1,
                                "column_id": 6,
                                "swimlane_id": 1,
                                "description": "large body omitted",
                                "recurrence_status": 0,
                                "project_name": "Homelab",
                                "nb_comments": 3,
                            }
                        ],
                    }
                ]
            },
            {
                "success": True,
                "data": {
                    "columns": [
                        {
                            "id": 6,
                            "title": "Doing",
                            "tasks": [
                                {"id": 42, "title": "Wire rack"}
                            ],
                        }
                    ]
                },
            },
            {"method_name": "get_board", "project_id": 1},
        ),
        (
            categories,
            "createCategory",
            {"project_id": 1, "name": "Ops", "color_id": "blue"},
            11,
            {"success": True, "data": {"category_id": 11}},
            {
                "method_name": "create_category",
                "project_id": 1,
                "name": "Ops",
                "color_id": "blue",
            },
        ),
        (
            categories,
            "updateCategory",
            {"category_id": 11, "name": "Infra"},
            True,
            {"success": True, "data": {"updated": True}},
            {"method_name": "update_category", "id": 11, "name": "Infra"},
        ),
        (
            categories,
            "getCategory",
            {"category_id": 11},
            {"id": 11},
            {"success": True, "data": {"id": 11}},
            {"method_name": "get_category", "category_id": 11},
        ),
        (
            categories,
            "getAllCategories",
            {"project_id": 1},
            [{"id": 11}],
            {"success": True, "data": [{"id": 11}], "count": 1},
            {"method_name": "get_all_categories", "project_id": 1},
        ),
        (
            files,
            "createTaskFile",
            {"task_id": 42, "filename": "note.txt", "blob": "Ym9keQ=="},
            9,
            {"success": True, "data": {"file_id": 9}},
            {
                "method_name": "create_task_file",
                "task_id": 42,
                "filename": "note.txt",
                "blob": "Ym9keQ==",
            },
        ),
        (
            files,
            "getAllTaskFiles",
            {"task_id": 42},
            [{"id": 9}],
            {"success": True, "data": [{"id": 9}], "count": 1},
            {"method_name": "get_all_task_files", "task_id": 42},
        ),
        (
            files,
            "getTaskFile",
            {"file_id": 9},
            {"id": 9},
            {"success": True, "data": {"id": 9}},
            {"method_name": "get_task_file", "file_id": 9},
        ),
        (
            files,
            "downloadTaskFile",
            {"file_id": 9},
            "Ym9keQ==",
            {"success": True, "data": {"content": "Ym9keQ=="}},
            {"method_name": "download_task_file", "file_id": 9},
        ),
        (
            files,
            "removeTaskFile",
            {"file_id": 9},
            True,
            {"success": True, "data": {"removed": True}},
            {"method_name": "remove_task_file", "file_id": 9},
        ),
        (
            files,
            "removeAllTaskFiles",
            {"task_id": 42},
            True,
            {"success": True, "data": {"removed": True}},
            {"method_name": "remove_all_task_files", "task_id": 42},
        ),
        (
            projects,
            "createProject",
            {"name": "Homelab", "description": "Ops", "owner_id": 2},
            1,
            {"success": True, "data": {"project_id": 1}},
            {
                "method_name": "create_project",
                "name": "Homelab",
                "description": "Ops",
                "owner_id": 2,
            },
        ),
        (
            projects,
            "getAllProjects",
            {},
            [
                {
                    "id": 1,
                    "name": "Homelab",
                    "identifier": "",
                    "is_active": 1,
                    "description": "Local infrastructure",
                    "priority_start": 1,
                    "priority_end": 5,
                    "priority_default": 3,
                    "token": "",
                    "email": None,
                    "url": {"board": "https://kanboard.example.test/board/1"},
                    "task_limit": 0,
                },
                {
                    "id": 2,
                    "name": "Career",
                    "identifier": "CAREER",
                    "is_active": 1,
                    "description": "",
                    "priority_start": 0,
                    "priority_end": 3,
                    "url": {"board": "https://kanboard.example.test/board/2"},
                }
            ],
            {
                "success": True,
                "data": [
                    {
                        "id": 1,
                        "name": "Homelab",
                        "is_active": 1,
                        "description": "Local infrastructure",
                        "priority_start": 1,
                        "priority_end": 5,
                    },
                    {
                        "id": 2,
                        "name": "Career",
                        "identifier": "CAREER",
                        "is_active": 1,
                        "priority_start": 0,
                        "priority_end": 3,
                    },
                ],
                "count": 2,
            },
            {"method_name": "get_all_projects"},
        ),
        (
            projects,
            "getProjectById",
            {"project_id": 1},
            {"id": 1},
            {"success": True, "data": {"id": 1}},
            {"method_name": "get_project_by_id", "project_id": 1},
        ),
        (
            projects,
            "getProjectByName",
            {"project_name": "Homelab"},
            {"id": 1},
            {"success": True, "data": {"id": 1}},
            {"method_name": "get_project_by_name", "project_name": "Homelab"},
        ),
        (
            projects,
            "getProjectActivity",
            {"project_id": 1},
            [{"event": "task.create"}],
            {"success": True, "data": [{"event": "task.create"}], "count": 1},
            {"method_name": "get_project_activity", "project_id": 1},
        ),
        (
            projects,
            "getProjectActivities",
            {"project_id": 1},
            [{"event": "task.update"}],
            {"success": True, "data": [{"event": "task.update"}], "count": 1},
            {"method_name": "get_project_activities", "project_id": 1},
        ),
        (
            subtasks,
            "createSubtask",
            {"task_id": 42, "title": "Cable", "user_id": 2, "status": 1},
            14,
            {"success": True, "data": {"subtask_id": 14}},
            {
                "method_name": "create_subtask",
                "task_id": 42,
                "title": "Cable",
                "user_id": 2,
                "status": 1,
            },
        ),
        (
            subtasks,
            "getSubtask",
            {"subtask_id": 14},
            {"id": 14},
            {"success": True, "data": {"id": 14}},
            {"method_name": "get_subtask", "subtask_id": 14},
        ),
        (
            subtasks,
            "getAllSubtasks",
            {"task_id": 42},
            [{"id": 14}],
            {"success": True, "data": [{"id": 14}], "count": 1},
            {"method_name": "get_all_subtasks", "task_id": 42},
        ),
        (
            subtasks,
            "removeSubtask",
            {"subtask_id": 14},
            True,
            {"success": True, "data": {"removed": True}},
            {"method_name": "remove_subtask", "subtask_id": 14},
        ),
        (
            tags,
            "getAllTags",
            {},
            [{"name": "homelab"}],
            {"success": True, "data": [{"name": "homelab"}], "count": 1},
            {"method_name": "get_all_tags"},
        ),
        (
            tags,
            "getTagsByProject",
            {"project_id": 1},
            [{"name": "homelab"}],
            {"success": True, "data": [{"name": "homelab"}], "count": 1},
            {"method_name": "get_tags_by_project", "project_id": 1},
        ),
        (
            tags,
            "getTaskTags",
            {"task_id": 42},
            [{"name": "homelab"}],
            {"success": True, "data": [{"name": "homelab"}], "count": 1},
            {"method_name": "get_task_tags", "task_id": 42},
        ),
        (
            users,
            "getUser",
            {"user_id": 2},
            {"id": 2},
            {"success": True, "data": {"id": 2}},
            {"method_name": "get_user", "user_id": 2},
        ),
        (
            users,
            "getUserByName",
            {"username": "jcherry"},
            {"id": 2},
            {"success": True, "data": {"id": 2}},
            {"method_name": "get_user_by_name", "username": "jcherry"},
        ),
        (
            users,
            "getAllUsers",
            {},
            [{"id": 2}],
            {"success": True, "data": [{"id": 2}], "count": 1},
            {"method_name": "get_all_users"},
        ),
        (
            users,
            "getMe",
            {},
            {"id": 2},
            {"success": True, "data": {"id": 2}},
            {"method_name": "get_me"},
        ),
        (
            users,
            "getMyDashboard",
            {},
            {"tasks": []},
            {"success": True, "data": {"tasks": []}},
            {"method_name": "get_my_dashboard"},
        ),
        (
            users,
            "getMyActivityStream",
            {},
            [{"event": "login"}],
            {"success": True, "data": [{"event": "login"}], "count": 1},
            {"method_name": "get_my_activity_stream"},
        ),
        (
            users,
            "getMyProjectsList",
            {},
            [{"id": 1}],
            {"success": True, "data": [{"id": 1}], "count": 1},
            {"method_name": "get_my_projects_list"},
        ),
        (
            users,
            "getMyOverdueTasks",
            {},
            [{"id": 42}],
            {"success": True, "data": [{"id": 42}], "count": 1},
            {"method_name": "get_my_overdue_tasks"},
        ),
        (
            users,
            "getMyProjects",
            {},
            [{"id": 1}],
            {"success": True, "data": [{"id": 1}], "count": 1},
            {"method_name": "get_my_projects"},
        ),
    ],
)
def test_simple_tool_wrapper_success(
    fake_mcp,
    module,
    tool_name,
    tool_kwargs,
    api_response,
    expected,
    expected_kwargs,
):
    client = ScriptedClient(responses=[api_response])
    module.register_tools(fake_mcp, client)

    result = fake_mcp.tools[tool_name](**tool_kwargs)

    assert result == expected
    assert client.calls == [{"args": (), "kwargs": expected_kwargs}]


def test_update_subtask_resolves_parent_task_id_before_update(fake_mcp):
    client = ScriptedClient(responses=[{"id": 14, "task_id": 42}, True])
    subtasks.register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateSubtask"](
        subtask_id=14, title="Cable neatly", time_spent=1
    )

    assert result == {"success": True, "data": {"updated": True}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {"method_name": "get_subtask", "subtask_id": 14},
        },
        {
            "args": (),
            "kwargs": {
                "method_name": "update_subtask",
                "id": 14,
                "task_id": 42,
                "title": "Cable neatly",
                "time_spent": 1,
            },
        },
    ]


def test_update_subtask_returns_error_when_parent_task_id_is_unavailable(fake_mcp):
    client = ScriptedClient(responses=[{"id": 14}])
    subtasks.register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateSubtask"](subtask_id=14, status=2)

    assert result == {
        "success": False,
        "error": "Unable to resolve task_id for subtask 14",
    }
    assert client.calls == [
        {
            "args": (),
            "kwargs": {"method_name": "get_subtask", "subtask_id": 14},
        }
    ]


def test_update_project_sends_minimal_project_id_and_name_payload(fake_mcp):
    client = ScriptedClient(responses=[True])
    projects.register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateProject"](project_id=1, name="Homelab")

    assert result == {"success": True, "data": {"updated": True}}
    assert client.calls == [
        {
            "args": (),
            "kwargs": {
                "method_name": "update_project",
                "project_id": 1,
                "name": "Homelab",
            },
        }
    ]


def test_update_project_drops_none_values_and_uses_project_id_param(fake_mcp):
    client = ScriptedClient(responses=[True])
    projects.register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateProject"](
        project_id=1,
        name="Homelab",
        description=None,
        owner_id=None,
        identifier=None,
        start_date=None,
        end_date=None,
        priority_default=None,
        priority_start=None,
        priority_end=None,
    )

    assert result == {"success": True, "data": {"updated": True}}
    update_kwargs = client.calls[0]["kwargs"]
    assert update_kwargs == {
        "method_name": "update_project",
        "project_id": 1,
        "name": "Homelab",
    }
    assert "id" not in update_kwargs
    assert all(value is not None for value in update_kwargs.values())


def test_update_project_sets_priority_range_and_get_all_projects_reads_it_back(
    fake_mcp,
):
    project_after_update = {
        "id": 1,
        "name": "Homelab",
        "description": "Local infrastructure",
        "identifier": "HOMELAB",
        "priority_start": 1,
        "priority_end": 5,
        "priority_default": 3,
    }
    client = ScriptedClient(responses=[True, project_after_update, [project_after_update]])
    projects.register_tools(fake_mcp, client)

    update_result = fake_mcp.tools["updateProject"](
        project_id=1,
        priority_start=1,
        priority_end=5,
        priority_default=3,
    )
    readback_result = fake_mcp.tools["getAllProjects"]()

    assert update_result == {"success": True, "data": {"updated": True}}
    assert readback_result == {
        "success": True,
        "data": [
            {
                "id": 1,
                "name": "Homelab",
                "description": "Local infrastructure",
                "identifier": "HOMELAB",
                "priority_start": 1,
                "priority_end": 5,
            }
        ],
        "count": 1,
    }
    assert readback_result["data"][0]["name"] == "Homelab"
    assert readback_result["data"][0]["description"] == "Local infrastructure"
    assert readback_result["data"][0]["identifier"] == "HOMELAB"
    assert readback_result["data"][0]["priority_start"] == 1
    assert readback_result["data"][0]["priority_end"] == 5
    assert "priority_default" not in readback_result["data"][0]
    update_kwargs = client.calls[0]["kwargs"]
    assert "id" not in update_kwargs
    assert "name" not in update_kwargs
    assert "description" not in update_kwargs
    assert "identifier" not in update_kwargs
    assert all(value is not None for value in update_kwargs.values())
    assert [call["kwargs"] for call in client.calls] == [
        {
            "method_name": "update_project",
            "project_id": 1,
            "priority_start": 1,
            "priority_end": 5,
            "priority_default": 3,
        },
        {"method_name": "get_project_by_id", "project_id": 1},
        {"method_name": "get_all_projects"},
    ]


def test_update_project_reports_priority_fields_that_do_not_persist(fake_mcp):
    client = ScriptedClient(
        responses=[
            True,
            {
                "id": 1,
                "name": "Homelab",
                "description": "Local infrastructure",
                "identifier": "HOMELAB",
                "priority_start": 0,
                "priority_end": 3,
                "priority_default": 0,
            },
        ]
    )
    projects.register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateProject"](
        project_id=1,
        priority_start=1,
        priority_end=5,
        priority_default=3,
    )

    assert result == {
        "success": False,
        "error": "Kanboard accepted updateProject but did not persist priority fields",
        "data": {
            "updated": True,
            "mismatches": {
                "priority_default": {"expected": 3, "actual": 0},
                "priority_start": {"expected": 1, "actual": 0},
                "priority_end": {"expected": 5, "actual": 3},
            },
        },
    }
    assert [call["kwargs"] for call in client.calls] == [
        {
            "method_name": "update_project",
            "project_id": 1,
            "priority_start": 1,
            "priority_end": 5,
            "priority_default": 3,
        },
        {"method_name": "get_project_by_id", "project_id": 1},
    ]


def test_update_project_reports_non_integer_priority_readback_as_mismatch(fake_mcp):
    client = ScriptedClient(
        responses=[
            True,
            {
                "id": 1,
                "priority_start": "not-an-int",
                "priority_end": "5",
                "priority_default": "3",
            },
        ]
    )
    projects.register_tools(fake_mcp, client)

    result = fake_mcp.tools["updateProject"](
        project_id=1,
        priority_start=1,
        priority_end=5,
        priority_default=3,
    )

    assert result == {
        "success": False,
        "error": "Kanboard accepted updateProject but did not persist priority fields",
        "data": {
            "updated": True,
            "mismatches": {
                "priority_start": {"expected": 1, "actual": "not-an-int"},
            },
        },
    }


@pytest.mark.parametrize(
    ("tool_name", "tool_kwargs", "method_kwargs"),
    [
        ("getUser", {"user_id": 2}, {"method_name": "get_user", "user_id": 2}),
        (
            "getUserByName",
            {"username": "jcherry"},
            {"method_name": "get_user_by_name", "username": "jcherry"},
        ),
        ("getMe", {}, {"method_name": "get_me"}),
    ],
)
def test_user_tools_redact_single_user_records(
    fake_mcp, tool_name, tool_kwargs, method_kwargs
):
    user_record = {
        "id": 2,
        "username": "jcherry",
        "email": "jcherry@example.test",
        "twofactor_secret": "otp-secret",
        "twofactor_activated": True,
        "api_access_token": "personal-api-token",
        "password": "$2y$10$password-hash",
    }
    client = ScriptedClient(responses=[user_record])
    users.register_tools(fake_mcp, client)

    result = fake_mcp.tools[tool_name](**tool_kwargs)

    assert result == {
        "success": True,
        "data": {
            "id": 2,
            "username": "jcherry",
            "email": "jcherry@example.test",
            "twofactor_secret": "[redacted]",
            "twofactor_activated": True,
        },
    }
    assert client.calls == [{"args": (), "kwargs": method_kwargs}]


def test_get_all_users_redacts_each_user_record(fake_mcp):
    user_records = [
        {
            "id": 2,
            "username": "jcherry",
            "twofactor_secret": "otp-secret",
            "api_access_token": "personal-api-token",
            "password": "$2y$10$password-hash",
        },
        {
            "id": 3,
            "username": "test",
            "twofactor_secret": None,
            "api_access_token": "other-api-token",
            "password": "$2y$10$other-password-hash",
        },
    ]
    client = ScriptedClient(responses=[user_records])
    users.register_tools(fake_mcp, client)

    result = fake_mcp.tools["getAllUsers"]()

    assert result == {
        "success": True,
        "data": [
            {
                "id": 2,
                "username": "jcherry",
                "twofactor_secret": "[redacted]",
            },
            {"id": 3, "username": "test", "twofactor_secret": None},
        ],
        "count": 2,
    }
    assert client.calls == [{"args": (), "kwargs": {"method_name": "get_all_users"}}]


def test_simple_tool_wrapper_error_shape(fake_mcp):
    client = ScriptedClient(responses=[KanboardClientError("nope")])
    projects.register_tools(fake_mcp, client)

    result = fake_mcp.tools["getAllProjects"]()

    assert result == {"success": False, "error": "nope"}


def test_get_board_summarizes_top_level_column_list(fake_mcp):
    raw_board = [
        {
            "id": 6,
            "title": "Doing",
            "project_id": 1,
            "tasks": [
                {
                    "id": 42,
                    "title": "Wire rack",
                    "project_id": 1,
                    "column_id": 6,
                    "swimlane_id": 1,
                    "is_active": 0,
                    "category_id": 0,
                    "priority": 0,
                    "description": "large body omitted",
                    "project_name": "Homelab",
                    "column_name": "Doing",
                    "swimlane_name": "Default swimlane",
                    "recurrence_status": 0,
                    "recurrence_trigger": 0,
                    "assignee_avatar_path": None,
                    "is_draggable": True,
                    "is_milestone": False,
                    "nb_comments": 3,
                    "nb_subtasks": 2,
                }
            ],
        }
    ]
    client = ScriptedClient(responses=[raw_board])
    boards.register_tools(fake_mcp, client)

    result = fake_mcp.tools["getBoard"](project_id=1)

    assert result == {
        "success": True,
        "data": [
            {
                "id": 6,
                "title": "Doing",
                "tasks": [
                    {
                        "id": 42,
                        "title": "Wire rack",
                        "is_active": 0,
                        "category_id": 0,
                        "priority": 0,
                    }
                ],
            }
        ],
    }


def test_get_board_summarizes_live_swimlane_column_shape(fake_mcp):
    raw_board = [
        {
            "id": 1,
            "name": "Default swimlane",
            "columns": [
                {
                    "id": 6,
                    "title": "Doing",
                    "project_id": 1,
                    "description": "",
                    "column_nb_open_tasks": 1,
                    "nb_open_tasks": 1,
                    "nb_tasks": 1,
                    "nb_visible_tasks_across_swimlane": 1,
                    "nb_unfiltered_tasks_across_swimlane": 1,
                    "cumulative_score_across_swimlane": 0,
                    "score": 0,
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Wire rack",
                            "project_id": 1,
                            "column_id": 6,
                            "swimlane_id": 1,
                            "is_active": 0,
                            "category_id": 0,
                            "priority": 0,
                            "description": "large body omitted",
                            "project_name": "Homelab",
                            "column_name": "Doing",
                            "swimlane_name": "Default swimlane",
                            "recurrence_factor": 0,
                            "assignee_avatar_path": None,
                            "nb_comments": 3,
                        }
                    ],
                }
            ],
        }
    ]
    client = ScriptedClient(responses=[raw_board])
    boards.register_tools(fake_mcp, client)

    result = fake_mcp.tools["getBoard"](project_id=1)

    assert result == {
        "success": True,
        "data": [
            {
                "id": 1,
                "name": "Default swimlane",
                "columns": [
                    {
                        "id": 6,
                        "title": "Doing",
                        "nb_open_tasks": 1,
                        "tasks": [
                            {
                                "id": 42,
                                "title": "Wire rack",
                                "is_active": 0,
                                "category_id": 0,
                                "priority": 0,
                            }
                        ],
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    ("module", "tool_name", "tool_kwargs", "responses", "expected", "expected_calls"),
    [
        (
            links,
            "createTaskLink",
            {"task_id": 1, "opposite_task_id": 2, "link_id": 3},
            [True],
            {"success": True, "data": {"created": True}},
            [
                {
                    "method_name": "create_task_link",
                    "task_id": 1,
                    "opposite_task_id": 2,
                    "link_id": 3,
                }
            ],
        ),
        (
            links,
            "updateTaskLink",
            {"task_link_id": 4, "task_id": 1, "opposite_task_id": 2, "link_id": 3},
            [True],
            {"success": True, "data": {"updated": True}},
            [
                {
                    "method_name": "update_task_link",
                    "task_link_id": 4,
                    "task_id": 1,
                    "opposite_task_id": 2,
                    "link_id": 3,
                }
            ],
        ),
        (
            links,
            "getAllLinks",
            {},
            [[{"id": 3}]],
            {"success": True, "data": [{"id": 3}], "count": 1},
            [{"method_name": "get_all_links"}],
        ),
        (
            links,
            "getTaskLinkById",
            {"task_link_id": 4},
            [{"id": 4}],
            {"success": True, "data": {"id": 4}},
            [{"method_name": "get_task_link_by_id", "task_link_id": 4}],
        ),
        (
            links,
            "getAllTaskLinks",
            {"task_id": 42},
            [[{"id": 4}]],
            {"success": True, "data": [{"id": 4}], "count": 1},
            [{"method_name": "get_all_task_links", "task_id": 42}],
        ),
        (
            links,
            "removeTaskLink",
            {"task_link_id": 4},
            [True],
            {"success": True, "data": {"removed": True}},
            [{"method_name": "remove_task_link", "task_link_id": 4}],
        ),
        (
            links,
            "getOppositeLinkId",
            {"link_id": 3},
            [4],
            {"success": True, "data": {"opposite_link_id": 4}},
            [{"method_name": "get_opposite_link_id", "link_id": 3}],
        ),
        (
            links,
            "getLinkByLabel",
            {"label": "blocks"},
            [{"id": 3}],
            {"success": True, "data": {"id": 3}},
            [{"method_name": "get_link_by_label", "label": "blocks"}],
        ),
        (
            links,
            "getLinkById",
            {"link_id": 3},
            [{"id": 3}],
            {"success": True, "data": {"id": 3}},
            [{"method_name": "get_link_by_id", "link_id": 3}],
        ),
        (
            links,
            "createLink",
            {"label": "blocks", "opposite_label": "blocked by"},
            [3],
            {"success": True, "data": {"link_id": 3}},
            [
                {
                    "method_name": "create_link",
                    "label": "blocks",
                    "opposite_label": "blocked by",
                }
            ],
        ),
        (
            links,
            "updateLink",
            {"link_id": 3, "label": "blocks", "opposite_label": "blocked by"},
            [True],
            {"success": True, "data": {"updated": True}},
            [
                {
                    "method_name": "update_link",
                    "link_id": 3,
                    "label": "blocks",
                    "opposite_label": "blocked by",
                }
            ],
        ),
        (
            links,
            "removeLink",
            {"link_id": 3},
            [True],
            {"success": True, "data": {"removed": True}},
            [{"method_name": "remove_link", "link_id": 3}],
        ),
    ],
)
def test_link_wrapper_calls(
    fake_mcp,
    module,
    tool_name,
    tool_kwargs,
    responses,
    expected,
    expected_calls,
):
    client = ScriptedClient(responses=responses)
    module.register_tools(fake_mcp, client)

    result = fake_mcp.tools[tool_name](**tool_kwargs)

    assert result == expected
    assert [call["kwargs"] for call in client.calls] == expected_calls


@pytest.mark.parametrize(
    ("module", "tool_name", "tool_kwargs"),
    [
        (boards, "getBoard", {"project_id": 1}),
        (categories, "getCategory", {"category_id": 11}),
        (files, "getTaskFile", {"file_id": 9}),
        (links, "getLinkById", {"link_id": 3}),
        (projects, "getProjectById", {"project_id": 1}),
        (subtasks, "getSubtask", {"subtask_id": 14}),
        (tags, "getTaskTags", {"task_id": 42}),
        (users, "getUser", {"user_id": 2}),
    ],
)
def test_tool_modules_return_error_payloads(fake_mcp, module, tool_name, tool_kwargs):
    client = ScriptedClient(responses=[KanboardClientError("api failed")])
    module.register_tools(fake_mcp, client)

    result = fake_mcp.tools[tool_name](**tool_kwargs)

    assert result == {"success": False, "error": "api failed"}
