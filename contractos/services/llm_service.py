import os
from typing import Optional


class AzureOpenAIService:
    def __init__(self) -> None:
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key and self.deployment)

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.is_configured():
            raise RuntimeError("Azure OpenAI is not configured. Check environment variables.")

        try:
            from openai import AzureOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed.") from exc

        client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""
