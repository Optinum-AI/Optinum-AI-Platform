import { useState } from "react";
import { KeyRound, CheckCircle2, Circle } from "lucide-react";
import { useFetch } from "../hooks/useFetch";
import { get, put } from "../api/client";

interface Integration {
  platform: string;
  label: string;
  configured: boolean;
  client_id: string;
}

const DISCORD_INTEGRATION: Integration = {
  platform: "discord",
  label: "Discord (channel webhook)",
  configured: false,
  client_id: "",
};

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

export default function IntegrationsPage() {
  const { data, refetch } = useFetch(() => get<Integration[]>("/settings/integrations"));
  const integrations = [...(data ?? [])];
  if (!integrations.some((it) => it.platform === "discord")) {
    integrations.push(DISCORD_INTEGRATION);
  }
  const [form, setForm] = useState<Record<string, { id: string; secret: string }>>({});
  const [saved, setSaved] = useState<string | null>(null);

  const save = async (platform: string) => {
    const f = form[platform];
    if (!f?.id || !f.secret) return;
    await put(`/settings/integrations/${platform}`, { client_id: f.id, client_secret: f.secret });
    setSaved(platform);
    setForm((s) => ({ ...s, [platform]: { id: "", secret: "" } }));
    await refetch();
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="micro flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-accent" /> Real-Mode Control Panel
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold mt-2">Integrations</h1>
        <p className="text-salmon/70 text-sm mt-2 max-w-3xl">
          Paste your developer-app credentials here and the matching integration flips to LIVE instantly —
          no restarts. Create the free app in the platform console, and whitelist the redirect URI shown
          on each card. Credentials are stored only on this machine (backend/data/integrations.json, mode 600).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {integrations.map((it) => (
          <div key={it.platform} className="card p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold">
                <KeyRound size={15} className="text-accent2" /> {it.label}
              </div>
              {it.configured ? (
                <span className="font-mono text-[9px] uppercase text-pos border border-pos/50 bg-pos/10 px-2 py-1 rounded flex items-center gap-1">
                  <CheckCircle2 size={11} /> {it.platform === "discord" ? "Ready — Live webhook" : "Ready — Live OAuth"}
                </span>
              ) : (
                <span className="font-mono text-[9px] uppercase text-salmon/60 border border-line px-2 py-1 rounded flex items-center gap-1">
                  <Circle size={11} /> Not configured
                </span>
              )}
            </div>
            <a className="text-[11px] text-salmon/60 hover:text-white underline block mt-2" href={CONSOLE_URLS[it.platform]} target="_blank" rel="noreferrer">
              Open {it.platform} developer console ↗
            </a>
            <div className="micro mt-3 mb-1 text-salmon/50">
              {it.platform === "discord" ? "Discord webhook URL" : "Redirect URI to whitelist"}
            </div>
            <code className="block text-[10px] bg-panel border border-line rounded p-2 text-salmon/80 break-all">
              {it.platform === "discord"
                ? "Paste a Discord channel webhook URL in Client ID; Client Secret can be webhook"
                : it.platform === "google"
                ? "http://localhost:8000/api/auth/google/callback"
                : `http://localhost:8000/api/connections/${it.platform}/oauth/callback`}
            </code>
            <div className="grid grid-cols-2 gap-3 mt-4">
              <input
                className="input"
                type={it.platform === "discord" ? "url" : "text"}
                placeholder={it.platform === "discord" ? "Webhook URL" : "Client ID"}
                value={form[it.platform]?.id ?? ""}
                onChange={(e) => setForm((s) => ({ ...s, [it.platform]: { id: e.target.value, secret: s[it.platform]?.secret ?? "" } }))}
              />
              {it.platform === "discord" && (
                <p className="text-[10px] text-salmon/60 mt-2">
                  Paste the complete URL copied from Discord. It must start with
                  <code className="ml-1">https://discord.com/api/webhooks/</code>
                </p>
              )}
              <input
                className="input"
                type="password"
                placeholder={it.platform === "discord" ? 'Type "webhook"' : "Client Secret"}
                value={form[it.platform]?.secret ?? ""}
                onChange={(e) => setForm((s) => ({ ...s, [it.platform]: { id: s[it.platform]?.id ?? "", secret: e.target.value } }))}
              />
            </div>
            <button className="btn-accent w-full mt-3" disabled={!form[it.platform]?.id || !form[it.platform]?.secret} onClick={() => save(it.platform)}>
              Save & Enable Live Mode
            </button>
            {saved === it.platform && <p className="text-[11px] text-pos mt-2 font-mono">Saved — {it.label} is now LIVE-ready.</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
