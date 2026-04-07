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


# --- Module-level agent instances (created once, reused across calls) ---

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
    return {"frontend_output": _text(_frontend.run(state["plan_tecnico"]))}


def qa_node(state: PipelineState) -> dict:
    return {"qa_result": _text(_qa.run(state["frontend_output"]))}


# --- Graph definition ---

def _build_graph():
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
    # Stub edge — replace with conditional_edge when Dev↔QA loop is implemented
    graph.add_edge("qa", END)

    return graph.compile()


app = _build_graph()
