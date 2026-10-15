
import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"


def ask_ai(question: str) -> str:
    """Ask the local Ollama model a question."""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a data analytics assistant. "
                    "Explain results clearly and simply. "
                    "Never invent dataset values or claim calculations "
                    "were performed unless verified results are provided."
                ),
            },
            {"role": "user", "content": question},
        ],
        "stream": False,
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    return response.json()["message"]["content"]
