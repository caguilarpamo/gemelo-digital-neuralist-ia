from graph.workflow import app

if __name__ == "__main__":
    idea = input("Describe tu idea: ")
    resultado = app.run(idea)

    print("\n✅ RESULTADO FINAL:\n")
    print(resultado)