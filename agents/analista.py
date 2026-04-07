from agents.base import BaseAgent


class AnalistaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Analista de negocio",
            goal="Entender y estructurar requerimientos del usuario"
        )