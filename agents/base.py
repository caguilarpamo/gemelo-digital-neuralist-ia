from langchain_core.prompts import PromptTemplate
from llm.provider import get_llm


class BaseAgent:
    def __init__(self, role, goal):
        self.role = role
        self.goal = goal
        self.llm = get_llm()

    def run(self, input_text):
        prompt = PromptTemplate.from_template(
            """
            Eres un {role}.
            Tu objetivo es: {goal}

            Entrada:
            {input}

            Responde de forma clara y estructurada.
            """
        )

        chain = prompt | self.llm

        return chain.invoke({
            "role": self.role,
            "goal": self.goal,
            "input": input_text
        })