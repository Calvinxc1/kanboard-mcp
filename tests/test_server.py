import pytest

from kanboard_mcp.config import Config, KanboardConfig, MCPServerConfig
from kanboard_mcp.server import KanboardMCPServer, create_server


class FakeFastMCP:
    instances = []

    def __init__(self, name):
        self.name = name
        self.tools = {}
        self.run_called = False
        FakeFastMCP.instances.append(self)

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator

    def run(self):
        self.run_called = True


class FakeServerClient:
    def __init__(self):
        self.connection_result = {"connected": True}
        self.server_info = {"server_version": "1.2.3"}

    def call_api(self, **kwargs):
        return {"method": kwargs["method_name"]}

    def test_connection(self):
        return self.connection_result

    def get_server_info(self):
        return self.server_info


def make_config(debug=False):
    return Config(
        kanboard=KanboardConfig(
            url="https://kanboard.example.test/jsonrpc.php",
            username="jsonrpc",
            password="token",
        ),
        server=MCPServerConfig(server_name="Test Kanboard", debug=debug),
    )


def test_server_registers_tools_and_connection_helpers(monkeypatch):
    fake_client = FakeServerClient()
    monkeypatch.setattr("kanboard_mcp.server.FastMCP", FakeFastMCP)
    monkeypatch.setattr("kanboard_mcp.server.create_client", lambda _: fake_client)

    server = KanboardMCPServer(make_config())

    assert server.mcp.name == "Test Kanboard"
    assert "getTask" in server.mcp.tools
    assert "setTaskTags" in server.mcp.tools
    assert server.mcp.tools["test_connection"]() == {
        "success": True,
        "data": {"connected": True},
    }
    assert server.mcp.tools["get_server_info"]() == {
        "success": True,
        "data": {"server_version": "1.2.3"},
    }
    config_info = server.mcp.tools["get_config_info"]()
    assert config_info["data"]["kanboard_url"] == "https://kanboard.example.test/jsonrpc.php"
    assert "password" not in config_info["data"]


def test_connection_helpers_return_error_payloads(monkeypatch):
    fake_client = FakeServerClient()
    fake_client.test_connection = lambda: (_ for _ in ()).throw(RuntimeError("down"))
    fake_client.get_server_info = lambda: (_ for _ in ()).throw(RuntimeError("nope"))
    monkeypatch.setattr("kanboard_mcp.server.FastMCP", FakeFastMCP)
    monkeypatch.setattr("kanboard_mcp.server.create_client", lambda _: fake_client)

    server = KanboardMCPServer(make_config())

    assert server.mcp.tools["test_connection"]() == {"success": False, "error": "down"}
    assert server.mcp.tools["get_server_info"]() == {"success": False, "error": "nope"}


def test_server_run_starts_mcp_when_connection_succeeds(monkeypatch):
    fake_client = FakeServerClient()
    monkeypatch.setattr("kanboard_mcp.server.FastMCP", FakeFastMCP)
    monkeypatch.setattr("kanboard_mcp.server.create_client", lambda _: fake_client)
    server = KanboardMCPServer(make_config())

    server.run()

    assert server.mcp.run_called is True


def test_server_run_swallows_keyboard_interrupt(monkeypatch):
    fake_client = FakeServerClient()
    monkeypatch.setattr("kanboard_mcp.server.FastMCP", FakeFastMCP)
    monkeypatch.setattr("kanboard_mcp.server.create_client", lambda _: fake_client)
    server = KanboardMCPServer(make_config())
    server.mcp.run = lambda: (_ for _ in ()).throw(KeyboardInterrupt())

    server.run()


def test_server_run_raises_when_connection_fails(monkeypatch):
    fake_client = FakeServerClient()
    fake_client.connection_result = {"connected": False, "error": "offline"}
    monkeypatch.setattr("kanboard_mcp.server.FastMCP", FakeFastMCP)
    monkeypatch.setattr("kanboard_mcp.server.create_client", lambda _: fake_client)
    server = KanboardMCPServer(make_config())

    try:
        server.run()
    except ConnectionError as exc:
        assert str(exc) == "Cannot connect to Kanboard: offline"
    else:
        raise AssertionError("Expected ConnectionError")


def test_create_server_loads_config_when_omitted(monkeypatch):
    monkeypatch.setattr("kanboard_mcp.server.FastMCP", FakeFastMCP)
    monkeypatch.setattr("kanboard_mcp.server.create_client", lambda _: FakeServerClient())
    monkeypatch.setattr("kanboard_mcp.server.load_config", lambda: make_config())

    server = create_server()

    assert isinstance(server, KanboardMCPServer)


@pytest.mark.parametrize(
    ("exception", "expected_stderr"),
    [
        (ValueError("bad config"), "Configuration error: bad config"),
        (ConnectionError("offline"), "Connection error: offline"),
        (RuntimeError("boom"), "Unexpected error: boom"),
    ],
)
def test_main_exits_with_error_messages(monkeypatch, capsys, exception, expected_stderr):
    import kanboard_mcp.server as server_module

    monkeypatch.setattr(
        server_module,
        "load_config",
        lambda: (_ for _ in ()).throw(exception),
    )

    with pytest.raises(SystemExit) as exc_info:
        server_module.main()

    assert exc_info.value.code == 1
    assert expected_stderr in capsys.readouterr().err


def test_main_runs_created_server(monkeypatch):
    import kanboard_mcp.server as server_module

    class RunnableServer:
        def __init__(self):
            self.run_called = False

        def run(self):
            self.run_called = True

    runnable = RunnableServer()
    monkeypatch.setattr(server_module, "load_config", lambda: make_config())
    monkeypatch.setattr(server_module, "create_server", lambda config: runnable)

    server_module.main()

    assert runnable.run_called is True
