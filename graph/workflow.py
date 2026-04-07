from agents.analista import AnalistaAgent
from agents.arquitecto import ArquitectoAgent
from agents.lider_tecnico import LiderTecnicoAgent
from agents.desarrollador import DesarrolladorAgent
from agents.qa import QAAgent


class Workflow:

    def __init__(self):
        self.analista = AnalistaAgent()
        self.arquitecto = ArquitectoAgent()
        self.lider = LiderTecnicoAgent()
        self.dev = DesarrolladorAgent()
        self.qa = QAAgent()

    def run(self, idea):

        print("\n🧠 Analista...")
        r1 = self.analista.run(idea)

        print("\n🏗 Arquitecto...")
        r2 = self.arquitecto.run(r1)

        print("\n👨‍💻 Líder Técnico...")
        r3 = self.lider.run(r2)

        print("\n💻 Desarrollador...")
        r4 = self.dev.run(r3)

        print("\n🧪 QA...")
        r5 = self.qa.run(r4)

        return r5


app = Workflow()