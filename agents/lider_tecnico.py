from agents.base import BaseAgent


class LiderTecnicoAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Líder técnico",
            goal="Definir estrategia de implementación y buenas prácticas"
        )