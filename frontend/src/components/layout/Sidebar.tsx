import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutGrid, Share2, Package, Bot, Activity, CreditCard,
  Rocket, HelpCircle, LogOut, TerminalSquare, UploadCloud, PlayCircle,
} from "lucide-react";
import { useAuth } from "../../state/AuthContext";

const items = [
  { to: "/", label: "Overview", icon: LayoutGrid, end: true },
  { to: "/social-hub", label: "Social Hub", icon: Share2 },
  { to: "/product-builder", label: "Product Builder", icon: Package },
  { to: "/content", label: "Content Studio", icon: UploadCloud },
  { to: "/engagement", label: "AI Interactions", icon: Bot },
  { to: "/performance", label: "Performance", icon: Activity },
  { to: "/billing", label: "Billing", icon: CreditCard },
];

export default function Sidebar({
  onHelp,
  onUpgrade,
  onTour,
  open,
  onClose,
}: {
  onHelp: () => void;
  onUpgrade: () => void;
  onTour: () => void;
  open: boolean;
  onClose: () => void;
}) {
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <aside
      className={`fixed left-0 top-0 bottom-0 w-60 bg-panel border-r border-line flex flex-col z-40 transition-transform duration-200 ${
        open ? "translate-x-0" : "-translate-x-full"
      } lg:translate-x-0`}
    >
      <div className="flex items-center gap-3 px-5 py-5 border-b border-line/60">
        <div className="w-9 h-9 rounded bg-accent/20 border border-accent flex items-center justify-center shrink-0">
          <TerminalSquare size={18} className="text-accent2" />
        </div>
        <div className="min-w-0">
          <div className="font-bold text-salmon leading-tight truncate">Optinum AI</div>
          <div className="micro text-salmon/60">Business Automation</div>
        </div>
      </div>

      <nav className="flex-1 py-4 space-y-1 px-3 overflow-y-auto">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded text-sm font-mono tracking-wide border-l-2 transition-colors ${
                isActive
                  ? "bg-accent text-white border-accent shadow-[0_0_18px_rgba(220,38,38,0.35)]"
                  : "text-salmon/80 border-transparent hover:bg-card hover:text-white"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 pb-5 space-y-1 border-t border-line/60 pt-4">
        <button onClick={onUpgrade} className="w-full flex items-center gap-3 px-3 py-2.5 rounded border border-salmon/40 text-salmon hover:bg-card font-mono text-xs uppercase tracking-wider">
          <Rocket size={15} /> Upgrade to Pro
        </button>
        <button onClick={onTour} className="w-full flex items-center gap-3 px-3 py-2.5 rounded text-salmon/80 hover:bg-card font-mono text-xs uppercase tracking-wider">
          <PlayCircle size={15} /> Demo Tour
        </button>
        <button onClick={onHelp} className="w-full flex items-center gap-3 px-3 py-2.5 rounded text-salmon/80 hover:bg-card font-mono text-xs uppercase tracking-wider">
          <HelpCircle size={15} /> Help Center
        </button>
        <button
          onClick={() => { logout(); navigate("/login"); }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded text-salmon/80 hover:bg-card font-mono text-xs uppercase tracking-wider"
        >
          <LogOut size={15} /> Sign Out / Switch
        </button>
      </div>
    </aside>
  );
}
