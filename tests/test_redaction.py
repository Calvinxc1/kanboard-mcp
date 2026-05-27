from kanboard_mcp.redaction import redact_user_record


def test_redact_user_record_drops_secret_fields_and_masks_twofactor_secret():
    user = {
        "id": 2,
        "username": "jcherry",
        "name": "John Cherry",
        "email": "jcherry@example.test",
        "role": "app-user",
        "is_active": "1",
        "is_admin": "1",
        "is_project_admin": "0",
        "avatar_path": "avatars/jcherry.png",
        "twofactor_activated": True,
        "twofactor_secret": "otp-secret",
        "api_access_token": "personal-api-token",
        "password": "$2y$10$password-hash",
        "token": "",
    }

    redacted = redact_user_record(user)

    assert redacted == {
        "id": 2,
        "username": "jcherry",
        "name": "John Cherry",
        "email": "jcherry@example.test",
        "role": "app-user",
        "is_active": "1",
        "is_admin": "1",
        "is_project_admin": "0",
        "avatar_path": "avatars/jcherry.png",
        "twofactor_activated": True,
        "twofactor_secret": "[redacted]",
        "token": "",
    }
    assert user["api_access_token"] == "personal-api-token"
    assert user["password"] == "$2y$10$password-hash"
    assert user["twofactor_secret"] == "otp-secret"


def test_redact_user_record_leaves_null_twofactor_secret():
    user = {
        "id": 2,
        "twofactor_secret": None,
        "api_access_token": "personal-api-token",
        "password": "$2y$10$password-hash",
    }

    redacted = redact_user_record(user)

    assert redacted == {"id": 2, "twofactor_secret": None}


def test_redact_user_record_without_dropped_fields_only_applies_twofactor_rule():
    user = {
        "id": 2,
        "username": "jcherry",
        "twofactor_secret": "otp-secret",
        "is_admin": "1",
        "is_project_admin": "0",
    }

    redacted = redact_user_record(user)

    assert redacted == {
        "id": 2,
        "username": "jcherry",
        "twofactor_secret": "[redacted]",
        "is_admin": "1",
        "is_project_admin": "0",
    }


def test_redact_user_record_ignores_non_dict_values():
    assert redact_user_record(None) is None
    assert redact_user_record(["not", "a", "dict"]) == ["not", "a", "dict"]
