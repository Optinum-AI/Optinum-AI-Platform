import { useNavigate } from "react-router-dom";
import { Bell, Plus, Search, Settings, Menu, Sparkles } from "lucide-react";

export default function Topbar({
  onHelp,
  onMenu,
  onOpenCopilot,
}: {
  onHelp: () => void;
  onMenu: () => void;
  onOpenCopilot?: () => void;
}) {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-20 bg-ink/95 backdrop-blur border-b border-line/60 flex items-center justify-between gap-3 px-4 md:px-8 py-3 overflow-x-hidden">
      <div className="flex items-center gap-3">
        <button
          className="lg:hidden text-salmon hover:text-white transition-colors p-1"
          onClick={onMenu}
          aria-label="Open menu"
        >
          <Menu size={20} />
        </button>
        <div className="font-extrabold text-accent2 leading-none tracking-tight">
          Optinum <span className="text-white font-normal text-xs ml-1 font-mono uppercase tracking-widest">Enterprise</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative hidden md:block">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-salmon/50" />
          <input
            placeholder="Search channels, automations, posts..."
            className="bg-card border border-line rounded pl-9 pr-3 py-1.5 text-xs w-64 outline-none focus:border-accent placeholder-salmon/40 text-white"
          />
        </div>

        {onOpenCopilot && (
          <button
            className="px-3 py-1.5 rounded bg-accent/20 border border-accent/60 hover:bg-accent/30 text-white text-xs font-mono flex items-center gap-1.5 transition"
            onClick={onOpenCopilot}
          >
            <Sparkles size={13} className="text-cyan-400" />
            <span className="hidden sm:inline">AI Copilot</span>
          </button>
        )}

        <button
          className="btn-accent flex items-center gap-1.5 text-xs py-1.5"
          onClick={() => navigate("/product-builder")}
        >
          <Plus size={14} /> <span className="hidden sm:inline">New Pipeline</span>
        </button>

        <button className="relative text-salmon/80 hover:text-white transition p-1" aria-label="Notifications">
          <Bell size={17} />
          <span className="absolute 0 0 w-2 h-2 rounded-full bg-accent" />
        </button>

        <button
          className="text-salmon/80 hover:text-white transition p-1"
          onClick={onHelp}
          aria-label="Settings"
        >
          <Settings size={17} />
        </button>
      </div>
    </header>
  );
}
