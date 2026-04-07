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
pytest                                          # all tests
pytest tests/tools/test_stitch_client.py        # Stitch HTTP client
pytest tests/tools/test_stitch_tools.py         # LangChain tool wrappers
pytest tests/graph/test_workflow.py             # LangGraph nodes
pytest tests/agents/test_desarrollador_frontend.py  # FrontEnd agent
pytest -v -k "test_name"                        # single test
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
- `graph/workflow.py` — `StateGraph` definition. Node functions (`analista_node`, etc.) are module-level for testability. Module-level agent instances (`_analista`, etc.) are created once and reused. `app` is the compiled graph.
- `agents/base.py` — `BaseAgent`: wraps `PromptTemplate | ChatAnthropic` chain. All simple agents extend this.
- `agents/desarrollador_frontend.py` — `DesarrolladorFrontEndAgent`: a LangChain 1.2.x agent (via `create_agent`, returns a `CompiledStateGraph`) with three Stitch tools. Compiled once in `__init__`, invoked with `recursion_limit=30`.
- `tools/stitch_client.py` — `StitchMCPClient`: async JSON-RPC HTTP client for `https://stitch.googleapis.com/mcp`. Reads `STITCH_API_KEY` from env. Extracted from `mcpServerStich.ipynb`.
- `tools/stitch_tools.py` — Three `@tool`-decorated functions: `create_stitch_project`, `generate_screen`, `save_and_convert_to_react`. The last saves HTML to `output/stitch/` and uses the LLM to generate React `.jsx` files in `output/react/src/components/`. Uses `nest_asyncio` for async compatibility.
- `llm/provider.py` — `get_llm()`: returns `ChatAnthropic` (will be replaced with Vertex AI — do not modify).
- `config/settings.py` — loads env vars including `STITCH_API_KEY`.

## FrontEnd Agent Flow

The `DesarrolladorFrontEndAgent` uses a tool-calling loop (LangChain 1.2.x `create_agent`) to:
1. Call `create_stitch_project` → gets `project_id`
2. Call `generate_screen` for each needed screen → gets HTML/design content
3. Call `save_and_convert_to_react` → saves `output/stitch/<name>.html` + generates `output/react/src/components/<name>/<name>.jsx`

## Adding a New Agent

1. Create `agents/my_agent.py` extending `BaseAgent` (or build a custom agent with `create_agent`).
2. Add a node function in `graph/workflow.py` and wire it with `graph.add_node` + `graph.add_edge`.
3. Add the new field to `PipelineState` in `graph/state.py`.

## Future Work (Out of Scope for This Iteration)

- Dev↔QA feedback loop (conditional edge after `qa_node`)
- Backend and Database sub-agents
- LLM provider migration to Vertex AI (handled by teammate)
