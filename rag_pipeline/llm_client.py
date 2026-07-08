from abc import ABC, abstractmethod
import ollama


class LLMClient(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass


class OllamaClient(LLMClient):

    def __init__(
        self,
        model: str = "llama3.2:3b",
        temperature: float = 0.0,
        num_ctx: int = 8192,
    ):
        self.model = model
        self.temperature = temperature
        self.num_ctx = num_ctx

    def generate(self, prompt: str) -> str:

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
                {
            "role": "system",

            "content":
            "You are an expert software engineer. "
            "Answer only using the repository context."
        },
            ],
            options={
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            },
        )

        return response["message"]["content"]