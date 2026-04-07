from unittest.mock import MagicMock, patch
from graph.state import PipelineState


def _make_state(**kwargs) -> PipelineState:
    base = {
        "idea": "",
        "requerimientos": "",
        "arquitectura": "",
        "plan_tecnico": "",
        "frontend_output": "",
        "qa_result": "",
    }
    base.update(kwargs)
    return base


def _mock_agent_run(text: str):
    response = MagicMock()
    response.content = text
    return response


def test_analista_node_writes_requerimientos():
    # Agents are module-level instances, so patch the instance method directly
    import graph.workflow as wf
    with patch.object(wf._analista, "run", return_value=_mock_agent_run("Reqs text")):
        state = _make_state(idea="Build a fintech app")
        result = wf.analista_node(state)
        assert "requerimientos" in result
        assert result["requerimientos"] == "Reqs text"


def test_frontend_node_writes_frontend_output():
    import graph.workflow as wf
    with patch.object(wf._frontend, "run", return_value="React files at output/react/src/components/App/App.jsx"):
        state = _make_state(plan_tecnico="Build login screen")
        result = wf.frontend_node(state)
        assert "frontend_output" in result
        assert "react" in result["frontend_output"]


def test_app_has_invoke_and_stream():
    from graph.workflow import app
    assert hasattr(app, "invoke")
    assert hasattr(app, "stream")
