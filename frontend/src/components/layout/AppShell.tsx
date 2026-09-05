import { Outlet } from "react-router-dom";
import { useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import HelpCenterModal from "../modals/HelpCenterModal";
import UpgradeModal from "../modals/UpgradeModal";
import AICopilotModal from "../modals/AICopilotModal";
import FirstRunTour from "../FirstRunTour";

export default function AppShell() {
  const [showHelp, setShowHelp] = useState(false);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [showCopilot, setShowCopilot] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [showTour, setShowTour] = useState(() => !localStorage.getItem("optimum_tour_seen"));

  const closeTour = () => {
    localStorage.setItem("optimum_tour_seen", "1");
    setShowTour(false);
  };

  return (
    <div className="flex min-h-screen bg-ink">
      {menuOpen && (
        <div className="fixed inset-0 bg-black/60 z-30 lg:hidden" onClick={() => setMenuOpen(false)} />
      )}
      <Sidebar
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        onHelp={() => { setMenuOpen(false); setShowHelp(true); }}
        onUpgrade={() => { setMenuOpen(false); setShowUpgrade(true); }}
        onTour={() => { setMenuOpen(false); setShowTour(true); }}
      />
      <div className="flex-1 lg:ml-60 min-w-0">
        <Topbar
          onHelp={() => setShowHelp(true)}
          onMenu={() => setMenuOpen(true)}
          onOpenCopilot={() => setShowCopilot(true)}
        />
        <main className="p-4 md:p-8 md:pt-6">
          <Outlet />
        </main>
      </div>
      {showHelp && <HelpCenterModal onClose={() => setShowHelp(false)} />}
      {showUpgrade && <UpgradeModal onClose={() => setShowUpgrade(false)} />}
      {showCopilot && <AICopilotModal onClose={() => setShowCopilot(false)} />}
      {showTour && <FirstRunTour onClose={closeTour} />}
    </div>
  );
}
