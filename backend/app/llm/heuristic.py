import hashlib
import json
import random
from datetime import datetime, timedelta, timezone

from .base import LLMProvider

SEGMENT_LABELS = {
    "founders": "startup founders",
    "marketers": "growth marketers",
    "developers": "developers",
    "smb_owners": "small business owners",
    "enterprise_it": "enterprise IT leaders",
}

HOOKS = {
    "bold": "Stop scrolling. This one pays for itself.",
    "professional": "A brief note on a measurable outcome:",
    "playful": "Okay, this one is genuinely fun.",
    "educational": "Here is what most teams get wrong:",
}

BENEFITS = [
    "cut manual busywork by hours every week",
    "turn scattered channels into one revenue engine",
    "lift qualified pipeline without adding headcount",
    "keep branding consistent across every platform",
    "compound reach while you sleep",
]

CTAS = {
    "signup": "Start free today.",
    "demo": "Book a 15-minute demo this week.",
    "download": "Grab the free toolkit below.",
    "comment": "What has your experience been? Tell us below.",
}

TAGS = {
    "linkedin": "#B2B #Growth",
    "facebook": "#SmallBusiness",
    "youtube": "#Tech",
    "instagram": "#BrandStory",
    "tiktok": "#fyp #BuildInPublic",
    "x": "#BuildInPublic",
}

HOUR_OF_DAY = {"morning": 9, "noon": 12, "evening": 18}

PLATFORM_BASE_IMPRESSIONS = {
    "linkedin": 900,
    "facebook": 1200,
    "youtube": 1500,
    "instagram": 1100,
    "tiktok": 2500,
    "x": 700,
}


def seed_for(*parts: str) -> random.Random:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return random.Random(digest)


class HeuristicProvider(LLMProvider):
    name = "heuristic"

    async def health(self) -> bool:
        return True

    async def chat(
        self,
        system: str,
        user: str,
        json_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        try:
            ctx = json.loads(user)
        except Exception:
            ctx = {}
        task = ctx.get("task", "")
        product = ctx.get("product", {})
        node_id = str(ctx.get("node_id", ""))
        rng = seed_for(product.get("name", ""), node_id, task)
        if task == "graph":
            return json.dumps(self.graph(ctx))
        if task == "posts":
            return json.dumps({"posts": self.posts(ctx, rng)})
        if task == "creative":
            return json.dumps({"notes": self.creative(ctx, rng)})
        if task == "schedule":
            return json.dumps({"slots": self.schedule(ctx)})
        if task == "notes":
            return json.dumps({"notes": self.notes(ctx)})
        if task == "recommend":
            return json.dumps(self.recommend(ctx))
        if task == "analysis":
            return json.dumps(self.analysis(ctx, rng))
        if task == "competitor":
            return json.dumps(self.competitor(ctx, rng))
        return json.dumps({"note": "heuristic fallback"})

    # -- generators -----------------------------------------------------

    def graph(self, ctx: dict) -> dict:
        connected = ctx.get("connected_platforms", [])
        product = ctx.get("product", {})
        rng = seed_for(product.get("name", ""), "graph")
        segments = rng.sample(list(SEGMENT_LABELS), 2)
        channels = list(connected) if connected else ["linkedin", "instagram", "tiktok"]
        channels = (channels + [p for p in ("linkedin", "instagram", "tiktok") if p not in channels])[:3]
        tones = rng.sample(list(HOOKS), 2)
        formats = ["text_post", "short_video"]

        nodes, edges = [], []
        nodes.append({"id": "n_goal", "type": "goal", "position": {"x": 300, "y": 0},
                      "params": {"objective": "awareness", "horizon_weeks": 4}})
        for i, seg in enumerate(segments):
            nodes.append({"id": f"n_aud{i+1}", "type": "audience",
                          "position": {"x": 120 + i * 360, "y": 130},
                          "params": {"segment": seg, "temperature_of_audience": rng.choice(["cold", "warm"])}})
            edges.append({"id": f"e_goal_aud{i+1}", "source": "n_goal", "target": f"n_aud{i+1}"})
        for i, (fmt, tone) in enumerate(zip(formats, tones)):
            nodes.append({"id": f"n_cnt{i+1}", "type": "content",
                          "position": {"x": 120 + i * 360, "y": 260},
                          "params": {"format": fmt, "tone": tone, "cta": rng.choice(list(CTAS))}})
            edges.append({"id": f"e_aud{i+1}_cnt{i+1}", "source": f"n_aud{i+1}", "target": f"n_cnt{i+1}"})
        for i, plat in enumerate(channels):
            nodes.append({"id": f"n_ch{i+1}", "type": "channel",
                          "position": {"x": 60 + i * 260, "y": 520},
                          "params": {"platform": plat, "priority": 8 - i}})
            edges.append({"id": f"e_cnt{(i % 2)+1}_ch{i+1}", "source": f"n_cnt{(i % 2)+1}", "target": f"n_ch{i+1}"})
        nodes.append({"id": "n_cad1", "type": "cadence", "position": {"x": 620, "y": 260},
                      "params": {"posts_per_week": 5, "time_of_day": "morning", "duration_weeks": 4}})
        for i in range(len(channels)):
            edges.append({"id": f"e_cad1_ch{i+1}", "source": "n_cad1", "target": f"n_ch{i+1}"})
        nodes.append({"id": "n_exp1", "type": "experiment", "position": {"x": 620, "y": 520},
                      "params": {"variant": "hook", "traffic_pct": 15}})
        edges.append({"id": "e_exp1_ch1", "source": "n_exp1", "target": "n_ch1"})
        return {"version": 1, "nodes": nodes, "edges": edges}

    def posts(self, ctx: dict, rng: random.Random) -> list[str]:
        params = ctx.get("params", {})
        product = ctx.get("product", {})
        n = int(ctx.get("n", 4))
        tone = params.get("tone", "bold")
        cta = params.get("cta", "signup")
        platform = params.get("platform", "linkedin")
        segment = SEGMENT_LABELS.get(params.get("segment", "marketers"), "growth teams")
        out = []
        for _ in range(n):
            out.append(
                f"{HOOKS.get(tone, HOOKS['bold'])} {product.get('name', 'Our product')} helps "
                f"{segment} {rng.choice(BENEFITS)}. {CTAS.get(cta, CTAS['signup'])} {TAGS.get(platform, '')}"
            )
        return out

    def creative(self, ctx: dict, rng: random.Random) -> list[str]:
        params = ctx.get("params", {})
        n = int(ctx.get("n", 4))
        fmt = params.get("format", "text_post")
        styles = [
            f"High-contrast card in brand red/black, headline hook, {fmt} framing",
            f"Product screenshot with annotated arrows, mono caption strip, {fmt} framing",
            f"Founder-style selfie frame with bold stat overlay, {fmt} framing",
            f"Minimal kinetic-type animation, 3 beats, {fmt} framing",
        ]
        return [styles[rng.randrange(len(styles))] for _ in range(n)]

    def schedule(self, ctx: dict) -> list[str]:
        params = ctx.get("params", {})
        n = int(ctx.get("n", 4))
        hour = HOUR_OF_DAY.get(params.get("time_of_day", "morning"), 9)
        start = datetime.now(timezone.utc).replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return [(start + timedelta(days=i, minutes=15 * i)).isoformat() for i in range(n)]

    def notes(self, ctx: dict) -> list[str]:
        product = ctx.get("product", {})
        counts = ctx.get("node_counts", {})
        name = product.get("name", "The product")
        return [
            f"Lead with outcome, not features: {name} sells time back, not tooling.",
            f"Focus on {counts.get('audience', 2)} segments max this horizon; breadth kills early signal.",
            "Publish hooks as experiments: 15% traffic to the variant node before scaling.",
            "Route short-video to tiktok/instagram and long-form to youtube/linkedin only.",
            "Review resolution rate weekly; below 80% triggers a cadence cut, not a spend increase.",
        ]

    def recommend(self, ctx: dict) -> dict:
        stats = sorted(ctx.get("platforms", []), key=lambda p: p.get("impressions", 0), reverse=True)
        ranking = []
        for i, p in enumerate(stats):
            if not stats:
                break
            top = stats[0].get("impressions", 0) or 1
            score = max(1, round(100 * p.get("impressions", 0) / top))
            if i == 0:
                reason = f"strongest reach ({p.get('impressions', 0):,} impressions) — scale here first"
            elif p.get("likes", 0) >= p.get("impressions", 0) * 0.04:
                reason = "high engagement ratio — good for community building"
            else:
                reason = "supporting channel — keep a light cadence"
            ranking.append({"platform": p.get("platform"), "score": score, "reason": reason})
        return {"ranking": ranking, "best": ranking[0]["platform"] if ranking else "linkedin"}

    def analysis(self, ctx: dict, rng: random.Random) -> dict:
        s = ctx.get("summary", {})
        best = s.get("best_channel", "linkedin")
        narrative = (
            f"Across {s.get('total_posts', 0)} simulated posts you reached "
            f"{s.get('total_impressions', 0):,} impressions with a "
            f"{s.get('resolution_rate', 0):.1f}% autonomous resolution rate. {best.title()} is your "
            f"strongest channel; evening slots outperform the median and your hook variants are "
            f"driving the majority of clicks."
        )
        suggestions = [
            f"Shift 20% of {best} budget into short-video formats to compound reach.",
            "Double down on the top hook variant; retire the weakest CTA.",
            "Move two posts per week into evening slots where engagement peaks.",
            "Add a retention objective node after week 2 to convert awareness into repeat usage.",
        ]
        return {"narrative": narrative, "suggestions": suggestions}

    def competitor(self, ctx: dict, rng: random.Random) -> dict:
        comp = ctx.get("competitor", {})
        product = ctx.get("product", {})
        narrative = (
            f"Based on the public notes you provided, {comp.get('name', 'the competitor')} competes "
            f"on price and legacy integrations, while {product.get('name', 'your product')} wins on "
            f"automation depth and speed-to-value. Their content cadence is heavier on long-form; "
            f"their short-form presence is thin."
        )
        suggestions = [
            "Publish 2 short-form teardown posts per week against their legacy workflow.",
            "Add a public ROI calculator page; they have none and buyers compare on this.",
            "Target their thin platform: win their absent channel with a consistent cadence.",
            "Collect 3 customer switch-stories and turn them into a carousel series.",
        ]
        return {"narrative": narrative, "suggestions": suggestions}
