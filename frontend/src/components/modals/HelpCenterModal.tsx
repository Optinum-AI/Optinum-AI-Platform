import Modal from "../ui/Modal";
import { TerminalSquare, Share2, Headphones } from "lucide-react";

export default function HelpCenterModal({ onClose }: { onClose: () => void }) {
  return (
    <Modal title="Optinum AI Help Center" micro="Operational Assistance" onClose={onClose}>
      <div className="space-y-4">
        <div className="card bg-card p-4">
          <div className="flex items-center gap-2 text-sm font-semibold"><TerminalSquare size={15} className="text-accent2" /> System CLI Shortcuts</div>
          <p className="text-xs text-salmon/70 mt-2">Press <kbd className="px-1.5 py-0.5 bg-card2 border border-line rounded font-mono">⌘</kbd> + <kbd className="px-1.5 py-0.5 bg-card2 border border-line rounded font-mono">K</kbd> to open global parameter search anywhere.</p>
        </div>
        <div className="card bg-card p-4">
          <div className="flex items-center gap-2 text-sm font-semibold"><Share2 size={15} className="text-accent2" /> Social Nodes Ingestion</div>
          <p className="text-xs text-salmon/70 mt-2">OAuth tokens are refreshed autonomously every 60 minutes with zero downtime. Connections run in simulated dev mode until official API credentials are attached.</p>
        </div>
        <div className="card bg-card p-4">
          <div className="flex items-center gap-2 text-sm font-semibold"><Headphones size={15} className="text-accent2" /> Architecture On-Call</div>
          <p className="text-xs text-salmon/70 mt-2">Enterprise SLA provides sub-5 minute priority escalation via on-call bridge.</p>
        </div>
        <div className="flex justify-end pt-2">
          <button className="btn-accent" onClick={onClose}>Dismiss</button>
        </div>
      </div>
    </Modal>
  );
}
