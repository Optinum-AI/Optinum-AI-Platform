import logging
import os

from .base import LLMProvider
from .gemini import GeminiProvider
from .heuristic import HeuristicProvider
from .ollama import OllamaProvider

log = logging.getLogger("optimum.llm")

_provider: LLMProvider | None = None


async def probe_provider() -> LLMProvider:
    global _provider
    # 1. Check Gemini API
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key.strip():
        _provider = GeminiProvider(api_key=gemini_key)
        log.info("LLM provider selected: %s (Google Gemini API)", _provider.name)
        return _provider

    # 2. Check Ollama
    ollama = OllamaProvider()
    if await ollama.health():
        _provider = ollama
        log.info("LLM provider selected: %s", _provider.name)
        return _provider

    # 3. Fallback to Heuristic
    _provider = HeuristicProvider()
    log.warning(
        "LLM provider selected: heuristic fallback; Ollama is unavailable or model %s is missing",
        ollama.model,
    )
    return _provider


def get_provider() -> LLMProvider:
    return _provider or HeuristicProvider()


async def chat_with_fallback(
    system: str,
    user: str,
    json_mode: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> tuple[str, str]:
    # Check Gemini first if key exists
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key.strip():
        try:
            p = GeminiProvider(api_key=gemini_key)
            return await p.chat(system, user, json_mode, temperature, max_tokens), "gemini"
        except Exception as exc:
            log.warning("Gemini API call failed (%s); falling back", exc)

    provider = get_provider()
    # Probe again when startup happened before Ollama was ready.
    if provider.name != "ollama":
        candidate = OllamaProvider()
        if await candidate.health():
            provider = candidate
            log.info("LLM provider selected: ollama (recovered after startup)")
    if provider.name == "ollama":
        try:
            return await provider.chat(system, user, json_mode, temperature, max_tokens), "ollama"
        except Exception as exc:
            message = str(exc)
            retryable = any(
                marker in message.lower()
                for marker in ("connection failed", "timeout", "temporarily", "http 5")
            )
            log.warning(
                "Ollama LLM generation failed: %s; retryable=%s; action=verify service, host, and model",
                exc,
                retryable,
            )
    return await HeuristicProvider().chat(system, user, json_mode, temperature, max_tokens), "heuristic"
