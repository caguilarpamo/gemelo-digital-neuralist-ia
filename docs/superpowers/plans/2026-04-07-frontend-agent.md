# Frontend Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Google Stitch MCP as a UI generator for a new FrontEnd AgentExecutor and migrate the pipeline orchestration to a proper LangGraph StateGraph.

**Architecture:** Five existing agents (Analista, Arquitecto, LiderTecnico, Desarrollador, QA) are kept unchanged and become nodes in a LangGraph StateGraph. A new `DesarrolladorFrontEndAgent` is inserted after LiderTecnico as a LangChain ReAct AgentExecutor with three Stitch tools: create project, generate screen, and save/convert to React. State flows as a typed dict between nodes.

**Tech Stack:** Python 3.12, LangChain, LangGraph, `httpx` (Stitch HTTP client), `pytest`, `pytest-asyncio`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| CREATE | `graph/state.py` | `PipelineState` TypedDict |
| UPDATE | `config/settings.py` | Load `STITCH_API_KEY` from `.env` |
| CREATE | `tools/__init__.py` | Empty package marker |
| CREATE | `tools/stitch_client.py` | `StitchMCPClient` — async JSON-RPC HTTP client |
| CREATE | `tools/stitch_tools.py` | LangChain `@tool` wrappers for Stitch |
| CREATE | `agents/desarrollador_frontend.py` | `DesarrolladorFrontEndAgent` — ReAct AgentExecutor |
| REWRITE | `graph/workflow.py` | LangGraph `StateGraph` replacing plain `Workflow` class |
| UPDATE | `main.py` | Use LangGraph `app.invoke()` instead of `app.run()` |
| UPDATE | `requirements.txt` | Add `pytest-asyncio` |
| CREATE | `tests/__init__.py` | Empty |
| CREATE | `tests/tools/__init__.py` | Empty |
| CREATE | `tests/tools/test_stitch_client.py` | Unit tests for `StitchMCPClient` |
| CREATE | `tests/tools/test_stitch_tools.py` | Unit tests for Stitch tool functions |
| CREATE | `tests/graph/test_workflow.py` | Integration test for LangGraph nodes |
| UPDATE | `CLAUDE.md` | Hackathon context, Vertex AI note, new architecture |

---

## Task 1: PipelineState and config

**Files:**
- Create: `graph/state.py`
- Update: `config/settings.py`
- Update: `requirements.txt`

- [ ] **Step 1.1: Create `graph/state.py`**

```python
# graph/state.py
from typing import TypedDict


class PipelineState(TypedDict):
    idea: str
    requerimientos: str
    arquitectura: str
    plan_tecnico: str
    frontend_output: str
    qa_result: str
```

- [ ] **Step 1.2: Update `config/settings.py`**

```python
# config/settings.py
from dotenv import load_dotenv
import os

load_dotenv()

STITCH_API_KEY = os.getenv("STITCH_API_KEY")
```

- [ ] **Step 1.3: Add `pytest-asyncio` to `requirements.txt`**

Open `requirements.txt` and add this line:
```
pytest-asyncio>=0.23.0
```

- [ ] **Step 1.4: Commit**

```bash
git add graph/state.py config/settings.py requirements.txt
git commit -m "feat: add PipelineState TypedDict and STITCH_API_KEY config"
```

---

## Task 2: StitchMCPClient

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/stitch_client.py`
- Create: `tests/__init__.py`
- Create: `tests/tools/__init__.py`
- Create: `tests/tools/test_stitch_client.py`

- [ ] **Step 2.1: Write the failing tests**

```python
# tests/__init__.py
# (empty)
```

```python
# tests/tools/__init__.py
# (empty)
```

```python
# tests/tools/test_stitch_client.py
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


def test_init_raises_without_api_key():
    with patch.dict("os.environ", {}, clear=True):
        from importlib import reload
        import tools.stitch_client as m
        reload(m)
        with pytest.raises(ValueError, match="STITCH_API_KEY"):
            m.StitchMCPClient()


def test_init_reads_env_var():
    with patch.dict("os.environ", {"STITCH_API_KEY": "test-key"}):
        from importlib import reload
        import tools.stitch_client as m
        reload(m)
        client = m.StitchMCPClient()
        assert client.api_key == "test-key"


def test_init_accepts_explicit_key():
    client_module = _import_client()
    client = client_module.StitchMCPClient(api_key="explicit-key")
    assert client.api_key == "explicit-key"


@pytest.mark.asyncio
async def test_request_returns_empty_dict_on_http_error():
    client = _import_client().StitchMCPClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        result = await client._request("tools/list", {})
        assert result == {}


@pytest.mark.asyncio
async def test_request_returns_json_on_success():
    client = _import_client().StitchMCPClient(api_key="test-key")
    expected = {"result": {"tools": []}}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        result = await client._request("tools/list", {})
        assert result == expected


@pytest.mark.asyncio
async def test_request_returns_empty_on_exception():
    client = _import_client().StitchMCPClient(api_key="test-key")

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        result = await client._request("tools/list", {})
        assert result == {}


def _import_client():
    from importlib import reload
    import tools.stitch_client as m
    reload(m)
    return m
```

- [ ] **Step 2.2: Run tests to confirm they fail**

```bash
cd C:\Users\juand\Documents\Hackathon02
pytest tests/tools/test_stitch_client.py -v
```

Expected: `ERROR` — `tools/stitch_client.py` does not exist yet.

- [ ] **Step 2.3: Create `tools/__init__.py`**

```python
# tools/__init__.py
# (empty)
```

- [ ] **Step 2.4: Create `tools/stitch_client.py`**

```python
# tools/stitch_client.py
import httpx
import json
import os
import traceback


class StitchMCPClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("STITCH_API_KEY")
        if not self.api_key:
            raise ValueError("STITCH_API_KEY is required. Set it in .env or pass it explicitly.")
        self.url = "https://stitch.googleapis.com/mcp"
        self.headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }
        self.request_id = 1

    async def _request(self, method: str, params: dict) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params,
        }
        self.request_id += 1
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(self.url, headers=self.headers, json=payload)
                if response.status_code != 200:
                    print(f"[Stitch HTTP ERROR] {response.status_code}: {response.text}")
                    return {}
                return response.json()
            except Exception:
                traceback.print_exc()
                return {}

    async def call_tool(self, name: str, arguments: dict) -> dict:
        return await self._request("tools/call", {"name": name, "arguments": arguments})
```

- [ ] **Step 2.5: Run tests to confirm they pass**

```bash
pytest tests/tools/test_stitch_client.py -v
```

Expected: 6 tests PASSED.

- [ ] **Step 2.6: Commit**

```bash
git add tools/__init__.py tools/stitch_client.py tests/__init__.py tests/tools/__init__.py tests/tools/test_stitch_client.py
git commit -m "feat: add StitchMCPClient extracted from demo notebook"
```

---

## Task 3: Stitch LangChain Tools

**Files:**
- Create: `tools/stitch_tools.py`
- Create: `tests/tools/test_stitch_tools.py`

- [ ] **Step 3.1: Write the failing tests**

```python
# tests/tools/test_stitch_tools.py
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

    with patch("tools.stitch_tools.get_llm") as mock_get_llm, \
         patch("tools.stitch_tools.PromptTemplate") as mock_prompt_cls:
        mock_prompt_cls.from_template.return_value.__or__ = MagicMock(return_value=mock_chain)
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
```

- [ ] **Step 3.2: Run tests to confirm they fail**

```bash
pytest tests/tools/test_stitch_tools.py -v
```

Expected: `ERROR` — `tools/stitch_tools.py` does not exist yet.

- [ ] **Step 3.3: Create `tools/stitch_tools.py`**

```python
# tools/stitch_tools.py
import asyncio
import json
from pathlib import Path

from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate

from llm.provider import get_llm
from tools.stitch_client import StitchMCPClient


def _get_client() -> StitchMCPClient:
    return StitchMCPClient()


@tool
def create_stitch_project(title: str) -> str:
    """Create a new Stitch UI project. Returns the numeric project_id string."""

    async def _run():
        client = _get_client()
        res = await client.call_tool("create_project", {"title": title})
        content_text = res.get("result", {}).get("content", [{}])[0].get("text", "{}")
        project_data = json.loads(content_text)
        full_name = project_data.get("name", "")
        return full_name.replace("projects/", "")

    return asyncio.run(_run())


@tool
def generate_screen(project_id: str, prompt: str, device_type: str = "DESKTOP") -> str:
    """Generate a UI screen via Stitch from a text prompt. Returns the design content (HTML/Markdown)."""

    async def _run():
        client = _get_client()
        res = await client.call_tool(
            "generate_screen_from_text",
            {
                "projectId": project_id,
                "prompt": prompt,
                "deviceType": device_type,
                "modelId": "GEMINI_3_1_PRO",
            },
        )
        try:
            generated = json.loads(
                res.get("result", {}).get("content", [{}])[0].get("text", "{}")
            )
            design_md = (
                generated.get("outputComponents", [{}])[0]
                .get("designSystem", {})
                .get("designSystem", {})
                .get("designMd", "")
            )
            return design_md or json.dumps(generated)
        except Exception as e:
            return f"Error extracting design content: {e}"

    return asyncio.run(_run())


@tool
def save_and_convert_to_react(html_content: str, screen_name: str) -> str:
    """Save HTML from Stitch locally and convert it to a React functional component using JSX + Tailwind CSS."""
    # Save raw HTML
    stitch_dir = Path("output/stitch")
    stitch_dir.mkdir(parents=True, exist_ok=True)
    html_path = stitch_dir / f"{screen_name}.html"
    html_path.write_text(html_content, encoding="utf-8")

    # Convert to React via LLM
    llm = get_llm()
    prompt = PromptTemplate.from_template(
        """You are a senior frontend developer. Convert the following HTML/design spec into a React functional component.

Rules:
- Use React hooks (useState, useEffect) only where needed
- Use Tailwind CSS classes for all styling (no inline styles)
- Export the component as default
- Component name: {component_name}
- Return ONLY the JSX/TSX code, no explanations or markdown fences

HTML/Design:
{html_content}
"""
    )
    chain = prompt | llm
    result = chain.invoke({"component_name": screen_name, "html_content": html_content})
    jsx_content = result.content if hasattr(result, "content") else str(result)

    # Save React component
    react_dir = Path(f"output/react/src/components/{screen_name}")
    react_dir.mkdir(parents=True, exist_ok=True)
    jsx_path = react_dir / f"{screen_name}.jsx"
    jsx_path.write_text(jsx_content, encoding="utf-8")

    return f"HTML saved to {html_path}\nReact component saved to {jsx_path}"
```

- [ ] **Step 3.4: Run tests to confirm they pass**

```bash
pytest tests/tools/test_stitch_tools.py -v
```

Expected: 3 tests PASSED.

- [ ] **Step 3.5: Commit**

```bash
git add tools/stitch_tools.py tests/tools/test_stitch_tools.py
git commit -m "feat: add Stitch LangChain tools (create_project, generate_screen, save_and_convert)"
```

---

## Task 4: FrontEnd AgentExecutor

**Files:**
- Create: `agents/desarrollador_frontend.py`

- [ ] **Step 4.1: Create `agents/desarrollador_frontend.py`**

```python
# agents/desarrollador_frontend.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from llm.provider import get_llm
from tools.stitch_tools import create_stitch_project, generate_screen, save_and_convert_to_react

_REACT_PROMPT = """You are a Senior Frontend Developer in an AI-powered software team.
Your task is to build the frontend for a software project using Google Stitch for UI generation.

You have access to the following tools:

{tools}

Use this format strictly:

Thought: think about what to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I have completed the frontend generation
Final Answer: summary of what was built, including file paths of generated React components

Instructions:
1. Call create_stitch_project once with a descriptive title based on the technical plan
2. Identify the screens needed from the technical plan (at minimum: one main screen)
3. Call generate_screen for each screen using the architecture as the prompt
4. Call save_and_convert_to_react for each generated screen
5. Report the paths of all generated files in your Final Answer

Technical Plan:
{input}

{agent_scratchpad}"""


class DesarrolladorFrontEndAgent:
    def __init__(self):
        self.llm = get_llm()
        self.tools = [create_stitch_project, generate_screen, save_and_convert_to_react]

    def run(self, plan_tecnico: str) -> str:
        prompt = PromptTemplate.from_template(_REACT_PROMPT)
        agent = create_react_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True,
        )
        result = executor.invoke({"input": plan_tecnico})
        return result.get("output", "Frontend generation completed.")
```

- [ ] **Step 4.2: Smoke-test import**

```bash
python -c "from agents.desarrollador_frontend import DesarrolladorFrontEndAgent; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4.3: Commit**

```bash
git add agents/desarrollador_frontend.py
git commit -m "feat: add DesarrolladorFrontEndAgent as ReAct AgentExecutor with Stitch tools"
```

---

## Task 5: Migrate Workflow to LangGraph StateGraph

**Files:**
- Rewrite: `graph/workflow.py`
- Create: `tests/graph/__init__.py`
- Create: `tests/graph/test_workflow.py`

- [ ] **Step 5.1: Write the failing tests**

```python
# tests/graph/__init__.py
# (empty)
```

```python
# tests/graph/test_workflow.py
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
```

- [ ] **Step 5.2: Run tests to confirm they fail**

```bash
pytest tests/graph/test_workflow.py -v
```

Expected: `ERROR` — `graph.workflow` has no `analista_node`, `frontend_node`, or compiled graph yet.

- [ ] **Step 5.3: Rewrite `graph/workflow.py`**

```python
# graph/workflow.py
from langgraph.graph import StateGraph, END

from graph.state import PipelineState
from agents.analista import AnalistaAgent
from agents.arquitecto import ArquitectoAgent
from agents.lider_tecnico import LiderTecnicoAgent
from agents.desarrollador_frontend import DesarrolladorFrontEndAgent
from agents.qa import QAAgent


def _text(result) -> str:
    """Extract string content from a LangChain message or plain string."""
    return result.content if hasattr(result, "content") else str(result)


# --- Node functions (module-level so tests can import them directly) ---

_analista = AnalistaAgent()
_arquitecto = ArquitectoAgent()
_lider = LiderTecnicoAgent()
_frontend = DesarrolladorFrontEndAgent()
_qa = QAAgent()


def analista_node(state: PipelineState) -> dict:
    return {"requerimientos": _text(_analista.run(state["idea"]))}


def arquitecto_node(state: PipelineState) -> dict:
    return {"arquitectura": _text(_arquitecto.run(state["requerimientos"]))}


def lider_node(state: PipelineState) -> dict:
    return {"plan_tecnico": _text(_lider.run(state["arquitectura"]))}


def frontend_node(state: PipelineState) -> dict:
    return {"frontend_output": _frontend.run(state["plan_tecnico"])}


def qa_node(state: PipelineState) -> dict:
    return {"qa_result": _text(_qa.run(state["frontend_output"]))}


# --- Graph definition ---

def _build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)
    graph.add_node("analista", analista_node)
    graph.add_node("arquitecto", arquitecto_node)
    graph.add_node("lider", lider_node)
    graph.add_node("frontend", frontend_node)
    graph.add_node("qa", qa_node)

    graph.set_entry_point("analista")
    graph.add_edge("analista", "arquitecto")
    graph.add_edge("arquitecto", "lider")
    graph.add_edge("lider", "frontend")
    graph.add_edge("frontend", "qa")
    # Stub conditional edge — replace with loop logic when Dev↔QA loop is implemented
    graph.add_edge("qa", END)

    return graph.compile()


app = _build_graph()
```

- [ ] **Step 5.4: Run tests to confirm they pass**

```bash
pytest tests/graph/test_workflow.py -v
```

Expected: 3 tests PASSED.

- [ ] **Step 5.5: Commit**

```bash
git add graph/workflow.py tests/graph/__init__.py tests/graph/test_workflow.py
git commit -m "feat: migrate workflow to LangGraph StateGraph with FrontEnd node"
```

---

## Task 6: Update main.py

**Files:**
- Update: `main.py`

- [ ] **Step 6.1: Update `main.py` to use LangGraph `invoke`**

Replace the full content of `main.py` with:

```python
# main.py
from graph.workflow import app


if __name__ == "__main__":
    idea = input("Describe tu idea: ")

    initial_state = {
        "idea": idea,
        "requerimientos": "",
        "arquitectura": "",
        "plan_tecnico": "",
        "frontend_output": "",
        "qa_result": "",
    }

    print("\n🚀 Iniciando pipeline...\n")
    result = app.invoke(initial_state)

    print("\n✅ RESULTADO FINAL:\n")
    print(result["qa_result"])
```

- [ ] **Step 6.2: Verify import is clean**

```bash
python -c "from graph.workflow import app; print('Graph compiled OK')"
```

Expected: `Graph compiled OK`

- [ ] **Step 6.3: Commit**

```bash
git add main.py
git commit -m "feat: update main.py to use LangGraph invoke API"
```

---

## Task 7: Update CLAUDE.md

**Files:**
- Update: `CLAUDE.md`

- [ ] **Step 7.1: Replace the content of `CLAUDE.md`**

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Hackathon Context

**Challenge:** Ciadet Artify — build an AI agent pipeline that replicates a real software development team.

**Elevator Pitch:** A digital twin of a dev team where autonomous agents with defined roles (analyst, architect, developer, QA, tech lead) collaborate via LangChain and LangGraph. From requirements to deployment, the system generates code, tests it, documents it, and delivers it production-ready. Not just automation — an AI-powered software factory.

**Current status:** Hackathon in progress. A teammate is migrating the LLM provider from Anthropic (`langchain_anthropic`) to Vertex AI (`langchain_google_vertexai`). Do NOT modify `llm/provider.py` until that migration is merged.

## Setup

Requires Python 3.12+ and the following keys in a `.env` file at the project root:

```
ANTHROPIC_API_KEY=...   # will be replaced by Vertex AI credentials
STITCH_API_KEY=...      # Google Stitch MCP API key
```

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Prompts for a text idea and runs the full agent pipeline.

## Testing

```bash
pytest                                    # all tests
pytest tests/tools/test_stitch_client.py  # Stitch HTTP client
pytest tests/tools/test_stitch_tools.py   # LangChain tool wrappers
pytest tests/graph/test_workflow.py       # LangGraph nodes
pytest -v -k "test_name"                  # single test
```

## Architecture

A LangGraph `StateGraph` pipeline. Each agent is a node that reads from a shared `PipelineState` TypedDict and writes one field back.

```
idea → analista → arquitecto → lider_tecnico → frontend → qa → END
```

**State (`graph/state.py`):**
```
PipelineState: { idea, requerimientos, arquitectura, plan_tecnico, frontend_output, qa_result }
```

**Key modules:**

- `graph/state.py` — `PipelineState` TypedDict shared across all nodes.
- `graph/workflow.py` — `StateGraph` definition. Node functions (`analista_node`, etc.) are module-level for testability. `app` is the compiled graph.
- `agents/base.py` — `BaseAgent`: wraps `PromptTemplate | ChatAnthropic` chain. All simple agents extend this.
- `agents/desarrollador_frontend.py` — `DesarrolladorFrontEndAgent`: a LangChain ReAct `AgentExecutor` with three Stitch tools. Uses `create_react_agent` with a custom ReAct prompt.
- `tools/stitch_client.py` — `StitchMCPClient`: async JSON-RPC HTTP client for `https://stitch.googleapis.com/mcp`. Reads `STITCH_API_KEY` from env. Extracted from `mcpServerStich.ipynb`.
- `tools/stitch_tools.py` — Three `@tool`-decorated functions: `create_stitch_project`, `generate_screen`, `save_and_convert_to_react`. The last one saves HTML to `output/stitch/` and uses the LLM to generate React `.jsx` files in `output/react/src/components/`.
- `llm/provider.py` — `get_llm()`: returns `ChatAnthropic` (will be replaced with Vertex AI).
- `config/settings.py` — loads env vars including `STITCH_API_KEY`.

## FrontEnd Agent Flow

The `DesarrolladorFrontEndAgent` uses ReAct to:
1. Call `create_stitch_project` → gets `project_id`
2. Call `generate_screen` for each needed screen → gets HTML/design content
3. Call `save_and_convert_to_react` → saves `output/stitch/<name>.html` + generates `output/react/src/components/<name>/<name>.jsx`

## Adding a New Agent

1. Create `agents/my_agent.py` extending `BaseAgent` (or build a custom `AgentExecutor`).
2. Add a node function in `graph/workflow.py` and wire it with `graph.add_node` + `graph.add_edge`.
3. Add the new field to `PipelineState` in `graph/state.py`.
```

- [ ] **Step 7.2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with hackathon context, LangGraph architecture, Stitch MCP"
```

---

## Task 8: Run full test suite

- [ ] **Step 8.1: Install updated dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 8.2: Run all tests**

```bash
pytest -v
```

Expected: All tests PASSED. If any test fails, check the error and fix it before proceeding.

- [ ] **Step 8.3: Final commit**

```bash
git add -A
git commit -m "chore: final test pass — frontend agent + LangGraph migration complete"
```
