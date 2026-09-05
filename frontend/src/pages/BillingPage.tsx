import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { useFetch } from "../hooks/useFetch";
import { get } from "../api/client";
import type { Billing } from "../api/types";
import UpgradeModal from "../components/modals/UpgradeModal";

export default function BillingPage() {
  const { data, refetch } = useFetch(() => get<Billing>("/billing"));
  const [showUpgrade, setShowUpgrade] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="micro">Subscription & Quota Allocation</div>
          <h1 className="text-3xl md:text-4xl font-extrabold mt-2">Billing & Invoices</h1>
          <p className="text-salmon/70 text-sm mt-2">
            Manage your Optinum AI Enterprise cluster tier, API billing quotas, and automated receipts.
          </p>
        </div>
        <button className="btn-accent flex items-center gap-2" onClick={() => setShowUpgrade(true)}>
          <ArrowUpRight size={14} /> Upgrade Tier
        </button>
      </div>

      <div className="card p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="micro bg-accent text-white px-2 py-1 rounded">Active {data?.plan ?? "free"}</span>
              <span className="font-mono text-[10px] text-pos">Billing Cycle: Monthly</span>
            </div>
            <h2 className="text-2xl font-bold mt-3">{data?.tier.label ?? "Starter"}</h2>
            <p className="text-xs text-salmon/60 mt-1">
              Unlimited multi-agent concurrency, dedicated edge VPCs, sub-14ms telemetry, and white-glove SLA.
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-extrabold">${(data?.tier.price ?? 0).toLocaleString()}<span className="text-sm text-salmon/60">/mo</span></div>
            <div className="font-mono text-[10px] text-pos mt-1">Net ROI: 342%</div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6 border-t border-line/60 pt-5">
          <Quota label="Agent Instances" used={`${data?.quotas.agents.used ?? 0}`} max={` / ${data?.quotas.agents.max ?? 0}`} pct={data ? data.quotas.agents.used / data.quotas.agents.max : 0} />
          <Quota label="Inference Tokens" used={data?.quotas.tokens.used_label ?? "0M"} max={` / ${data?.quotas.tokens.max ?? ""}`} pct={0.2} />
          <Quota label="Social Sync Nodes" used={`${data?.quotas.nodes.used ?? 0}`} max={` / ${data?.quotas.nodes.max ?? 0}`} pct={data ? data.quotas.nodes.used / data.quotas.nodes.max : 0} green />
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-bold mb-4">Recent Invoices & Receipts</h2>
        <div className="overflow-x-auto"><table className="w-full text-xs">
          <thead>
            <tr className="micro text-left"><th className="pb-2">Invoice</th><th className="pb-2">Date</th><th className="pb-2">Amount</th><th className="pb-2">Status</th></tr>
          </thead>
          <tbody>
            {(data?.invoices ?? []).map((i) => (
              <tr key={i.id} className="border-t border-line/60">
                <td className="py-3 font-mono">{i.id}</td>
                <td className="py-3 text-salmon/70">{i.date}</td>
                <td className="py-3">{i.amount}</td>
                <td className="py-3"><span className="font-mono text-[9px] uppercase text-pos border border-pos/50 bg-pos/10 px-2 py-0.5 rounded">{i.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table></div>
      </div>

      {showUpgrade && <UpgradeModal onClose={() => { setShowUpgrade(false); refetch(); }} />}
    </div>
  );
}

function Quota({ label, used, max, pct, green }: { label: string; used: string; max: string; pct: number; green?: boolean }) {
  return (
    <div>
      <div className="flex justify-between font-mono text-[10px]">
        <span className="text-salmon/60">{label}</span>
        <span>{used}<span className="text-salmon/50">{max}</span></span>
      </div>
      <div className="h-1 bg-card2 rounded mt-2 overflow-hidden">
        <div className={`h-full ${green ? "bg-pos" : "bg-salmon"}`} style={{ width: `${Math.min(100, pct * 100)}%` }} />
      </div>
    </div>
  );
}
