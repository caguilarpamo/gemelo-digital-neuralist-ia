# tests/agents/test_desarrollador_frontend.py
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage


def test_run_returns_last_ai_message_content():
    """run() should return the content of the last AIMessage."""
    mock_ai_msg = AIMessage(content="Built Login.jsx at output/react/src/components/Login/Login.jsx")
    mock_result = {"messages": [HumanMessage(content="plan"), mock_ai_msg]}

    mock_agent = MagicMock()
    mock_agent.invoke.return_value = mock_result

    with patch("langchain.agents.create_agent", return_value=mock_agent), \
         patch("llm.provider.get_llm", return_value=MagicMock()):
        from importlib import reload
        import agents.desarrollador_frontend as m
        reload(m)
        agent = m.DesarrolladorFrontEndAgent()
        result = agent.run("Build a login screen")

    assert "Login.jsx" in result


def test_run_returns_fallback_when_no_ai_message():
    """run() should return fallback string when no AIMessage in result."""
    mock_result = {"messages": [HumanMessage(content="plan")]}

    mock_agent = MagicMock()
    mock_agent.invoke.return_value = mock_result

    with patch("langchain.agents.create_agent", return_value=mock_agent), \
         patch("llm.provider.get_llm", return_value=MagicMock()):
        from importlib import reload
        import agents.desarrollador_frontend as m
        reload(m)
        agent = m.DesarrolladorFrontEndAgent()
        result = agent.run("Build a login screen")

    assert result == "Frontend generation completed."
