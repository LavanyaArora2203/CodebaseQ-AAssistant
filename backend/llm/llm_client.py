# backend/llm/llm_client.py

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Check your .env file.")
    return Groq(api_key=api_key)


def generate_answer(prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI code assistant for GitHub repositories."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def generate_answer_stream(prompt: str, model: str = "llama-3.3-70b-versatile"):
    """Streaming response for Streamlit UI."""
    client = get_client()
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI code assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        stream=True
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content