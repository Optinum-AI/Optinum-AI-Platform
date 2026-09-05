export default function SplashScreen({ hiding }: { hiding: boolean }) {
  return (
    <div
      className={`fixed inset-0 z-[100] bg-ink flex flex-col items-center justify-center transition-opacity duration-500 ${
        hiding ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
    >
      <div className="splash-ring relative w-40 h-40 rounded-full flex items-center justify-center">
        <img
          src="/logo.png"
          alt="Optinum AI"
          className="w-28 h-28 object-contain splash-pulse drop-shadow-[0_0_25px_rgba(59,130,246,0.55)]"
        />
      </div>
      <h1 className="text-3xl font-extrabold mt-6 tracking-tight">Optinum AI</h1>
      <p className="micro mt-3">Optimize. Automate. Accelerate.</p>
      <div className="w-40 h-1 bg-card2 rounded mt-8 overflow-hidden">
        <div className="h-full bg-accent splash-bar" />
      </div>
      <style>{`
        .splash-ring::before {
          content: "";
          position: absolute;
          inset: 0;
          border-radius: 9999px;
          border: 3px solid #222;
          border-top-color: #dc2626;
          animation: splash-spin 1s linear infinite;
        }
        @keyframes splash-spin { to { transform: rotate(360deg); } }
        .splash-pulse { animation: splash-pulse 1.6s ease-in-out infinite; }
        @keyframes splash-pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.06); } }
        .splash-bar { width: 0%; animation: splash-bar 1.6s ease forwards; }
        @keyframes splash-bar { to { width: 100%; } }
      `}</style>
    </div>
  );
}
