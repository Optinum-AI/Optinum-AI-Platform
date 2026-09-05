import { useEffect, useRef, useState } from "react";
import {
  AtSign, Briefcase, Camera, ThumbsUp, Video, Music2, MessageCircle,
  RefreshCw, Link2, Unlink, Globe, ChevronDown, ChevronUp, KeyRound,
  CheckCircle2, Circle, Send, ShieldCheck, AlertTriangle, ExternalLink,
  Lock, Check, Loader2, Monitor, Eye, EyeOff, Radio, Sparkles, TrendingUp,
  Award, ArrowRight, UserPlus
} from "lucide-react";
import { useFetch } from "../hooks/useFetch";
import { get, post, put } from "../api/client";
import type { Connection, Recommend } from "../api/types";
import Modal from "../components/ui/Modal";
import AICopilotModal from "../components/modals/AICopilotModal";

export const PLATFORMS = [
  { id: "x", label: "X (Twitter)", icon: AtSign, loginUrl: "https://x.com/login", scopes: ["Read posts", "Post on your behalf"] },
  { id: "linkedin", label: "LinkedIn", icon: Briefcase, loginUrl: "https://www.linkedin.com/login", scopes: ["Profile", "Share posts", "Read engagement"] },
  { id: "instagram", label: "Instagram", icon: Camera, loginUrl: "https://www.instagram.com/accounts/login/", scopes: ["Media upload", "Publish content"] },
  { id: "facebook", label: "Facebook", icon: ThumbsUp, loginUrl: "https://www.facebook.com/login", scopes: ["Pages", "Publish posts"] },
  { id: "youtube", label: "YouTube", icon: Video, loginUrl: "https://accounts.google.com", scopes: ["Upload videos", "Manage channel"] },
  { id: "tiktok", label: "TikTok", icon: Music2, loginUrl: "https://www.tiktok.com/login", scopes: ["Video upload", "Publish content"] },
  { id: "discord", label: "Discord", icon: MessageCircle, loginUrl: "https://discord.com/login", scopes: ["Channel webhook", "Publish messages and media"] },
];

interface Integration {
  platform: string;
  label: string;
  configured: boolean;
  client_id: string;
}

const CONSOLE_URLS: Record<string, string> = {
  google: "https://console.cloud.google.com/apis/credentials",
  x: "https://developer.x.com/en/portal/dashboard",
  linkedin: "https://www.linkedin.com/developers/apps",
  facebook: "https://developers.facebook.com/apps/",
  instagram: "https://developers.facebook.com/apps/",
  youtube: "https://console.cloud.google.com/apis/credentials",
  tiktok: "https://developers.tiktok.com/",
  discord: "https://discord.com/developers/applications",
};

function timeAgo(iso: string) {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} mins ago`;
  return `${Math.round(mins / 60)} hrs ago`;
}

export default function SocialHubPage() {
  const { data: connections, refetch } = useFetch(() => get<Connection[]>("/connections"));
  const { data: recommendations } = useFetch(() => get<Recommend>("/analytics/recommend"));
  const { data: integrationsData, refetch: refetchIntegrations } = useFetch(() =>
    get<Integration[]>("/settings/integrations")
  );

  const [consent, setConsent] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [showCopilot, setShowCopilot] = useState<boolean>(false);

  // Interactive Browser Connection State
  const [activePlatform, setActivePlatform] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<string>("initializing");
  const [sessionUrl, setSessionUrl] = useState<string>("");
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [showScreenView, setShowScreenView] = useState<boolean>(true);
  const [isCaptcha, setIsCaptcha] = useState<boolean>(false);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [detectedHandle, setDetectedHandle] = useState<string>("");
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [directHandle, setDirectHandle] = useState<string>("");
  const [showManualInput, setShowManualInput] = useState<boolean>(false);

  const [showIntegrations, setShowIntegrations] = useState(false);
  const [form, setForm] = useState<Record<string, { id: string; secret: string }>>({});
  const [savedPlatform, setSavedPlatform] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ platform: string; message: string; ok: boolean } | null>(null);

  const pollTimer = useRef<number | null>(null);

  const byPlatform = Object.fromEntries((connections ?? []).map((c) => [c.platform, c]));

  const act = async (fn: () => Promise<unknown>, key: string) => {
    setBusy(key);
    try {
      await fn();
      await refetch();
    } finally {
      setBusy(null);
    }
  };

  const startOAuthLink = async (platform: string) => {
    try {
      const { url } = await get<{ url: string }>(`/connections/${platform}/oauth/start`);
      location.href = url;
    } catch {
      setConsent(platform);
    }
  };

  // ---------------------------------------------------------------------------
  // Interactive Browser Flow: Connect -> Login -> User Approves -> Store
  // ---------------------------------------------------------------------------
  const startInteractiveBrowser = async (platform: string) => {
    setActivePlatform(platform);
    setSessionStatus("launching");
    setSessionUrl("");
    setScreenshot(null);
    setIsCaptcha(false);
    setIsLoggedIn(false);
    setDetectedHandle("");
    setApprovalError(null);
    setDirectHandle("");
    setShowManualInput(false);
    setBusy(`b_${platform}`);

    try {
      const res = await post<{ success: boolean; status: string; url: string }>(
        `/social-hub/${platform}/browser/start`
      );
      setSessionStatus(res.status || "waiting_for_user");
      setSessionUrl(res.url || "");
    } catch (err: unknown) {
      setApprovalError(err instanceof Error ? err.message : "Failed to open browser.");
      setSessionStatus("error");
    } finally {
      setBusy(null);
    }
  };

  // Poll active session status & screenshot
  useEffect(() => {
    if (!activePlatform || sessionStatus === "approved" || sessionStatus === "error") {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
        pollTimer.current = null;
      }
      return;
    }

    const poll = async () => {
      try {
        const data = await get<{
          active: boolean;
          status: string;
          is_captcha: boolean;
          is_logged_in: boolean;
          handle: string;
          url: string;
          screenshot?: string | null;
        }>(`/social-hub/${activePlatform}/browser/poll`);

        if (data.active) {
          setSessionStatus(data.status);
          setIsCaptcha(data.is_captcha);
          setIsLoggedIn(data.is_logged_in);
          if (data.handle) setDetectedHandle(data.handle);
          if (data.url) setSessionUrl(data.url);
          if (data.screenshot) setScreenshot(data.screenshot);
        } else if (sessionStatus !== "launching") {
          setSessionStatus("closed");
        }
      } catch {
        // ignore transient poll errors
      }
    };

    pollTimer.current = window.setInterval(poll, 1200);
    return () => {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
        pollTimer.current = null;
      }
    };
  }, [activePlatform, sessionStatus]);

  const handleApprove = async () => {
    if (!activePlatform) return;
    setBusy("approving");
    setApprovalError(null);
    try {
      const res = await post<{ success: boolean; handle: string }>(
        `/social-hub/${activePlatform}/browser/approve`
      );
      if (res.success) {
        setSessionStatus("approved");
        await refetch();
        setTimeout(() => {
          setActivePlatform(null);
        }, 1500);
      }
    } catch (err: unknown) {
      setApprovalError(err instanceof Error ? err.message : "Approval failed. Please ensure you are logged in.");
    } finally {
      setBusy(null);
    }
  };

  const handleDirectLink = async () => {
    if (!activePlatform || !directHandle.trim()) return;
    setBusy("linking_direct");
    setApprovalError(null);
    try {
      const res = await post<{ success: boolean; handle: string }>(
        `/social-hub/${activePlatform}/browser/import-session`,
        { handle: directHandle.trim() }
      );
      if (res.success) {
        setSessionStatus("approved");
        await refetch();
        setTimeout(() => {
          setActivePlatform(null);
        }, 1200);
      }
    } catch (err: unknown) {
      setApprovalError(err instanceof Error ? err.message : "Direct link failed.");
    } finally {
      setBusy(null);
    }
  };

  const handleCancelSession = async () => {
    if (!activePlatform) return;
    try {
      await post(`/social-hub/${activePlatform}/browser/cancel`);
    } catch {
      // ignore
    }
    setActivePlatform(null);
  };

  const disconnectBrowser = async (platform: string, connectionId: string) => {
    await post(`/social-hub/${platform}/browser/disconnect`);
    await post(`/connections/${connectionId}/disconnect`);
    await refetch();
  };

  const runTestPost = async (platform: string) => {
    setBusy(`test_${platform}`);
    setTestResult(null);
    try {
      const res = await post<{ success: boolean; post_id?: string }>(
        `/social-hub/${platform}/browser/test-post`,
        { text: `Optinum AI automated check - ${new Date().toLocaleTimeString()}` }
      );
      if (res.success) {
        setTestResult({
          platform,
          ok: true,
          message: `Post published successfully! (ID: ${res.post_id || "confirmed"})`,
        });
      }
    } catch (err: unknown) {
      setTestResult({
        platform,
        ok: false,
        message: err instanceof Error ? err.message : "Failed to publish test post.",
      });
    } finally {
      setBusy(null);
    }
  };

  const toggleConnection = async (connectionId: string, enabled: boolean) => {
    await post(`/connections/${connectionId}/toggle`, { enabled });
    await refetch();
  };

  const saveIntegration = async (platform: string) => {
    const f = form[platform];
    if (!f?.id || !f.secret) return;
    await put(`/settings/integrations/${platform}`, { client_id: f.id, client_secret: f.secret });
    setSavedPlatform(platform);
    setForm((s) => ({ ...s, [platform]: { id: "", secret: "" } }));
    await refetchIntegrations();
    await refetch();
  };

  const integrations = [...(integrationsData ?? [])];
  if (!integrations.some((it) => it.platform === "discord")) {
    integrations.push({
      platform: "discord",
      label: "Discord (channel webhook)",
      configured: false,
      client_id: "",
    });
  }

  const currentPlatformObj = PLATFORMS.find((p) => p.id === activePlatform);

  return (
    <div className="space-y-6 max-w-full overflow-x-hidden">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="micro flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            <span>DUAL-LAYER SOCIAL ENGINE</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">Social Hub Connections</h1>
          <p className="text-salmon/70 text-sm mt-1 max-w-2xl">
            Automate and coordinate all social channels with <strong>Optinum AI</strong>. Connect via <strong>Interactive Browser Worker</strong> with
            live screen view & CAPTCHA handling, or use standard API / SIM mode.
          </p>
          <div className="flex flex-wrap items-center gap-2.5 mt-3 text-[11px] text-salmon/60">
            <span className="flex items-center gap-1.5 bg-card px-2.5 py-1 rounded border border-line">
              <ShieldCheck size={13} className="text-pos" /> Zero Password Storage
            </span>
            <span className="flex items-center gap-1.5 bg-card px-2.5 py-1 rounded border border-line">
              <Globe size={13} className="text-cyan-400" /> Browser Automation Worker
            </span>
            <span className="flex items-center gap-1.5 bg-card px-2.5 py-1 rounded border border-line">
              <CheckCircle2 size={13} className="text-accent2" /> User-Controlled Authorization
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 self-start">
          <button
            className="px-3.5 py-2 rounded bg-accent/20 border border-accent hover:bg-accent/30 text-white font-mono text-xs flex items-center gap-2 transition"
            onClick={() => setShowCopilot(true)}
          >
            <Sparkles size={14} className="text-cyan-400" />
            <span>AI Copilot & Advisor</span>
          </button>
          <span className="micro border border-accent/60 text-accent2 px-3 py-2 rounded flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" /> Engine Ready
          </span>
        </div>
      </div>

      {/* AI Market & Channel Recommendation Advisor Card */}
      {recommendations && recommendations.ranking && recommendations.ranking.length > 0 && (
        <div className="card p-5 bg-gradient-to-r from-card2 via-card to-card2 border border-accent/40 rounded-xl relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-mono text-cyan-400">
                <TrendingUp size={14} />
                <span className="uppercase tracking-wider font-bold">AI Market & Channel Recommendation</span>
                <span className="text-[10px] text-salmon/50">({recommendations.provider})</span>
              </div>
              <div className="text-base font-bold text-white flex items-center gap-2">
                <Award size={18} className="text-amber-400" />
                <span>Primary Recommendation: <span className="capitalize text-accent2">{recommendations.best}</span></span>
              </div>
              <p className="text-xs text-salmon/80 max-w-2xl leading-relaxed">
                {recommendations.ranking[0]?.reason || "Highest predicted engagement and audience conversion for your product."}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {recommendations.ranking.slice(0, 3).map((r) => (
                <div
                  key={r.platform}
                  className="px-3 py-2 rounded bg-panel/90 border border-line flex items-center gap-2.5 text-xs font-mono"
                >
                  <span className="capitalize font-bold text-white">{r.platform}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-pos/10 text-pos border border-pos/30">
                    {r.score}% Match
                  </span>
                  {!byPlatform[r.platform] && (
                    <button
                      className="text-cyan-400 hover:text-white text-[11px] underline flex items-center gap-0.5"
                      onClick={() => startInteractiveBrowser(r.platform)}
                    >
                      Connect <ArrowRight size={10} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Test feedback toast */}
      {testResult && (
        <div
          className={`p-3 rounded text-xs flex items-center justify-between border ${
            testResult.ok
              ? "bg-pos/10 border-pos/40 text-pos"
              : "bg-accent/10 border-accent/40 text-accent2"
          }`}
        >
          <span className="flex items-center gap-2">
            {testResult.ok ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
            <strong>[{testResult.platform.toUpperCase()}]</strong> {testResult.message}
          </span>
          <button className="underline text-[11px] ml-4" onClick={() => setTestResult(null)}>
            Dismiss
          </button>
        </div>
      )}

      {/* Channel Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {PLATFORMS.map(({ id, label, icon: Icon }) => {
          const conn = byPlatform[id];
          const connected = conn?.status === "active";
          const isBrowser = conn?.mode === "browser";
          const isReal = conn?.mode === "real";

          return (
            <div key={id} className="card p-5 flex flex-col gap-4 relative">
              <div className="flex items-start justify-between">
                <div className="w-10 h-10 rounded bg-card2 border border-line flex items-center justify-center">
                  <Icon size={17} className="text-salmon" />
                </div>
                <span
                  className={`font-mono text-[9px] uppercase tracking-wider px-2 py-1 rounded border flex items-center gap-1.5 ${
                    connected
                      ? isBrowser
                        ? "text-cyan-400 border-cyan-400/50 bg-cyan-400/10"
                        : isReal
                        ? "text-pos border-pos/50 bg-pos/10"
                        : "text-amber-400 border-amber-400/50 bg-amber-400/10"
                      : "text-salmon/60 border-line"
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      connected
                        ? isBrowser
                          ? "bg-cyan-400"
                          : isReal
                          ? "bg-pos"
                          : "bg-amber-400"
                        : "bg-salmon/40"
                    }`}
                  />
                  {connected
                    ? isBrowser
                      ? "Browser"
                      : isReal
                      ? "Live API"
                      : "Sim"
                    : conn
                    ? "Expired"
                    : "Disconnected"}
                </span>
              </div>

              <div>
                <div className="font-bold">{label}</div>
                <div className="text-xs text-salmon/60 mt-0.5 font-mono">
                  {connected ? conn.handle : "Not connected"}
                </div>
              </div>

              <div className="border-t border-line/60 pt-3 mt-auto space-y-2.5">
                {connected ? (
                  <>
                    <div className="flex items-center justify-between font-mono text-[10px] text-salmon/60">
                      <span>Last Sync</span>
                      <span>{timeAgo(conn.last_sync_at)}</span>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-[10px] uppercase tracking-wider text-salmon/60">Enabled</span>
                      <label className="relative inline-flex cursor-pointer items-center">
                        <input
                          type="checkbox"
                          className="peer sr-only"
                          checked={conn.enabled !== false}
                          onChange={(e) => act(() => toggleConnection(conn.id, e.target.checked), `t${id}`)}
                        />
                        <span className="h-5 w-9 rounded-full border border-line bg-card2 transition peer-checked:bg-accent/90 peer-checked:border-accent" />
                        <span className="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
                      </label>
                    </div>

                    {isBrowser && (
                      <button
                        className="w-full text-xs font-mono py-1.5 px-2 bg-card2 hover:bg-card border border-line rounded flex items-center justify-center gap-1.5 text-salmon/90 transition"
                        disabled={busy === `test_${id}`}
                        onClick={() => runTestPost(id)}
                        title="Publish a sample post to verify automation"
                      >
                        <Send size={11} className="text-cyan-400" />
                        {busy === `test_${id}` ? "Posting..." : "Test Publish"}
                      </button>
                    )}

                    <div className="flex items-center gap-2">
                      <button
                        className="btn-ghost flex items-center gap-2 flex-1 justify-center text-xs py-1.5"
                        disabled={busy === `r${id}`}
                        onClick={() => act(() => post(`/connections/${conn.id}/resync`), `r${id}`)}
                      >
                        <RefreshCw size={12} /> Resync
                      </button>
                      <button
                        className="text-salmon/50 hover:text-accent2 p-2"
                        title="Disconnect"
                        onClick={() =>
                          act(
                            () =>
                              isBrowser
                                ? disconnectBrowser(id, conn.id)
                                : post(`/connections/${conn.id}/disconnect`),
                            `d${id}`
                          )
                        }
                      >
                        <Unlink size={14} />
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex justify-between font-mono text-[10px] text-salmon/60 mb-1">
                      <span>Status</span>
                      <span>Requires Auth</span>
                    </div>

                    {/* Interactive Browser Connect Button */}
                    <button
                      className="w-full py-2 px-3 rounded bg-accent/20 border border-accent hover:bg-accent/35 text-white font-mono text-xs flex items-center justify-center gap-2 transition"
                      disabled={busy === `b_${id}`}
                      onClick={() => startInteractiveBrowser(id)}
                    >
                      <Globe size={13} className="text-cyan-400" />
                      {busy === `b_${id}` ? "Launching..." : "Browser Connect"}
                    </button>

                    {/* OAuth / Sim Button */}
                    <button
                      className="btn-salmon w-full flex items-center justify-center gap-2 text-xs py-1.5"
                      onClick={() => startOAuthLink(id)}
                    >
                      <Link2 size={12} /> One-Click Link (API)
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* =========================================================================
          INTERACTIVE BROWSER CONNECTION MODAL (WITH LIVE SCREEN SHARE & DIRECT LOGIN)
         ========================================================================= */}
      {activePlatform && currentPlatformObj && (
        <Modal
          title={`Connect ${currentPlatformObj.label}`}
          micro="Interactive Browser Authentication & Authorization"
          onClose={handleCancelSession}
        >
          <div className="space-y-4 text-xs">
            {/* Quick Actions Bar */}
            <div className="flex items-center justify-between p-2.5 bg-card2 border border-line rounded-lg">
              <div className="flex items-center gap-2">
                <Globe size={14} className="text-cyan-400" />
                <span className="font-bold text-white text-[11px]">Direct Browser Login:</span>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={currentPlatformObj.loginUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 rounded bg-accent/20 border border-accent hover:bg-accent/30 text-white font-mono text-[10px] flex items-center gap-1.5 transition"
                >
                  <ExternalLink size={10} />
                  <span>Open in New Tab</span>
                </a>
                <button
                  className="px-2.5 py-1 rounded bg-panel hover:bg-card border border-line text-salmon/80 hover:text-white font-mono text-[10px] flex items-center gap-1 transition"
                  onClick={() => setShowManualInput(!showManualInput)}
                >
                  <UserPlus size={10} />
                  <span>{showManualInput ? "Use Automated" : "Direct Handle Link"}</span>
                </button>
              </div>
            </div>

            {/* Direct Handle Link Accordion */}
            {showManualInput && (
              <div className="p-3 bg-panel border border-line rounded-lg space-y-2">
                <div className="font-bold text-white text-[11px]">Instant Direct Connection</div>
                <p className="text-[10px] text-salmon/70">
                  Logged in via your browser tab? Enter your account handle below to link directly with Optinum AI:
                </p>
                <div className="flex gap-2">
                  <input
                    className="input text-xs flex-1"
                    placeholder="Account handle (e.g. @yourcompany)"
                    value={directHandle}
                    onChange={(e) => setDirectHandle(e.target.value)}
                  />
                  <button
                    className="btn-accent text-xs px-3 py-1.5 shrink-0"
                    disabled={!directHandle.trim() || busy === "linking_direct"}
                    onClick={handleDirectLink}
                  >
                    {busy === "linking_direct" ? "Linking..." : "Link Account"}
                  </button>
                </div>
              </div>
            )}

            {/* 3-Step Visual Progress Bar */}
            <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
              <div className="p-2 rounded bg-card2 border border-pos/40 text-pos flex items-center justify-center gap-1.5">
                <Check size={12} /> 1. Browser Open
              </div>
              <div
                className={`p-2 rounded border flex items-center justify-center gap-1.5 ${
                  isLoggedIn
                    ? "bg-card2 border-pos/40 text-pos"
                    : isCaptcha
                    ? "bg-amber-500/10 border-amber-500/50 text-amber-300 font-bold"
                    : "bg-accent/20 border-accent text-white"
                }`}
              >
                {isLoggedIn ? (
                  <>
                    <Check size={12} /> 2. Logged In
                  </>
                ) : isCaptcha ? (
                  <>
                    <AlertTriangle size={12} className="animate-pulse" /> 2. Security Check
                  </>
                ) : (
                  <>
                    <Loader2 size={12} className="animate-spin" /> 2. Manual Login
                  </>
                )}
              </div>
              <div
                className={`p-2 rounded border flex items-center justify-center gap-1.5 ${
                  sessionStatus === "approved"
                    ? "bg-card2 border-pos/40 text-pos"
                    : isLoggedIn
                    ? "bg-pos/20 border-pos text-pos font-bold animate-pulse"
                    : "bg-panel border-line text-salmon/40"
                }`}
              >
                {sessionStatus === "approved" ? (
                  <>
                    <Check size={12} /> 3. Authorized
                  </>
                ) : (
                  <>3. User Approval</>
                )}
              </div>
            </div>

            {/* Live Screen Share / Viewport Preview */}
            <div className="border border-line rounded-lg overflow-hidden bg-black/80">
              <div className="flex items-center justify-between px-3 py-2 bg-card2 border-b border-line text-[11px] font-mono">
                <div className="flex items-center gap-2 text-cyan-400">
                  <Monitor size={13} />
                  <span>Live Viewport Stream</span>
                  <span className="flex items-center gap-1 text-[9px] text-pos bg-pos/10 px-1.5 py-0.5 rounded border border-pos/30">
                    <Radio size={9} className="animate-pulse" /> LIVE
                  </span>
                </div>
                <button
                  className="text-salmon/70 hover:text-white flex items-center gap-1 text-[10px]"
                  onClick={() => setShowScreenView(!showScreenView)}
                >
                  {showScreenView ? <EyeOff size={12} /> : <Eye size={12} />}
                  <span>{showScreenView ? "Hide Screen" : "Show Screen"}</span>
                </button>
              </div>

              {showScreenView && (
                <div className="relative min-h-[180px] max-h-[260px] flex items-center justify-center bg-black/90 overflow-hidden">
                  {screenshot ? (
                    <img
                      src={screenshot}
                      alt="Live Browser Screen"
                      className="w-full h-auto object-contain max-h-[260px]"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center p-6 text-salmon/50 gap-2">
                      <Loader2 size={20} className="animate-spin text-cyan-400" />
                      <span className="text-[10px] font-mono">Streaming browser viewport...</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Dynamic Status Notification Box */}
            {sessionStatus === "approved" ? (
              <div className="p-3.5 bg-pos/15 border border-pos/50 rounded-lg text-pos flex items-center gap-3">
                <CheckCircle2 size={20} className="shrink-0" />
                <div>
                  <div className="font-bold text-xs">Session Authorized and Stored</div>
                  <div className="text-[10px] text-pos/80">
                    Encrypted cookies saved. Optinum AI browser worker is ready for scheduled posts.
                  </div>
                </div>
              </div>
            ) : isCaptcha ? (
              <div className="p-3.5 bg-amber-500/15 border border-amber-500/50 rounded-lg text-amber-200 space-y-1">
                <div className="flex items-center gap-2 font-bold text-xs text-amber-300">
                  <AlertTriangle size={15} />
                  <span>Security Challenge or CAPTCHA Detected</span>
                </div>
                <p className="text-[10px] text-amber-200/90 leading-relaxed">
                  Please complete the challenge directly in the browser window on your desktop. Optinum AI will detect completion automatically.
                </p>
              </div>
            ) : isLoggedIn ? (
              <div className="p-3.5 bg-pos/15 border border-pos/50 rounded-lg text-pos space-y-1">
                <div className="flex items-center gap-2 font-bold text-xs">
                  <CheckCircle2 size={15} />
                  <span>Account Authentication Detected</span>
                </div>
                <p className="text-[10px] text-pos/90 leading-relaxed">
                  Active account found{detectedHandle ? ` (${detectedHandle})` : ""}.
                  Click <strong>Approve & Store Session</strong> below to authorize Optinum AI.
                </p>
              </div>
            ) : (
              <div className="p-3.5 bg-card2 border border-line rounded-lg space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-white text-xs">
                  <Globe size={15} className="text-cyan-400" />
                  <span>Chromium Window is Active</span>
                </div>
                <p className="text-[10px] text-salmon/80 leading-relaxed">
                  Log in with your credentials in the Chromium window or in the new tab.
                  When you reach your feed, this card will turn green.
                </p>
                {sessionUrl && (
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-salmon/60 truncate pt-0.5">
                    <ExternalLink size={9} />
                    <span className="truncate">{sessionUrl}</span>
                  </div>
                )}
              </div>
            )}

            {/* Error banner if any */}
            {approvalError && (
              <div className="p-3 bg-accent/20 border border-accent rounded text-accent2 text-xs flex items-center gap-2">
                <AlertTriangle size={14} className="shrink-0" />
                <span>{approvalError}</span>
              </div>
            )}

            {/* Security Guarantee Notice */}
            <div className="p-2.5 bg-panel border border-line/60 rounded flex items-start gap-2.5 text-salmon/70 text-[10px]">
              <Lock size={13} className="text-pos shrink-0 mt-0.5" />
              <span>
                <strong>Security Guarantee:</strong> Passwords are never seen or stored.
                Only session cookies are encrypted and saved locally. Platform security policies and MFA are fully respected.
              </span>
            </div>

            {/* Action Buttons: User in full control */}
            <div className="flex items-center justify-end gap-3 pt-2 border-t border-line/60">
              <button
                className="btn-ghost text-xs"
                onClick={handleCancelSession}
                disabled={busy === "approving"}
              >
                Cancel & Close
              </button>

              <button
                className={`flex items-center gap-2 px-4 py-2 rounded font-mono text-xs transition ${
                  isLoggedIn
                    ? "bg-pos hover:bg-pos/90 text-white font-bold shadow-[0_0_15px_rgba(34,197,94,0.4)]"
                    : "btn-accent"
                }`}
                disabled={busy === "approving" || sessionStatus === "approved"}
                onClick={handleApprove}
              >
                {busy === "approving" ? (
                  <>
                    <Loader2 size={13} className="animate-spin" /> Saving...
                  </>
                ) : (
                  <>
                    <ShieldCheck size={13} /> Approve & Store Session
                  </>
                )}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Simulated OAuth Consent Modal */}
      {consent && (
        <ConsentModal
          platform={consent}
          onClose={() => setConsent(null)}
          onDone={async () => {
            await post(`/connections/${consent}/link`, {});
            setConsent(null);
            await refetch();
          }}
        />
      )}

      {/* AI Copilot Modal */}
      {showCopilot && <AICopilotModal onClose={() => setShowCopilot(false)} />}

      {/* =========================================================================
          EXPANDABLE DEVELOPER API & WEBHOOKS SETTINGS (INTEGRATIONS PANEL)
         ========================================================================= */}
      <div className="border border-line rounded-lg overflow-hidden mt-8">
        <button
          className="w-full p-4 bg-card2 hover:bg-card flex items-center justify-between text-left transition"
          onClick={() => setShowIntegrations(!showIntegrations)}
        >
          <div className="flex items-center gap-2.5 font-bold">
            <KeyRound size={16} className="text-accent2" />
            <span>Developer API Credentials & Webhooks (Optional)</span>
            <span className="text-[11px] font-normal text-salmon/60 hidden sm:inline">
              Configure official developer API keys or Discord webhooks
            </span>
          </div>
          {showIntegrations ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        {showIntegrations && (
          <div className="p-5 bg-card space-y-4">
            <p className="text-xs text-salmon/70 max-w-3xl">
              If you have registered developer apps with Meta, X, LinkedIn, Google, or TikTok, paste the credentials
              below to enable official API mode. Otherwise, use <strong>Browser Connect</strong> above for zero-config automated posting!
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {integrations.map((it) => (
                <div key={it.platform} className="card p-4 bg-panel border border-line">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-sm">
                      <KeyRound size={14} className="text-accent2" /> {it.label}
                    </div>
                    {it.configured ? (
                      <span className="font-mono text-[9px] uppercase text-pos border border-pos/50 bg-pos/10 px-2 py-0.5 rounded flex items-center gap-1">
                        <CheckCircle2 size={10} /> {it.platform === "discord" ? "Live Webhook" : "Live API"}
                      </span>
                    ) : (
                      <span className="font-mono text-[9px] uppercase text-salmon/60 border border-line px-2 py-0.5 rounded flex items-center gap-1">
                        <Circle size={10} /> Not configured
                      </span>
                    )}
                  </div>

                  <a
                    className="text-[11px] text-salmon/60 hover:text-white underline block mt-1.5 font-mono"
                    href={CONSOLE_URLS[it.platform]}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open {it.platform} developer console
                  </a>

                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <input
                      className="input text-xs"
                      type={it.platform === "discord" ? "url" : "text"}
                      placeholder={it.platform === "discord" ? "Webhook URL" : "Client ID / App ID"}
                      value={form[it.platform]?.id ?? ""}
                      onChange={(e) =>
                        setForm((s) => ({
                          ...s,
                          [it.platform]: { id: e.target.value, secret: s[it.platform]?.secret ?? "" },
                        }))
                      }
                    />
                    <input
                      className="input text-xs"
                      type="password"
                      placeholder={it.platform === "discord" ? 'Type "webhook"' : "Client Secret"}
                      value={form[it.platform]?.secret ?? ""}
                      onChange={(e) =>
                        setForm((s) => ({
                          ...s,
                          [it.platform]: { id: s[it.platform]?.id ?? "", secret: e.target.value },
                        }))
                      }
                    />
                  </div>

                  <button
                    className="btn-accent w-full mt-2.5 text-xs py-1.5"
                    disabled={!form[it.platform]?.id || !form[it.platform]?.secret}
                    onClick={() => saveIntegration(it.platform)}
                  >
                    Save API Key
                  </button>
                  {savedPlatform === it.platform && (
                    <p className="text-[10px] text-pos mt-1.5 font-mono">Saved successfully.</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ConsentModal({
  platform,
  onClose,
  onDone,
}: {
  platform: string;
  onClose: () => void;
  onDone: () => Promise<void>;
}) {
  const meta = PLATFORMS.find((p) => p.id === platform)!;
  const [busy, setBusy] = useState(false);
  return (
    <Modal title={`Authorize ${meta.label}`} micro="SIM Mode — Simulated OAuth 2.0 Consent" onClose={onClose}>
      <p className="text-xs text-salmon/70 -mt-3 mb-5">
        Optinum AI is requesting permission to manage this channel on your behalf. Dev-mode simulation — no real platform
        credentials are exchanged; official API or browser adapters plug in here.
      </p>
      <div className="card bg-card p-4 mb-6">
        <div className="micro mb-3">Requested Scopes</div>
        <ul className="space-y-2">
          {meta.scopes.map((s) => (
            <li key={s} className="text-xs text-salmon/90 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-accent" /> {s}
            </li>
          ))}
        </ul>
      </div>
      <div className="flex justify-end gap-3">
        <button className="text-salmon/70 text-sm" onClick={onClose}>
          Deny
        </button>
        <button
          className="btn-accent"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            await onDone();
          }}
        >
          {busy ? "Linking..." : "Authorize & Link"}
        </button>
      </div>
    </Modal>
  );
}
