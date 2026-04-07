# tests/graph/conftest.py
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(scope="session", autouse=True)
def _patch_llm_and_agent():
    with patch("agents.desarrollador_frontend.create_agent", return_value=MagicMock()), \
         patch("llm.provider.get_llm", return_value=MagicMock()):
        yield
