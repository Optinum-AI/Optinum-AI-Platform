import StatCard from "../components/ui/StatCard";
import { useFetch } from "../hooks/useFetch";
import { get } from "../api/client";

interface Perf {
  stats: { label: string; value: string; delta: string; good: boolean }[];
  clusters: { name: string; region: string; agents: number; latency: string; load: string; status: string }[];
}

export default function PerformancePage() {
  const { data } = useFetch(() => get<Perf>("/analytics/performance"));
  return (
    <div className="space-y-6">
      <div>
        <div className="micro">Telemetry & Inference Metrics</div>
        <h1 className="text-3xl md:text-4xl font-extrabold mt-2">Performance Matrix</h1>
        <p className="text-salmon/70 text-sm mt-2">
          Cluster latency, inference throughput, error-budget tracking, and autonomous agent resolution SLAs.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {(data?.stats ?? []).map((s) => (
          <StatCard key={s.label} label={s.label} value={s.value} delta={s.delta} />
        ))}
      </div>
      <div className="card p-5">
        <h2 className="font-bold mb-4">Active Cluster Nodes</h2>
        <div className="overflow-x-auto"><table className="w-full text-xs">
          <thead>
            <tr className="micro text-left">
              <th className="pb-2">Node Cluster</th><th className="pb-2">Region</th><th className="pb-2">Active Agents</th>
              <th className="pb-2">Avg Latency</th><th className="pb-2">Load</th><th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {(data?.clusters ?? []).map((c) => (
              <tr key={c.name} className="border-t border-line/60">
                <td className="py-3 font-semibold">{c.name}</td>
                <td className="py-3 text-salmon/70">{c.region}</td>
                <td className="py-3">{c.agents}</td>
                <td className="py-3 text-pos">{c.latency}</td>
                <td className="py-3">{c.load}</td>
                <td className="py-3"><span className="font-mono text-[9px] uppercase text-pos border border-pos/50 bg-pos/10 px-2 py-0.5 rounded">{c.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table></div>
      </div>
    </div>
  );
}
