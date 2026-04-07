from langchain_anthropic import ChatAnthropic
import os


def get_llm():
    return ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0.3,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )