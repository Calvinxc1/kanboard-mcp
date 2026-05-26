"""Helpers for redacting secret fields from Kanboard API responses."""

from typing import Any


def redact_user_record(user: Any) -> Any:
    """Return a copy of a Kanboard user dict with secret fields stripped.

    Drops api_access_token and password entirely. Masks twofactor_secret with
    the string "[redacted]" when present and not null. The user-level token
    field is left intact because Kanboard documents it separately from API
    access tokens.
    """
    if not isinstance(user, dict):
        return user

    drop_keys = {"api_access_token", "password"}
    sanitized = {k: v for k, v in user.items() if k not in drop_keys}
    if sanitized.get("twofactor_secret") is not None:
        sanitized["twofactor_secret"] = "[redacted]"

    return sanitized
