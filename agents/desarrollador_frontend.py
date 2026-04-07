# agents/desarrollador_frontend.py
# NOTE: Written for langchain>=1.2 / langgraph>=1.1 where AgentExecutor and
# create_react_agent have been replaced by create_agent (returns a CompiledStateGraph).
# The public interface (DesarrolladorFrontEndAgent.run) is unchanged.
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage

from llm.provider import get_llm
from tools.stitch_tools import create_stitch_project, generate_screen, save_and_convert_to_react

_SYSTEM_PROMPT = """You are a Senior Frontend Developer in an AI-powered software team.
Your task is to build the frontend for a software project using Google Stitch for UI generation.

Follow these steps in order:
1. Call create_stitch_project once with a descriptive title derived from the technical plan.
2. Identify the screens needed from the technical plan (at minimum: one main screen).
3. Call generate_screen for each screen, using the architecture description as the prompt.
4. Call save_and_convert_to_react for each generated screen.
5. Summarise what was built and list the file paths of all generated React components."""


class DesarrolladorFrontEndAgent:
    def __init__(self):
        self.llm = get_llm()
        self.tools = [create_stitch_project, generate_screen, save_and_convert_to_react]
        self._agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=_SYSTEM_PROMPT,
            debug=True,
        )

    def run(self, plan_tecnico: str) -> str:
        inputs = {"messages": [HumanMessage(content=plan_tecnico)]}
        result = self._agent.invoke(inputs, config={"recursion_limit": 30})
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        return "Frontend generation completed."
