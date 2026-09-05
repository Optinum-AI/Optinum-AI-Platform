import logging

import httpx

from .. import config
from .base import LLMProvider

log = logging.getLogger("optimum.llm.ollama")


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        host = config.OLLAMA_HOST.strip().rstrip("/")
        self.host = host if "://" in host else f"http://{host}"
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT_S

    async def _tags(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 10)) as client:
                response = await client.get(f"{self.host}/api/tags")
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"LLM connection failed: request timeout connecting to {self.host}"
            ) from exc
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"LLM connection failed: connection refused at {self.host}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"LLM service returned HTTP {exc.response.status_code} from /api/tags"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(f"LLM service returned an invalid /api/tags response") from exc
        models = payload.get("models", [])
        if not isinstance(models, list):
            raise RuntimeError("LLM service returned an invalid model list")
        return [model for model in models if isinstance(model, dict)]

    async def health(self) -> bool:
        try:
            models = await self._tags()
            available = {m.get("name") for m in models}
            if self.model not in available:
                log.warning("Model not found: %s (configured Ollama host: %s)", self.model, self.host)
                return False
            return True
        except RuntimeError as exc:
            log.warning("%s", exc)
            return False

    async def chat(
        self,
        system: str,
        user: str,
        json_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        payload = {
            "model": self.model,
            "system": system,
            "prompt": user,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.host}/api/generate", json=payload)
                response.raise_for_status()
                result = response.json()
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Request timeout generating with model {self.model} after {self.timeout:g}s"
            ) from exc
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"LLM connection failed: connection refused at {self.host}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"LLM service returned HTTP {exc.response.status_code} for /api/generate"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("Invalid response from Ollama /api/generate") from exc
        answer = result.get("response") if isinstance(result, dict) else None
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("Invalid response from Ollama: missing response text")
        return answer
