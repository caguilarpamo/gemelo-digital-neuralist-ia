from langchain_google_vertexai import ChatVertexAI

def get_llm():
    return ChatVertexAI(
        model="gemini-1.5-flash",
        temperature=0.3,
        #project="TU_PROJECT_ID",
        project="moodle-489002",
        location="us-central1"
    )