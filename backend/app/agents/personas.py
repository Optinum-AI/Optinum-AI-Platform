import json
from functools import lru_cache
from pathlib import Path

PERSONAS_DIR = Path(__file__).parent / "personas"
NAMES = ["strategist", "copywriter", "creative", "scheduler", "analyst"]


@lru_cache
def load_persona(name: str) -> dict:
    return json.loads((PERSONAS_DIR / f"{name}.json").read_text())


def build_prompt(persona: dict, ctx: dict) -> tuple[str, str]:
    system = persona["system_prompt"]
    for ex in persona.get("few_shot", []):
        system += f"\n\nExample input:\n{ex['input']}\nExample output:\n{ex['output']}"
    return system, json.dumps(ctx)
