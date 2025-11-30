import asyncio
from typing import AsyncGenerator
from openai import AsyncOpenAI
from src.core.interfaces import LLMInterface
from src.core.config import settings

class OpenAILLM(LLMInterface):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt = (
            "You are Chronos, a helpful voice assistant. "
            "Keep answers concise (under 2 sentences) for voice output."
        )

    async def generate_response(self, query: str) -> AsyncGenerator[str, None]:
        if not query:
            return

        try:
            stream = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": query}
                ],
                stream=True
            )

            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            yield f"Error: {str(e)}"