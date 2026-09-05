import { useNavigate } from "react-router-dom";
import { Banknote, Loader, Share2, Bot, ArrowUpRight, Package, Play, Link2 } from "lucide-react";
import StatCard from "../components/ui/StatCard";
import { useFetch } from "../hooks/useFetch";
import { get, post } from "../api/client";
import type { Overview } from "../api/types";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data, refetch } = useFetch(() => get<Overview>("/analytics/overview"));

  const runLatest = async () => {
    if (!data?.pipelines.length) return navigate("/product-builder");
    const sid = data.pipelines[0].strategy_id;
    await post(`/strategies/${sid}/run`);
    navigate(`/strategy/${sid}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="micro flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" /> Mission Control • Fleet V4.2
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold mt-2">Autonomous Command Overview</h1>
          <p className="text-salmon/70 text-sm mt-2">
            Global snapshot of automated pipelines, revenue generation nodes, and live multi-agent clusters.
          </p>
        </div>
        <button className="btn-accent flex items-center gap-2" onClick={() => navigate("/product-builder")}>
          <Package size={15} /> Launch Product Model
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Total Run-Rate" value={data?.run_rate ?? "—"} delta={data?.run_rate_delta ?? ""} icon={<Banknote size={16} />} />
        <StatCard label="Resolution Rate" value={`${data?.resolution_rate ?? 0}%`} delta={`Target ${data?.resolution_target ?? 85}% • Optimal`} icon={<Loader size={16} />} />
        <StatCard label="Connected Channels" value={`${data?.connected_channels ?? 0} Nodes`} delta="Syncing Active (100% SLA)" icon={<Share2 size={16} />} />
        <StatCard label="Active Fleet" value={`${data?.active_fleet ?? 0} Agents`} delta={`${data?.roi_pct ?? 0}% ROI Generated`} icon={<Bot size={16} />} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="card p-5 xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold">Core Autonomous Pipelines</h2>
              <p className="text-xs text-salmon/60 mt-1">Active business logic models translating inbound signals directly into revenue.</p>
            </div>
            <button className="btn-ghost flex items-center gap-1" onClick={() => navigate("/product-builder")}>
              Build New Model <ArrowUpRight size={12} />
            </button>
          </div>
          <div className="space-y-3">
            {(data?.pipelines ?? []).length === 0 && (
              <div className="border border-dashed border-line rounded p-6 text-center text-sm text-salmon/60">
                No pipelines yet. Launch your first product model to let the agent fleet build your strategy.
              </div>
            )}
            {(data?.pipelines ?? []).map((p) => (
              <button
                key={p.id}
                onClick={() => navigate(`/strategy/${p.strategy_id}`)}
                className="w-full text-left card bg-card2 p-4 flex items-center justify-between hover:border-accent/60 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-accent" />
                  <div>
                    <div className="text-sm font-semibold">{p.name}</div>
                    <div className="text-[11px] text-salmon/60 mt-0.5 max-w-md truncate">{p.description}</div>
                  </div>
                </div>
                <div className="font-mono text-salmon text-sm">{p.yield_usd} Yield</div>
              </button>
            ))}
          </div>
        </div>

        <div className="card p-5">
          <h2 className="font-bold">Command Actions</h2>
          <p className="text-xs text-salmon/60 mt-1 mb-4">Quick operational controls for instant execution.</p>
          <div className="space-y-3">
            <button className="w-full card bg-card2 p-3 flex items-center gap-3 hover:border-accent/60 text-left" onClick={() => navigate("/product-builder")}>
              <Package size={15} className="text-accent2" />
              <div><div className="text-xs font-semibold">Initialize Core Product</div><div className="micro text-salmon/50 mt-0.5">Ready</div></div>
            </button>
            <button className="w-full card bg-card2 p-3 flex items-center gap-3 hover:border-accent/60 text-left" onClick={runLatest}>
              <Play size={15} className="text-accent2" />
              <div><div className="text-xs font-semibold">Run Latest Strategy</div><div className="micro text-salmon/50 mt-0.5">Autonomous</div></div>
            </button>
            <button className="w-full card bg-card2 p-3 flex items-center gap-3 hover:border-accent/60 text-left" onClick={() => navigate("/social-hub")}>
              <Link2 size={15} className="text-accent2" />
              <div><div className="text-xs font-semibold">Link a Channel</div><div className="micro text-salmon/50 mt-0.5">OAuth Sim</div></div>
            </button>
          </div>
          <button className="btn-ghost w-full mt-4" onClick={() => refetch()}>Refresh Telemetry</button>
        </div>
      </div>
    </div>
  );
}
