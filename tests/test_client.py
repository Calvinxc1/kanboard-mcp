from urllib.error import HTTPError

import kanboard
import pytest

from kanboard_mcp.client import (
    KanboardAPIError,
    KanboardAuthenticationError,
    KanboardClient,
    KanboardClientError,
    KanboardConnectionError,
    create_client,
)
from kanboard_mcp.config import Config, KanboardConfig, MCPServerConfig


class FakeKanboardApi:
    def __init__(self):
        self.calls = []
        self.failures = []

    def get_me(self):
        self.calls.append(("get_me", {}, {}))
        return {"id": "1", "name": "Jason"}

    def get_version(self):
        self.calls.append(("get_version", {}, {}))
        return "1.2.3"

    def get_task(self, **kwargs):
        self.calls.append(("get_task", {}, kwargs))
        if self.failures:
            failure = self.failures.pop(0)
            if failure is not None:
                raise failure
        return {"id": kwargs["task_id"]}


def make_config(max_retries=0, retry_delay=0, debug=False):
    return Config(
        kanboard=KanboardConfig(
            url="https://kanboard.example.test/jsonrpc.php",
            password="token",
        ),
        server=MCPServerConfig(
            max_retries=max_retries,
            retry_delay=retry_delay,
            debug=debug,
        ),
    )


def make_client(fake_api=None, **config_kwargs):
    client = KanboardClient(make_config(**config_kwargs))
    client._client = fake_api or FakeKanboardApi()
    client._connected = True
    return client


def test_parse_response_returns_result():
    response = b'{"jsonrpc":"2.0","result":{"ok":true},"id":1}'

    assert KanboardClient._parse_response_with_error_details(response) == {"ok": True}


def test_parse_response_preserves_json_rpc_error_code():
    response = b'{"jsonrpc":"2.0","error":{"code":-32602,"message":"Invalid params"},"id":1}'

    with pytest.raises(KanboardAPIError) as exc_info:
        KanboardClient._parse_response_with_error_details(response)

    assert exc_info.value.code == -32602
    assert str(exc_info.value) == "JSON-RPC error -32602: Invalid params"


def test_parse_response_rejects_empty_and_invalid_json():
    with pytest.raises(KanboardAPIError, match="Empty response"):
        KanboardClient._parse_response_with_error_details(b"")

    with pytest.raises(KanboardAPIError, match="Failed to parse JSON response"):
        KanboardClient._parse_response_with_error_details(b"{")


def test_connect_marks_client_connected(monkeypatch):
    fake_api = FakeKanboardApi()

    def fake_kanboard_client(**kwargs):
        fake_api.client_kwargs = kwargs
        return fake_api

    monkeypatch.setattr("kanboard_mcp.client.kanboard.Client", fake_kanboard_client)
    client = KanboardClient(make_config())

    client.connect()

    assert client.is_connected() is True
    assert fake_api.client_kwargs["url"] == "https://kanboard.example.test/jsonrpc.php"
    assert fake_api.client_kwargs["auth_header"] == "Authorization"
    assert fake_api.client_kwargs["insecure"] is False


def test_create_client_returns_kanboard_client():
    client = create_client(make_config())

    assert isinstance(client, KanboardClient)


def test_connect_preserves_authentication_error_when_get_me_returns_none(monkeypatch):
    fake_api = FakeKanboardApi()
    fake_api.get_me = lambda: None
    monkeypatch.setattr("kanboard_mcp.client.kanboard.Client", lambda **_: fake_api)
    client = KanboardClient(make_config())

    with pytest.raises(KanboardAuthenticationError, match="invalid credentials"):
        client.connect()


def test_create_client_failure_is_connection_error(monkeypatch):
    def fail_create(**_):
        raise RuntimeError("bad constructor")

    monkeypatch.setattr("kanboard_mcp.client.kanboard.Client", fail_create)
    client = KanboardClient(make_config())

    with pytest.raises(KanboardConnectionError, match="Failed to create Kanboard client"):
        client.connect()


def test_connect_maps_kanboard_client_error_to_authentication_error(monkeypatch):
    def fail_get_me():
        raise kanboard.ClientError("bad credentials")

    fake_api = FakeKanboardApi()
    fake_api.get_me = fail_get_me
    monkeypatch.setattr("kanboard_mcp.client.kanboard.Client", lambda **_: fake_api)
    client = KanboardClient(make_config())

    with pytest.raises(KanboardAuthenticationError, match="Authentication failed"):
        client.connect()


def test_execute_with_retry_retries_transient_exception(monkeypatch):
    fake_api = FakeKanboardApi()
    fake_api.failures = [RuntimeError("temporary"), None]
    client = make_client(fake_api=fake_api, max_retries=1)
    monkeypatch.setattr("kanboard_mcp.client.time.sleep", lambda _: None)

    result = client.call_api(method_name="get_task", task_id=42)

    assert result == {"id": 42}
    assert len(fake_api.calls) == 2


def test_execute_with_retry_maps_json_rpc_error_without_retry():
    client = make_client()
    client._client.failures = [KanboardAPIError("Invalid params", code=-32602)]

    with pytest.raises(KanboardAPIError) as exc_info:
        client.call_api(method_name="get_task", task_id=42)

    assert exc_info.value.code == -32602


def test_execute_with_retry_maps_http_authentication_error():
    client = make_client()
    client._client.failures = [
        HTTPError(
            url="https://kanboard.example.test/jsonrpc.php",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
    ]

    with pytest.raises(KanboardAuthenticationError, match="Authentication failed"):
        client.call_api(method_name="get_task", task_id=42)


def test_execute_with_retry_maps_http_client_error():
    client = make_client()
    client._client.failures = [
        HTTPError(
            url="https://kanboard.example.test/jsonrpc.php",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )
    ]

    with pytest.raises(KanboardAPIError) as exc_info:
        client.call_api(method_name="get_task", task_id=42)

    assert exc_info.value.code == 403


def test_execute_with_retry_retries_http_server_error_then_exhausts(monkeypatch):
    client = make_client(max_retries=1)
    client._client.failures = [
        HTTPError("url", 500, "Server Error", None, None),
        HTTPError("url", 500, "Server Error", None, None),
    ]
    monkeypatch.setattr("kanboard_mcp.client.time.sleep", lambda _: None)

    with pytest.raises(KanboardClientError, match="Unexpected error"):
        client.call_api(method_name="get_task", task_id=42)


def test_execute_with_retry_retries_kanboard_client_error_then_exhausts(monkeypatch):
    client = make_client(max_retries=1)
    client._client.failures = [
        kanboard.ClientError("temporary"),
        kanboard.ClientError("temporary"),
    ]
    monkeypatch.setattr("kanboard_mcp.client.time.sleep", lambda _: None)

    with pytest.raises(KanboardAPIError, match="failed after 2 attempts"):
        client.call_api(method_name="get_task", task_id=42)


def test_execute_with_retry_raises_when_client_missing_after_connect(monkeypatch):
    client = KanboardClient(make_config())
    monkeypatch.setattr(client, "connect", lambda: setattr(client, "_connected", True))

    with pytest.raises(KanboardClientError, match="Unexpected error"):
        client.call_api(method_name="get_task", task_id=42)


def test_execute_with_retry_maps_kanboard_client_error_strings():
    client = make_client()
    client._client.failures = [kanboard.ClientError("HTTP Error 404: Not Found")]

    with pytest.raises(KanboardAPIError) as exc_info:
        client.call_api(method_name="get_task", task_id=42)

    assert exc_info.value.code == 404


def test_execute_with_retry_maps_kanboard_unauthorized_text():
    client = make_client()
    client._client.failures = [kanboard.ClientError("unauthorized")]

    with pytest.raises(KanboardAuthenticationError, match="Authentication failed"):
        client.call_api(method_name="get_task", task_id=42)


def test_call_api_wraps_unexpected_execute_exception(monkeypatch):
    client = make_client()
    monkeypatch.setattr(
        client,
        "_execute_with_retry",
        lambda *_, **__: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(KanboardClientError, match="Unexpected error: boom"):
        client.call_api(method_name="get_task")


def test_connection_helpers_return_success_and_failure(monkeypatch):
    client = make_client()

    assert client.test_connection()["connected"] is True
    assert client.get_server_info()["server_version"] == "1.2.3"

    monkeypatch.setattr(
        client,
        "call_api",
        lambda **_: (_ for _ in ()).throw(KanboardClientError("offline")),
    )

    assert client.test_connection()["connected"] is False
    assert client.get_server_info()["connected"] is False


def test_context_manager_connects_and_disconnects(monkeypatch):
    client = KanboardClient(make_config())
    fake_api = FakeKanboardApi()
    monkeypatch.setattr(client, "_create_client", lambda: fake_api)

    with client as active:
        assert active is client
        assert client.is_connected() is True

    assert client.is_connected() is False
