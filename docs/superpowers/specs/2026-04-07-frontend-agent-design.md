# Frontend Agent Design — 2026-04-07

## Context

Hackathon Ciadet Artify. The project is a multi-agent software development pipeline that replicates a real dev team using AI. The current pipeline is a sequential chain of 5 agents (Analista → Arquitecto → LiderTecnico → Desarrollador → QA) implemented as plain Python classes over LangChain.

This spec covers the integration of Google Stitch MCP as the UI designer for a new FrontEnd agent, and the migration of the orchestration layer to a proper LangGraph `StateGraph`.

---

## Scope

- Migrate `graph/workflow.py` to LangGraph `StateGraph`
- Extract `StitchMCPClient` from the demo notebook into a reusable module
- Create `DesarrolladorFrontEndAgent` as a LangChain `AgentExecutor` (ReAct) with Stitch tools
- Save Stitch HTML output locally and generate a React project structure
- Do NOT create Backend or Database sub-agents (future work)
- Do NOT implement the Dev↔QA feedback loop (future work)
- Do NOT change the LLM provider (Vertex AI migration is handled separately)

---

## File Structure

```
tools/
  stitch_client.py        # StitchMCPClient: async HTTP JSON-RPC client for stitch.googleapis.com/mcp
  stitch_tools.py         # LangChain @tool wrappers that call StitchMCPClient
agents/
  base.py                 # Unchanged
  analista.py             # Unchanged
  arquitecto.py           # Unchanged
  lider_tecnico.py        # Unchanged
  desarrollador_frontend.py   # NEW: AgentExecutor with Stitch tools
  desarrollador.py        # Unchanged (kept as fallback)
  qa.py                   # Unchanged
graph/
  state.py                # NEW: PipelineState TypedDict
  workflow.py             # MIGRATED: LangGraph StateGraph replacing plain Workflow class
output/
  stitch/                 # Runtime: HTML files saved from Stitch responses
  react/                  # Runtime: Generated React project structure
config/
  settings.py             # UPDATED: loads STITCH_API_KEY from .env
```

---

## State

```python
class PipelineState(TypedDict):
    idea: str            # User input
    requerimientos: str  # Analista output
    arquitectura: str    # Arquitecto output
    plan_tecnico: str    # LiderTecnico output
    frontend_output: str # FrontEnd agent output (paths to generated React files)
    qa_result: str       # QA output
```

Each node receives the full state and writes only its own field. Downstream nodes read only what they need.

---

## StitchMCPClient (`tools/stitch_client.py`)

Extracted directly from `mcpServerStich.ipynb`. No Colab dependencies (`google.colab.userdata` replaced with `os.getenv("STITCH_API_KEY")`).

- `_request(method, params)` — sends JSON-RPC 2.0 POST to `https://stitch.googleapis.com/mcp`
- `call_tool(name, arguments)` — wraps `_request` for `tools/call`
- Timeout: 120s (as in the original demo)

---

## LangChain Tools (`tools/stitch_tools.py`)

Three `@tool`-decorated async functions that wrap `StitchMCPClient`:

| Tool | Input | Output |
|------|-------|--------|
| `create_stitch_project` | `title: str` | `project_id: str` |
| `generate_screen` | `project_id: str`, `prompt: str`, `device_type: str` | Raw HTML string |
| `save_and_convert_to_react` | `html: str`, `screen_name: str` | Paths to saved files |

`save_and_convert_to_react` saves the raw HTML to `output/stitch/<screen_name>.html` and uses `get_llm()` (from `llm/provider.py`) to convert it into a React functional component saved as `output/react/src/components/<screen_name>/<screen_name>.jsx`. The LLM prompt instructs it to use React hooks and Tailwind CSS classes, preserving the visual structure from the HTML.

---

## FrontEnd Agent (`agents/desarrollador_frontend.py`)

- Type: LangChain `AgentExecutor` with ReAct pattern
- Input: `plan_tecnico` field from `PipelineState`
- Tools: `create_stitch_project`, `generate_screen`, `save_and_convert_to_react`
- The agent LLM decides the sequence of tool calls and can retry if Stitch returns an error
- Output: a summary string written to `frontend_output` in state (includes paths to React files)

The system prompt instructs the agent to act as a Senior Frontend Developer: read the technical plan, design the screens needed, generate each via Stitch, save and convert to React components.

---

## LangGraph Workflow (`graph/workflow.py`)

```
START
  → analista_node       (reads: idea         → writes: requerimientos)
  → arquitecto_node     (reads: requerimientos → writes: arquitectura)
  → lider_node          (reads: arquitectura  → writes: plan_tecnico)
  → frontend_node       (reads: plan_tecnico  → writes: frontend_output)
  → qa_node             (reads: frontend_output → writes: qa_result)
END
```

All nodes except `frontend_node` are simple LangChain `chain.invoke()` wrappers (same logic as before). `frontend_node` calls `DesarrolladorFrontEndAgent.run()`.

The graph is compiled with `workflow.compile()`. A `conditional_edge` after `qa_node` is left as a stub (always continues to END) to make the future Dev↔QA loop a non-breaking addition.

---

## Configuration (`config/settings.py`)

```python
from dotenv import load_dotenv
import os

load_dotenv()
STITCH_API_KEY = os.getenv("STITCH_API_KEY")
```

Required `.env` keys: `ANTHROPIC_API_KEY` (existing), `STITCH_API_KEY` (new).

---

## Error Handling

- If Stitch returns a non-200 or empty response, `StitchMCPClient._request` returns `{}` and logs the error (same behavior as the demo). The FrontEnd AgentExecutor will surface the error to the LLM so it can retry or skip.
- If `STITCH_API_KEY` is missing, `StitchMCPClient.__init__` raises `ValueError` immediately.

---

## Out of Scope

- Backend and Database sub-agents
- Dev↔QA feedback loop
- LLM provider migration (Vertex AI)
- Authentication flow for Stitch beyond API key
