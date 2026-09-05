import type { LogEntry } from "../../api/types";
import { BOT_LABELS } from "./botLabels";

export default function RunLogPanel({ logs, status }: { logs: LogEntry[]; status: string }) {
  return (
    <div className="card bg-panel p-4 h-56 overflow-y-auto font-mono text-[11px] space-y-1.5">
      <div className="text-salmon/60">
        execution status: <span className={status === "completed" ? "text-pos" : status === "failed" ? "text-accent2" : "text-salmon animate-pulse"}>{status}</span>
      </div>
      {logs.map((l, i) => (
        <div key={i} className="flex gap-2 items-start">
          <span className="text-salmon/40 shrink-0">▸</span>
          <span className="text-accent2 shrink-0 w-20">{l.type}</span>
          <span className="text-salmon shrink-0 w-40">{BOT_LABELS[l.persona] ?? l.persona}</span>
          <span className={l.provider === "ollama" ? "text-pos shrink-0" : "text-salmon/50 shrink-0"}>[{l.provider}]</span>
          <span className="text-salmon/40 shrink-0">{l.ms}ms</span>
          <span className="text-salmon/80">{l.excerpt}</span>
        </div>
      ))}
      {logs.length === 0 && <div className="text-salmon/40">No executions yet — press Run Strategy.</div>}
    </div>
  );
}
