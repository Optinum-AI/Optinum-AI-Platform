import json

from ..llm import chat_with_fallback
from ..llm.heuristic import HeuristicProvider
from . import graph_schema as gs
from . import personas


def parse_json_loose(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                continue
    return None


def _merged_params(ctx: dict) -> dict:
    merged = {}
    for key in ("goal", "audience", "content", "cadence", "channel", "experiment"):
        merged.update(ctx.get(key, {}))
    return merged


async def generate_graph(product: dict, connected: list[str]) -> tuple[dict, str]:
    persona = personas.load_persona("strategist")
    ctx = {"task": "graph", "product": product, "connected_platforms": connected}
    system, user = personas.build_prompt(persona, ctx)
    text, provider = await chat_with_fallback(system, user, json_mode=True, temperature=0.6, max_tokens=1024)
    data = parse_json_loose(text or "")
    if isinstance(data, dict) and isinstance(data.get("nodes"), list) and not gs.validate_graph(data):
        return data, provider
    return HeuristicProvider().graph(ctx), "heuristic"


async def generate_posts(node: dict, ctx: dict, product: dict, n: int) -> tuple[list[str], str]:
    persona = personas.load_persona("copywriter")
    params = _merged_params(ctx)
    c = {"task": "posts", "node_id": node["id"], "product": product, "n": n, "params": params}
    system, user = personas.build_prompt(persona, c)
    text, provider = await chat_with_fallback(system, user, json_mode=True, temperature=0.8, max_tokens=700)
    data = parse_json_loose(text or "")
    posts = data.get("posts") if isinstance(data, dict) else data
    if isinstance(posts, list) and posts and all(isinstance(p, str) for p in posts):
        return posts[:n], provider
    return HeuristicProvider().posts(c, __import__("random").Random()), "heuristic"


async def generate_creative(node: dict, ctx: dict, product: dict, n: int) -> tuple[list[str], str]:
    persona = personas.load_persona("creative")
    params = _merged_params(ctx)
    c = {"task": "creative", "node_id": node["id"], "product": product, "n": n, "params": params}
    system, user = personas.build_prompt(persona, c)
    text, provider = await chat_with_fallback(system, user, json_mode=True, temperature=0.8, max_tokens=700)
    data = parse_json_loose(text or "")
    notes = data.get("notes") if isinstance(data, dict) else data
    if isinstance(notes, list) and notes and all(isinstance(p, str) for p in notes):
        return notes[:n], provider
    return HeuristicProvider().creative(c, __import__("random").Random()), "heuristic"


async def generate_schedule(node: dict, ctx: dict, n: int) -> tuple[list[str], str]:
    persona = personas.load_persona("scheduler")
    params = _merged_params(ctx)
    c = {"task": "schedule", "node_id": node["id"], "n": n, "params": params}
    system, user = personas.build_prompt(persona, c)
    text, provider = await chat_with_fallback(system, user, json_mode=True, temperature=0.3, max_tokens=250)
    data = parse_json_loose(text or "")
    slots = data.get("slots") if isinstance(data, dict) else data
    if isinstance(slots, list) and slots and all(isinstance(p, str) for p in slots):
        return slots[:n], provider
    return HeuristicProvider().schedule(c), "heuristic"


async def generate_notes(product: dict, graph: dict) -> tuple[list[str], str]:
    persona = personas.load_persona("strategist")
    c = {"task": "notes", "product": product, "node_counts": _node_counts(graph)}
    system, user = personas.build_prompt(persona, c)
    text, provider = await chat_with_fallback(system, user, json_mode=True, temperature=0.7, max_tokens=350)
    data = parse_json_loose(text or "")
    notes = data.get("notes") if isinstance(data, dict) else data
    if isinstance(notes, list) and notes and all(isinstance(p, str) for p in notes):
        return notes[:6], provider
    return HeuristicProvider().notes(c), "heuristic"


async def analyze(summary: dict) -> tuple[dict, str]:
    persona = personas.load_persona("analyst")
    c = {"task": "analysis", "summary": summary}
    system, user = personas.build_prompt(persona, c)
    text, provider = await chat_with_fallback(system, user, json_mode=True, temperature=0.5, max_tokens=450)
    data = parse_json_loose(text or "")
    if isinstance(data, dict) and isinstance(data.get("narrative"), str):
        return data, provider
    import random
    return HeuristicProvider().analysis(c, random.Random()), "heuristic"


async def compare_competitor(product: dict, competitor: dict) -> tuple[dict, str]:
    persona = personas.load_persona("analyst")
    c = {"task": "competitor", "product": product, "competitor": competitor}
    system, user = personas.build_prompt(persona, c)
    text, provider = await chat_with_fallback(system, user, json_mode=True, temperature=0.5, max_tokens=450)
    data = parse_json_loose(text or "")
    if isinstance(data, dict) and isinstance(data.get("narrative"), str):
        return data, provider
    import random
    return HeuristicProvider().competitor(c, random.Random()), "heuristic"


async def recommend(platform_stats: list[dict]) -> tuple[dict, str]:
    persona = personas.load_persona("analyst")
    c = {"task": "recommend", "platforms": platform_stats}
    system, user = personas.build_prompt(persona, c)
    text, provider = await chat_with_fallback(system, user, json_mode=True, temperature=0.4, max_tokens=450)
    data = parse_json_loose(text or "")
    if isinstance(data, dict) and isinstance(data.get("ranking"), list) and data["ranking"]:
        return data, provider
    return HeuristicProvider().recommend(c), "heuristic"


def _node_counts(graph: dict) -> dict:
    counts: dict[str, int] = {}
    for node in graph.get("nodes", []):
        counts[node.get("type", "?")] = counts.get(node.get("type", "?"), 0) + 1
    return counts
