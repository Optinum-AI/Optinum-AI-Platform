from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def health(self) -> bool: ...

    @abstractmethod
    async def chat(
        self,
        system: str,
        user: str,
        json_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str: ...
