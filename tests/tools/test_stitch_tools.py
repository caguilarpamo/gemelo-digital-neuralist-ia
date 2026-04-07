import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


def _make_project_response(project_id: str) -> dict:
    return {
        "result": {
            "content": [{"text": json.dumps({"name": f"projects/{project_id}"})}]
        }
    }


def _make_screen_response(design_md: str) -> dict:
    content = {
        "outputComponents": [
            {
                "designSystem": {
                    "designSystem": {"designMd": design_md}
                }
            }
        ]
    }
    return {"result": {"content": [{"text": json.dumps(content)}]}}


def test_create_stitch_project_returns_clean_id():
    from tools.stitch_tools import create_stitch_project

    mock_client = MagicMock()
    mock_client.call_tool = AsyncMock(return_value=_make_project_response("99999"))

    with patch("tools.stitch_tools._get_client", return_value=mock_client):
        result = create_stitch_project.run("My App")
        assert result == "99999"


def test_generate_screen_returns_design_md():
    from tools.stitch_tools import generate_screen

    mock_client = MagicMock()
    mock_client.call_tool = AsyncMock(
        return_value=_make_screen_response("<div>hello</div>")
    )

    with patch("tools.stitch_tools._get_client", return_value=mock_client):
        result = generate_screen.run(
            {"project_id": "99999", "prompt": "A login screen", "device_type": "DESKTOP"}
        )
        assert "<div>hello</div>" in result


def test_save_and_convert_to_react_writes_files(tmp_path, monkeypatch):
    from tools.stitch_tools import save_and_convert_to_react

    monkeypatch.chdir(tmp_path)

    mock_llm_response = MagicMock()
    mock_llm_response.content = "export default function Login() { return <div>Login</div>; }"

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_llm_response

    mock_prompt_instance = MagicMock()
    mock_prompt_instance.__or__ = MagicMock(return_value=mock_chain)

    with patch("tools.stitch_tools.get_llm") as mock_get_llm, \
         patch("tools.stitch_tools.PromptTemplate") as mock_prompt_cls:
        mock_prompt_cls.from_template.return_value = mock_prompt_instance
        mock_get_llm.return_value = MagicMock()

        result = save_and_convert_to_react.run(
            {"html_content": "<div>Login</div>", "screen_name": "Login"}
        )

    html_file = tmp_path / "output" / "stitch" / "Login.html"
    jsx_file = tmp_path / "output" / "react" / "src" / "components" / "Login" / "Login.jsx"
    assert html_file.exists()
    assert jsx_file.exists()
    assert "Login.html" in result
    assert "Login.jsx" in result
