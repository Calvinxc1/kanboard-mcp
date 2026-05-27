import pytest


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


class ScriptedClient:
    def __init__(self, responses=None):
        self.calls = []
        self.responses = list(responses or [])

    def call_api(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        if args:
            raise AssertionError(f"call_api used positional args: {args}")
        if not self.responses:
            return None

        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


@pytest.fixture
def fake_mcp():
    return FakeMCP()
