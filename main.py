# main.py
from graph.workflow import app


if __name__ == "__main__":
    idea = input("Describe tu idea: ")

    initial_state = {
        "idea": idea,
        "requerimientos": "",
        "arquitectura": "",
        "plan_tecnico": "",
        "frontend_output": "",
        "qa_result": "",
    }

    print("\n🚀 Iniciando pipeline...\n")
    result = app.invoke(initial_state)

    print("\n✅ RESULTADO FINAL:\n")
    print(result["qa_result"])
