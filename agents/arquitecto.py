from agents.base import BaseAgent


class ArquitectoAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Arquitecto de software",
            goal="Definir arquitectura técnica clara y escalable"
        )