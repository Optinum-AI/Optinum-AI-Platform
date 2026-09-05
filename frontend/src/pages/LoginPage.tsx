import { useEffect, useState } from "react";
import type { ReactNode, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Lock } from "lucide-react";
import { useAuth } from "../state/AuthContext";
import { get } from "../api/client";

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-ink flex flex-col items-center justify-center p-6">
      <img src="/logo.png" alt="Optinum" className="h-14 mb-6 bg-white/95 rounded p-1" />
      {children}
      <p className="micro mt-8">Optimize. Automate. Accelerate.</p>
    </div>
  );
}

export function AuthCard({
  title,
  onSubmit,
  submitLabel,
  footer,
  extra,
  onGoogle,
  googleHint,
}: {
  title: string;
  onSubmit: (email: string, password: string) => Promise<void>;
  submitLabel: string;
  footer: ReactNode;
  extra?: ReactNode;
  onGoogle?: () => void;
  googleHint?: boolean;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="card bg-card2 w-full max-w-md p-8 space-y-5">
      <h1 className="text-2xl font-bold text-center">{title}</h1>
      <button
        type="button"
        onClick={onGoogle}
        className="w-full border border-line bg-card rounded py-2.5 text-sm text-salmon hover:border-salmon/50 flex items-center justify-center gap-2 transition-colors"
      >
        <span className="font-bold text-[13px] text-[#4285F4]">G</span> Continue with Google
      </button>
      {onGoogle && googleHint && (
        <div className="rounded border border-amber-400/40 bg-amber-400/10 px-3 py-2 text-[11px] leading-relaxed text-amber-200">
          Google Sign-In needs a free OAuth client ID. Log in with email, open Integrations, paste it, and the Google button becomes active.
          <div className="mt-1">
            Don't have an account? <Link to="/signup" className="font-semibold text-amber-100 underline underline-offset-2">Request Access</Link>
          </div>
        </div>
      )}
      <div className="flex items-center gap-3 text-[10px] font-mono text-salmon/50">
        <span className="flex-1 h-px bg-line" /> OR <span className="flex-1 h-px bg-line" />
      </div>
      <div className="relative">
        <Mail size={15} className="absolute left-1 top-1/2 -translate-y-1/2 text-salmon/60" />
        <input className="input pl-8" type="email" required placeholder="executive@optinum-ai.corp" value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <div className="relative">
        <Lock size={15} className="absolute left-1 top-1/2 -translate-y-1/2 text-salmon/60" />
        <input className="input pl-8" type="password" required minLength={8} placeholder="••••••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />
      </div>
      {extra}
      {error && <p className="text-xs text-accent2 font-mono">{error}</p>}
      <button className="btn-salmon w-full py-3" disabled={busy}>
        {busy ? "Authenticating..." : submitLabel}
      </button>
      <div className="text-center text-xs text-salmon/70">{footer}</div>
    </form>
  );
}

export default function LoginPage() {
  const { login } = useAuth();
  const [googleOn, setGoogleOn] = useState(false);
  const [googleHint, setGoogleHint] = useState(false);

  useEffect(() => {
    get<{ google: boolean }>("/auth/providers")
      .then((p) => setGoogleOn(p.google))
      .catch(() => setGoogleOn(false));
  }, []);

  return (
    <AuthLayout>
      <AuthCard
        title="Welcome Back"
        submitLabel="Initialize Session"
        onSubmit={login}
        googleHint={googleHint}
        onGoogle={() => {
          if (googleOn) location.href = "/api/auth/google/start";
          else setGoogleHint(true);
        }}
        extra={
          <div className="flex items-center justify-between text-xs text-salmon/70">
            <label className="flex items-center gap-2"><input type="checkbox" defaultChecked className="accent-accent" /> Remember me</label>
            <span className="hover:text-white cursor-pointer">Forgot Password?</span>
          </div>
        }
        footer={
          <>
            Don't have an account? <Link to="/signup" className="text-accent2 font-semibold hover:underline">Request Access</Link>
          </>
        }
      />
    </AuthLayout>
  );
}
