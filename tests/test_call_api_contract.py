import ast
from pathlib import Path


def test_tools_call_api_with_keyword_arguments_only():
    tools_dir = Path("src/kanboard_mcp/tools")
    offenders = []

    for path in sorted(tools_dir.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "call_api":
                continue
            if node.args:
                offenders.append(f"{path}:{node.lineno}")

    assert offenders == []
