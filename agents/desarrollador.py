from agents.base import BaseAgent


class DesarrolladorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Desarrollador",
            goal="Construir código basado en la arquitectura"
        )