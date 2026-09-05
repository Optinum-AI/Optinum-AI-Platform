import { useRef, useState } from "react";
import { UploadCloud, Sparkles, Send, Image as ImageIcon, Film } from "lucide-react";
import { useFetch } from "../hooks/useFetch";
import { get, post, api } from "../api/client";
import type { Connection } from "../api/types";
import { PLATFORMS } from "./SocialHubPage";

interface HistoryRow {
  id: string;
  platform: string;
  content_text: string;
  asset_path: string | null;
  status: string;
  error: string | null;
  created_at: string;
}

export default function ContentStudioPage() {
  const { data: connections } = useFetch(() => get<Connection[]>("/connections"));
  const { data: history, refetch } = useFetch(() => get<HistoryRow[]>("/content/history"));
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [results, setResults] = useState<{ platform: string; status: string; mode: string; error: string | null }[] | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const livePlatforms = new Set(
    (connections ?? [])
      .filter((c) => c.status === "active" && (c.mode === "real" || c.mode === "browser"))
      .map((c) => c.platform)
  );

  const pickFile = (f: File | null) => {
    setFile(f);
    setPreview(f && f.type.startsWith("image/") ? URL.createObjectURL(f) : null);
  };

  const draft = async () => {
    setDrafting(true);
    try {
      const r = await post<{ text: string }>("/content/suggest", { topic: "", tone: "bold" });
      setText(r.text);
    } finally {
      setDrafting(false);
    }
  };

  const publish = async () => {
    setBusy(true);
    setResults(null);
    try {
      const fd = new FormData();
      fd.append("text", text);
      fd.append("platforms", JSON.stringify(selected));
      if (file) fd.append("file", file);
      const r = await api<{ results: typeof results }>("/content/publish", { method: "POST", body: fd, headers: {} });
      setResults(r.results);
      await refetch();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="micro flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-accent" /> Upload • Compose • Distribute
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold mt-2">Content Studio</h1>
        <p className="text-salmon/70 text-sm mt-2 max-w-2xl">
          Upload your content first, pick the channels, and the fleet pushes it through each platform's
          official API when LIVE — or labeled SIM otherwise.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="card p-6 xl:col-span-2 space-y-5">
          <div className="flex items-center justify-between">
            <label className="micro">Caption</label>
            <button className="btn-ghost flex items-center gap-2" onClick={draft} disabled={drafting}>
              <Sparkles size={12} /> {drafting ? "Copywriter bot drafting..." : "Draft with AI"}
            </button>
          </div>
          <textarea
            className="input min-h-28 resize-none border border-line rounded p-3"
            placeholder="Write your post, or let the Copywriter bot draft it..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />

          <div>
            <label className="micro block mb-2">Media Asset</label>
            <button
              className="w-full border border-dashed border-salmon/40 rounded-lg p-4 flex items-center gap-4 hover:border-accent transition-colors text-left"
              onClick={() => fileRef.current?.click()}
            >
              {preview ? (
                <img src={preview} alt="preview" className="w-16 h-16 object-cover rounded border border-line" />
              ) : file ? (
                <Film size={28} className="text-salmon/60" />
              ) : (
                <ImageIcon size={28} className="text-salmon/50" />
              )}
              <div>
                <div className="text-sm font-semibold">{file ? file.name : "Click to upload image / video"}</div>
                <div className="text-[11px] text-salmon/50 mt-0.5">
                  X, Facebook, and Discord upload media directly in LIVE mode; Instagram/TikTok/YouTube officially require a public media URL.
                </div>
              </div>
            </button>
            <input ref={fileRef} type="file" accept="image/*,video/*" className="hidden" onChange={(e) => pickFile(e.target.files?.[0] ?? null)} />
          </div>

          <div>
            <label className="micro block mb-2">Distribute To</label>
            <div className="flex flex-wrap gap-2">
              {PLATFORMS.map((p) => {
                const on = selected.includes(p.id);
                const live = livePlatforms.has(p.id);
                return (
                  <button
                    key={p.id}
                    onClick={() => setSelected((s) => (on ? s.filter((x) => x !== p.id) : [...s, p.id]))}
                    className={`px-3 py-1.5 rounded border font-mono text-[10px] uppercase tracking-wider transition-colors ${
                      on ? "border-accent bg-accent/20 text-white" : "border-line text-salmon/70 hover:border-salmon/50"
                    }`}
                  >
                    {p.label} • {live ? "LIVE" : "SIM"}
                  </button>
                );
              })}
            </div>
          </div>

          <button className="btn-accent w-full py-3 flex items-center justify-center gap-2" disabled={busy || selected.length === 0} onClick={publish}>
            <Send size={14} /> {busy ? "Distributing..." : "Upload & Publish"}
          </button>

          {results && (
            <div className="card bg-panel p-4 space-y-2 font-mono text-[11px]">
              {results.map((r) => (
                <div key={r.platform} className="p-2 bg-card2/80 rounded border border-line/40">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-bold uppercase">{r.platform}</span>
                      <span
                        className={
                          r.status === "published"
                            ? "text-pos font-semibold"
                            : r.status === "failed"
                            ? "text-accent2 font-semibold"
                            : "text-amber-400"
                        }
                      >
                        {r.status}
                      </span>
                      <span className="text-salmon/50">[{r.mode}]</span>
                    </div>
                  </div>
                  {r.error && (
                    <div className="mt-1 text-salmon/70 flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-line/20">
                      <span>{r.error}</span>
                      {(r.error.includes("Social Hub") || r.error.includes("session")) && (
                        <a
                          href="/social-hub"
                          className="px-2 py-0.5 rounded bg-accent/20 border border-accent hover:bg-accent/30 text-white text-[10px] font-sans flex items-center gap-1 transition"
                        >
                          Connect in Social Hub →
                        </a>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card p-5">
          <h2 className="font-bold flex items-center gap-2"><UploadCloud size={15} className="text-accent2" /> Publish History</h2>
          <div className="space-y-3 mt-4 max-h-[560px] overflow-y-auto">
            {(history ?? []).length === 0 && <p className="text-xs text-salmon/60">Nothing published yet.</p>}
            {(history ?? []).map((h) => (
              <div key={h.id} className="card bg-card2 p-3">
                <div className="flex justify-between font-mono text-[9px] uppercase">
                  <span className="text-pos">{h.platform}</span>
                  <span className={h.status === "published" ? "text-pos" : h.status === "failed" ? "text-accent2" : "text-amber-400"}>{h.status}</span>
                </div>
                <p className="text-[11px] text-salmon/80 mt-1 line-clamp-2">{h.content_text || "(media only)"}</p>
                {h.asset_path && <p className="text-[10px] text-salmon/50 mt-1 font-mono">{h.asset_path}</p>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
