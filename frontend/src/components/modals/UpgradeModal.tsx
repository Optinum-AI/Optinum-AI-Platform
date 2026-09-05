import { useState } from "react";
import Modal from "../ui/Modal";
import { Check } from "lucide-react";
import { post } from "../../api/client";
import { useAuth } from "../../state/AuthContext";

const tiers = [
  {
    id: "growth",
    label: "Growth Pro",
    price: "$1,250/mo",
    blurb: "For scaling startups deploying automated lead generation.",
    features: ["Up to 50 active agent nodes", "Sub-25ms response latency", "10 connected social nodes", "Standard SLA & Email Support"],
  },
  {
    id: "unlimited",
    label: "Optinum Unlimited",
    price: "$4,850/mo",
    blurb: "Full autonomous multi-agent fleet with custom fine-tuned weights.",
    features: [
      "500+ concurrent agent nodes",
      "Sub-10ms dedicated edge VPC",
      "Unlimited social & CRM webhooks",
      "24/7 dedicated AI architecture team",
    ],
    recommended: true,
  },
];

export default function UpgradeModal({ onClose }: { onClose: () => void }) {
  const [selected, setSelected] = useState("unlimited");
  const [busy, setBusy] = useState(false);
  const { refresh } = useAuth();

  const confirm = async () => {
    setBusy(true);
    try {
      await post("/billing/upgrade", { tier: selected });
      await refresh();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Upgrade to Optinum Enterprise Pro" micro="Cluster Scaling Matrix" onClose={onClose} wide>
      <p className="text-xs text-salmon/70 -mt-4 mb-6">
        Scale autonomous agent capacity, unlock sub-10ms dedicated edge clusters, and get unlimited pipelines.
      </p>
      <div className="grid grid-cols-2 gap-4">
        {tiers.map((t) => (
          <button
            key={t.id}
            onClick={() => setSelected(t.id)}
            className={`text-left rounded-lg p-5 border transition-colors relative ${
              selected === t.id ? "border-accent bg-accent/10" : "border-line bg-card hover:border-salmon/40"
            }`}
          >
            {t.recommended && (
              <span className="absolute top-3 right-3 bg-accent text-white font-mono text-[9px] uppercase px-2 py-0.5 rounded">Recommended</span>
            )}
            <div className="flex items-baseline justify-between">
              <span className="font-bold">{t.label}</span>
              <span className="font-mono text-salmon text-sm">{t.price}</span>
            </div>
            <p className="text-xs text-salmon/70 mt-2">{t.blurb}</p>
            <ul className="mt-4 space-y-2">
              {t.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-xs text-salmon/90">
                  <Check size={13} className="text-pos mt-0.5 shrink-0" /> {f}
                </li>
              ))}
            </ul>
          </button>
        ))}
      </div>
      <div className="flex items-center justify-end gap-4 mt-6">
        <button className="text-salmon/70 text-sm hover:text-white" onClick={onClose}>Cancel</button>
        <button className="btn-accent" disabled={busy} onClick={confirm}>
          {busy ? "Provisioning..." : "Confirm Enterprise Provisioning"}
        </button>
      </div>
    </Modal>
  );
}
