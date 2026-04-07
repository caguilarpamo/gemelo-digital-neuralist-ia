from agents.base import BaseAgent


class QAAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="QA",
            goal="Validar calidad, detectar errores y proponer mejoras"
        )