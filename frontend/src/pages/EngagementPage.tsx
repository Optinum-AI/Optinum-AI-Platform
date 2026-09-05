import { useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Download, Filter, Plus, Trash2, Sparkles } from "lucide-react";
import { useFetch } from "../hooks/useFetch";
import { get, post, del } from "../api/client";
import type { Engagement, Competitor, Connection, Recommend } from "../api/types";

export default function EngagementPage() {
  const { data } = useFetch(() => get<Engagement>("/analytics/engagement"));
  const { data: insights } = useFetch(() => get<{ narrative: string; suggestions: string[]; provider: string }>("/analytics/insights"));
  const { data: competitors, refetch: refetchComp } = useFetch(() => get<Competitor[]>("/competitors"));
  const { data: conns } = useFetch(() => get<Connection[]>("/connections"));
  const { data: rec } = useFetch(() => get<Recommend>("/analytics/recommend"));
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  const anyLive = (conns ?? []).some((c) => c.mode === "real" && c.status === "active");

  const peak = useMemo(() => {
    if (!data?.volume.length) return null;
    return data.volume.reduce((a, b) => (b.volume > a.volume ? b : a));
  }, [data]);

  const exportLogs = async () => {
    const res = await fetch("/api/analytics/engagement", {
      headers: { Authorization: `Bearer ${localStorage.getItem("optimum_token")}` },
    });
    const blob = new Blob([JSON.stringify(await res.json(), null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "optimum-engagement-logs.json";
    a.click();
  };

  const addCompetitor = async () => {
    setBusy("add");
    try {
      await post("/competitors", { name, notes });
      setName("");
      setNotes("");
      await refetchComp();
    } finally {
      setBusy(null);
    }
  };

  const analyze = async (c: Competitor) => {
    setBusy(c.id);
    try {
      await post(`/competitors/${c.id}/analyze`);
      await refetchComp();
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="micro">Command Center ▸ Engagement Pulse</div>
          <h1 className="text-3xl md:text-4xl font-extrabold mt-2 flex items-center gap-3">
            Live Engagement Stream <span className="w-3 h-3 rounded-full bg-accent animate-pulse" />
          </h1>
          <p className="text-salmon/70 text-sm mt-2">
            Monitoring active AI conversations, autonomous resolution protocols, and live transcript telemetry.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost flex items-center gap-2"><Filter size={12} /> Filter: ALL</button>
          <button className="btn-ghost flex items-center gap-2" onClick={exportLogs}><Download size={12} /> Export Logs</button>
        </div>
      </div>

      {!anyLive && (
        <div className="micro border border-amber-400/50 text-amber-400 bg-amber-400/10 px-3 py-2 rounded flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          Simulated telemetry — link live accounts (Social Hub) to stream real platform metrics
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="card p-5 xl:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold">Interaction Volume</h2>
              <p className="text-xs text-salmon/60 mt-1">Cross-channel AI handled requests across global nodes</p>
            </div>
            {peak && <span className="micro border border-accent/60 text-accent2 px-2 py-1 rounded">+14.2% Peak</span>}
          </div>
          <div className="h-56 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.volume ?? []}>
                <XAxis dataKey="hour" stroke="#fca5a5" fontSize={10} tickLine={false} />
                <YAxis stroke="#262626" fontSize={10} tickLine={false} />
                <Tooltip contentStyle={{ background: "#141414", border: "1px solid #262626", fontSize: 12 }} labelStyle={{ color: "#fca5a5" }} />
                <Bar dataKey="volume" radius={[3, 3, 0, 0]}>
                  {(data?.volume ?? []).map((v) => (
                    <Cell key={v.hour} fill={peak && v.hour === peak.hour ? "#fca5a5" : "#3f3f46"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-5">
          <h2 className="font-bold">AI Resolution Rate</h2>
          <p className="text-xs text-salmon/60 mt-1">Automated issue closure without human escalation</p>
          <div className="text-5xl font-extrabold text-salmon mt-8">
            {data?.resolution_rate ?? 0}<span className="text-lg">%</span>
          </div>
          <div className="h-1.5 bg-card2 rounded mt-4 overflow-hidden">
            <div className="h-full bg-salmon" style={{ width: `${data?.resolution_rate ?? 0}%` }} />
          </div>
          <div className="flex justify-between font-mono text-[10px] mt-2">
            <span className="text-salmon/60">Target: 85%</span>
            <span className="text-pos">Optimal (+{(data?.resolution_rate ?? 0) - 85 > 0 ? ((data?.resolution_rate ?? 0) - 85).toFixed(1) : "0.0"} buffer)</span>
          </div>
          <div className="border-t border-line/60 mt-6 pt-4">
            <div className="micro mb-2 flex items-center gap-2"><Sparkles size={12} /> Analyst Bot Briefing</div>
            <p className="text-xs text-salmon/80 leading-relaxed">{insights?.narrative ?? "Run a strategy to generate analyst insights."}</p>
            <ul className="mt-3 space-y-1.5">
              {(insights?.suggestions ?? []).slice(0, 3).map((s, i) => (
                <li key={i} className="text-[11px] text-salmon/70 flex gap-2"><span className="text-accent2">▸</span>{s}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="card p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-bold flex items-center gap-2"><Sparkles size={15} className="text-accent2" /> Analyst Channel Recommendation</h2>
          <span className="micro text-salmon/50">via {rec?.provider ?? "…"}</span>
        </div>
        {!rec?.has_data && (
          <p className="text-xs text-salmon/60 mt-2">Run a strategy first — the Analyst bot ranks your channels from the telemetry it gathers.</p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          {(rec?.ranking ?? []).map((r, i) => (
            <div key={r.platform} className={`card bg-card2 p-4 ${i === 0 ? "border-pos/50" : ""}`}>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase text-pos">{r.platform}</span>
                <span className="font-mono text-[10px] text-salmon/70">{r.score}/100</span>
              </div>
              <div className="h-1 bg-card rounded mt-2 overflow-hidden">
                <div className={`h-full ${i === 0 ? "bg-pos" : "bg-salmon"}`} style={{ width: `${r.score}%` }} />
              </div>
              <p className="text-[11px] text-salmon/70 mt-2">{r.reason}</p>
              {i === 0 && <div className="micro text-pos mt-2">Best channel — scale here</div>}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="card p-5 xl:col-span-2">
          <h2 className="font-bold mb-4">Channel Breakdown</h2>
          <div className="overflow-x-auto"><table className="w-full text-xs">
            <thead>
              <tr className="micro text-left">
                <th className="pb-2">Platform</th><th className="pb-2">Posts</th><th className="pb-2">Impressions</th>
                <th className="pb-2">Likes</th><th className="pb-2">Comments</th><th className="pb-2">Shares</th>
              </tr>
            </thead>
            <tbody>
              {(data?.channels ?? []).map((c) => (
                <tr key={c.platform} className="border-t border-line/60">
                  <td className="py-2.5 font-mono uppercase text-pos">{c.platform}</td>
                  <td className="py-2.5">{c.posts}</td>
                  <td className="py-2.5 text-salmon">{(c.impressions ?? 0).toLocaleString()}</td>
                  <td className="py-2.5">{(c.likes ?? 0).toLocaleString()}</td>
                  <td className="py-2.5">{(c.comments ?? 0).toLocaleString()}</td>
                  <td className="py-2.5">{(c.shares ?? 0).toLocaleString()}</td>
                </tr>
              ))}
              {(data?.channels ?? []).length === 0 && (
                <tr><td colSpan={6} className="py-6 text-center text-salmon/50">No channel telemetry yet — run a strategy.</td></tr>
              )}
            </tbody>
          </table></div>
        </div>

        <div className="card p-5">
          <h2 className="font-bold">Competitor Tracking</h2>
          <p className="text-[11px] text-salmon/60 mt-1 mb-4">Public intel only — paste notes you already have; the Analyst bot compares and suggests improvements.</p>
          <div className="space-y-2 mb-4">
            <input className="input" placeholder="Competitor name" value={name} onChange={(e) => setName(e.target.value)} />
            <textarea className="input min-h-16 resize-none" placeholder="Public notes (pricing, cadence, gaps...)" value={notes} onChange={(e) => setNotes(e.target.value)} />
            <button className="btn-accent w-full flex items-center justify-center gap-2" disabled={busy === "add" || !name.trim()} onClick={addCompetitor}>
              <Plus size={13} /> Track Competitor
            </button>
          </div>
          <div className="space-y-3 max-h-72 overflow-y-auto">
            {(competitors ?? []).map((c) => {
              const analysis = c.analysis_json ? JSON.parse(c.analysis_json) : null;
              return (
                <div key={c.id} className="card bg-card2 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold">{c.name}</span>
                    <div className="flex gap-2">
                      <button className="btn-ghost" disabled={busy === c.id} onClick={() => analyze(c)}>
                        {busy === c.id ? "Analyzing..." : "Analyze"}
                      </button>
                      <button className="text-salmon/50 hover:text-accent2" onClick={async () => { await del(`/competitors/${c.id}`); refetchComp(); }}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                  {analysis && (
                    <div className="mt-2">
                      <p className="text-[11px] text-salmon/70">{analysis.narrative}</p>
                      <ul className="mt-2 space-y-1">
                        {(analysis.suggestions ?? []).map((s: string, i: number) => (
                          <li key={i} className="text-[10px] text-salmon/60 flex gap-1.5"><span className="text-pos">▸</span>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
