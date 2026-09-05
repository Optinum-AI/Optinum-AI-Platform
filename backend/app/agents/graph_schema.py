PLATFORMS = ["linkedin", "facebook", "youtube", "instagram", "tiktok", "x", "discord"]

NODE_TYPES = {
    "goal": {
        "objective": {"kind": "enum", "options": ["awareness", "lead_gen", "sales", "retention"], "default": "awareness"},
        "horizon_weeks": {"kind": "int", "min": 1, "max": 12, "default": 4},
    },
    "audience": {
        "segment": {"kind": "enum", "options": ["founders", "marketers", "developers", "smb_owners", "enterprise_it"], "default": "marketers"},
        "temperature_of_audience": {"kind": "enum", "options": ["cold", "warm", "hot"], "default": "cold"},
    },
    "content": {
        "format": {"kind": "enum", "options": ["text_post", "thread", "short_video", "long_video", "carousel", "article"], "default": "text_post"},
        "tone": {"kind": "enum", "options": ["bold", "professional", "playful", "educational"], "default": "bold"},
        "cta": {"kind": "enum", "options": ["signup", "demo", "download", "comment"], "default": "signup"},
    },
    "channel": {
        "platform": {"kind": "enum", "options": PLATFORMS, "default": "linkedin"},
        "priority": {"kind": "int", "min": 1, "max": 10, "default": 5},
    },
    "cadence": {
        "posts_per_week": {"kind": "int", "min": 1, "max": 14, "default": 3},
        "time_of_day": {"kind": "enum", "options": ["morning", "noon", "evening"], "default": "morning"},
        "duration_weeks": {"kind": "int", "min": 1, "max": 8, "default": 4},
    },
    "experiment": {
        "variant": {"kind": "enum", "options": ["hook", "visual", "cta"], "default": "hook"},
        "traffic_pct": {"kind": "int", "min": 5, "max": 30, "default": 10},
    },
}

NODE_LABELS = {
    "goal": "Goal",
    "audience": "Audience",
    "content": "Content",
    "channel": "Channel",
    "cadence": "Cadence",
    "experiment": "Experiment",
}


def default_params(node_type: str) -> dict:
    return {k: v["default"] for k, v in NODE_TYPES.get(node_type, {}).items()}


def validate_graph(graph: dict) -> list[str]:
    errors = []
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    ids = set()
    for node in nodes:
        nid, ntype = node.get("id"), node.get("type")
        if not nid:
            errors.append("node missing id")
            continue
        if nid in ids:
            errors.append(f"duplicate node id {nid}")
        ids.add(nid)
        if ntype not in NODE_TYPES:
            errors.append(f"node {nid}: unknown type {ntype}")
            continue
        params = node.get("params", {})
        for key, spec in NODE_TYPES[ntype].items():
            value = params.get(key, spec["default"])
            if spec["kind"] == "enum" and value not in spec["options"]:
                errors.append(f"node {nid}: param {key}={value!r} not in {spec['options']}")
            if spec["kind"] == "int":
                if not isinstance(value, int) or not (spec["min"] <= value <= spec["max"]):
                    errors.append(f"node {nid}: param {key} must be int {spec['min']}..{spec['max']}")
    for edge in edges:
        if edge.get("source") not in ids:
            errors.append(f"edge {edge.get('id')}: unknown source {edge.get('source')}")
        if edge.get("target") not in ids:
            errors.append(f"edge {edge.get('id')}: unknown target {edge.get('target')}")
    if not errors and _has_cycle(nodes, edges):
        errors.append("graph contains a cycle")
    return errors


def _has_cycle(nodes: list, edges: list) -> bool:
    try:
        topo_sort(nodes, edges)
        return False
    except ValueError:
        return True


def topo_sort(nodes: list, edges: list) -> list[str]:
    ids = [n["id"] for n in nodes]
    indeg = {i: 0 for i in ids}
    adj = {i: [] for i in ids}
    for e in edges:
        adj[e["source"]].append(e["target"])
        indeg[e["target"]] += 1
    pos = {n["id"]: n.get("position", {}).get("x", 0) for n in nodes}
    ready = sorted([i for i in ids if indeg[i] == 0], key=lambda i: pos[i])
    order = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for nxt in adj[current]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)
        ready.sort(key=lambda i: pos[i])
    if len(order) != len(ids):
        raise ValueError("cycle detected")
    return order


def context_for(node_id: str, nodes: list, edges: list) -> dict:
    """Merge params of all ancestors (by type) plus own params."""
    parents = {e["target"]: e["source"] for e in edges}
    by_id = {n["id"]: n for n in nodes}
    ctx = {}
    stack, seen = [node_id], set()
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        node = by_id.get(current)
        if node:
            ctx.setdefault(node["type"], node.get("params", {}))
        if current in parents:
            stack.append(parents[current])
    own = by_id.get(node_id, {})
    ctx[own.get("type", "node")] = own.get("params", {})
    return ctx
