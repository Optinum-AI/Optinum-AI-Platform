import { useState } from "react";
import { Share2, Package, Play, BarChart3, UploadCloud, ArrowRight, X } from "lucide-react";

const STEPS = [
  {
    icon: Share2,
    title: "1 • Connect your channels",
    body: "Open Social Hub. With developer credentials (Integrations page) connections go LIVE via real OAuth; otherwise they run in clearly-labeled SIM mode so you can explore safely.",
  },
  {
    icon: Package,
    title: "2 • Initialize your product",
    body: "Product Builder takes a name + description (or a preset). The Strategist bot reads it and drafts your whole pipeline as a node graph.",
  },
  {
    icon: Play,
    title: "3 • Run the strategy graph",
    body: "In Strategy Studio you steer the fleet visually — drag nodes, turn dials, no prompts. Run Strategy and watch 5 bots write, design, schedule and publish.",
  },
  {
    icon: BarChart3,
    title: "4 • Read the telemetry",
    body: "Engagement shows volume, resolution rate and the Analyst bot's recommendation of which social media is best for you — real metrics when LIVE, labeled SIM otherwise.",
  },
  {
    icon: UploadCloud,
    title: "5 • Upload your own content",
    body: "Content Studio: upload an asset or draft a caption with the Copywriter bot, pick channels, and publish through each platform's official API.",
  },
];

export default function FirstRunTour({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(0);
  const s = STEPS[step];
  const Icon = s.icon;
  const last = step === STEPS.length - 1;

  return (
    <div className="fixed inset-0 z-[90] bg-black/85 flex items-center justify-center p-6">
      <div className="card bg-card2 w-full max-w-lg p-8 relative overflow-hidden">
        <button className="absolute top-4 right-4 text-salmon hover:text-white" onClick={onClose} aria-label="Skip tour">
          <X size={16} />
        </button>
        <div className="micro">First-Run Demo • {step + 1}/{STEPS.length}</div>
        <div className="mt-6 flex items-center gap-4">
          <div className="w-14 h-14 rounded-lg bg-accent/15 border border-accent flex items-center justify-center tour-float shrink-0">
            <Icon size={22} className="text-accent2" />
          </div>
          <h2 className="text-xl font-bold">{s.title}</h2>
        </div>
        <p className="text-sm text-salmon/80 mt-4 leading-relaxed">{s.body}</p>
        <div className="flex items-center justify-between mt-8">
          <div className="flex gap-1.5">
            {STEPS.map((_, i) => (
              <span key={i} className={`h-1.5 rounded-full transition-all ${i === step ? "w-6 bg-accent" : "w-1.5 bg-line"}`} />
            ))}
          </div>
          <div className="flex gap-3">
            <button className="text-salmon/70 text-xs hover:text-white" onClick={onClose}>Skip</button>
            <button className="btn-accent flex items-center gap-2" onClick={() => (last ? onClose() : setStep(step + 1))}>
              {last ? "Start Automating" : "Next"} {!last && <ArrowRight size={13} />}
            </button>
          </div>
        </div>
        <style>{`
          .tour-float { animation: tour-float 2.2s ease-in-out infinite; }
          @keyframes tour-float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
        `}</style>
      </div>
    </div>
  );
}
