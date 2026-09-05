import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Database, ScanEye, CheckCircle2, UploadCloud } from "lucide-react";
import { post, api } from "../api/client";
import type { Product, Strategy } from "../api/types";

const PRESETS = ["Nexus", "OmniFlow", "FinPulse"];

function suggestCampaign(name: string, description: string) {
  const text = `${name} ${description}`.toLowerCase();
  const recommendations = [
    { platform: "linkedin", score: 0, label: "LinkedIn", reason: "Best for B2B trust, founder story, and professional authority." },
    { platform: "instagram", score: 0, label: "Instagram", reason: "Best for visual storytelling and product lifestyle content." },
    { platform: "facebook", score: 0, label: "Facebook", reason: "Best for community engagement and broad reach campaigns." },
    { platform: "youtube", score: 0, label: "YouTube", reason: "Best for product demos, tutorials, and educational video assets." },
    { platform: "tiktok", score: 0, label: "TikTok", reason: "Best for short-form trend-driven discovery and awareness." },
  ];

  const boosts: Record<string, string[]> = {
    linkedin: ["b2b", "saas", "enterprise", "business", "software", "analytics", "finance", "marketing", "lead"],
    instagram: ["fashion", "beauty", "lifestyle", "visual", "brand", "shop", "product", "photo", "design"],
    facebook: ["community", "local", "events", "groups", "service", "support", "retail", "reach"],
    youtube: ["video", "tutorial", "demo", "how-to", "training", "education", "review", "product"],
    tiktok: ["viral", "short", "trend", "creator", "social", "launch", "story", "reels", "tiktok"],
  };

  for (const item of recommendations) {
    const keywords = boosts[item.platform] ?? [];
    item.score = keywords.reduce((sum, keyword) => sum + (text.includes(keyword) ? 22 : 0), 12);
  }

  const ranked = recommendations.sort((a, b) => b.score - a.score);
  const primary = ranked[0] ?? recommendations[0];
  const secondary = ranked.slice(1, 4).map((item) => item.label);
  const plan = `Launch the ${primary.label} campaign first with a ${primary.label === "YouTube" || primary.label === "TikTok" ? "video-first" : "story-led"} offer, then expand to ${secondary.join(", ")}.`;

  return { primary, secondary, plan };
}

export default function ProductBuilderPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [preset, setPreset] = useState<string | null>(null);
  const [logo, setLogo] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const recommendation = suggestCampaign(name, description);

  const applyPreset = (p: string) => {
    setPreset(p);
    setName(p === "Nexus" ? "Nexus Automation Suite" : p === "OmniFlow" ? "OmniFlow Orchestrator" : "FinPulse Revenue AI");
    setDescription("");
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await post<{ product: Product; strategy: Strategy }>("/products", { name, description, preset });
      if (logo) {
        const fd = new FormData();
        fd.append("file", logo);
        await api(`/products/${res.product.id}/logo`, { method: "POST", body: fd, headers: {} });
      }
      navigate(`/strategy/${res.strategy.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="micro flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent" /> System Ready • Optinum Engine V4.2
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold mt-2">Initialize Product</h1>
          <p className="text-salmon/70 text-sm mt-2 max-w-2xl">
            Deploy essential product parameters into the Optinum AI engine to generate your automated
            business model and autonomous agent fleet.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-salmon/60 font-mono">Presets:</span>
          {PRESETS.map((p) => (
            <button key={p} onClick={() => applyPreset(p)}
              className={`px-3 py-1.5 rounded border font-mono text-xs transition-colors ${
                preset === p ? "border-accent text-white bg-accent/20" : "border-line text-salmon hover:border-salmon/50"
              }`}>
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-6 space-y-6">
          <div className="flex items-center gap-2 font-bold"><Database size={16} className="text-accent2" /> Data Ingestion</div>
          <div>
            <label className="micro block mb-2">Product Designation</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nexus Automation Suite" />
          </div>
          <div>
            <label className="micro block mb-2">Functional Description</label>
            <textarea
              className="input min-h-32 resize-none border border-line rounded p-3"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Autonomous multi-agent customer acquisition, tier qualification, and cross-channel CRM reconciliation pipeline with automated revenue recovery."
            />
          </div>
          {error && <p className="text-xs text-accent2 font-mono">{error}</p>}
          <div className="rounded border border-accent/40 bg-accent/5 p-4">
            <div className="micro uppercase tracking-wide text-accent2">AI campaign recommendation</div>
            <div className="mt-2 flex items-center justify-between gap-3">
              <div>
                <div className="text-lg font-bold">Best platform: {recommendation.primary.label}</div>
                <p className="text-xs text-salmon/70 mt-1">{recommendation.primary.reason}</p>
              </div>
              <span className="font-mono text-[10px] text-pos border border-pos/40 rounded px-2 py-1">{recommendation.primary.score}/100</span>
            </div>
            <div className="mt-3 text-[11px] text-salmon/75">
              <span className="font-semibold text-white">Plan:</span> {recommendation.plan}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {recommendation.secondary.map((item) => (
                <span key={item} className="rounded-full border border-line bg-card2 px-2 py-1 text-[10px] uppercase tracking-wide text-salmon/70">{item}</span>
              ))}
            </div>
          </div>
          <button className="btn-accent w-full py-3 mt-5" disabled={busy || !name.trim()} onClick={submit}>
            {busy ? "Strategist bot drafting your pipeline..." : "Generate Autonomous Strategy"}
          </button>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-2 font-bold mb-4"><ScanEye size={16} className="text-accent2" /> Visual Telemetry</div>
          <button
            className="w-full border border-dashed border-salmon/40 rounded-lg min-h-64 flex flex-col items-center justify-center gap-3 hover:border-accent transition-colors"
            onClick={() => fileRef.current?.click()}
          >
            {logo ? (
              <>
                <CheckCircle2 size={28} className="text-pos" />
                <div className="font-mono text-xs text-pos">Schematic Vector Ingested</div>
                <div className="text-[11px] text-salmon/60">{logo.name}</div>
              </>
            ) : (
              <>
                <UploadCloud size={28} className="text-salmon/50" />
                <div className="font-mono text-xs text-salmon/60">Click or drag to replace asset</div>
              </>
            )}
          </button>
          <input ref={fileRef} type="file" accept="image/*" className="hidden"
            onChange={(e) => setLogo(e.target.files?.[0] ?? null)} />
          <p className="text-[11px] text-salmon/50 mt-4">
            The Creative bot uses your brand asset as the visual anchor for every generated asset note.
          </p>
        </div>
      </div>
    </div>
  );
}
