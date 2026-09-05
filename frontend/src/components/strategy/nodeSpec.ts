export interface ParamSpec {
  kind: "enum" | "int";
  options?: string[];
  min?: number;
  max?: number;
  default: string | number;
}

export const NODE_SPEC: Record<string, Record<string, ParamSpec>> = {
  goal: {
    objective: { kind: "enum", options: ["awareness", "lead_gen", "sales", "retention"], default: "awareness" },
    horizon_weeks: { kind: "int", min: 1, max: 12, default: 4 },
  },
  audience: {
    segment: { kind: "enum", options: ["founders", "marketers", "developers", "smb_owners", "enterprise_it"], default: "marketers" },
    temperature_of_audience: { kind: "enum", options: ["cold", "warm", "hot"], default: "cold" },
  },
  content: {
    format: { kind: "enum", options: ["text_post", "thread", "short_video", "long_video", "carousel", "article"], default: "text_post" },
    tone: { kind: "enum", options: ["bold", "professional", "playful", "educational"], default: "bold" },
    cta: { kind: "enum", options: ["signup", "demo", "download", "comment"], default: "signup" },
  },
  channel: {
    platform: { kind: "enum", options: ["linkedin", "facebook", "youtube", "instagram", "tiktok", "x"], default: "linkedin" },
    priority: { kind: "int", min: 1, max: 10, default: 5 },
  },
  cadence: {
    posts_per_week: { kind: "int", min: 1, max: 14, default: 3 },
    time_of_day: { kind: "enum", options: ["morning", "noon", "evening"], default: "morning" },
    duration_weeks: { kind: "int", min: 1, max: 8, default: 4 },
  },
  experiment: {
    variant: { kind: "enum", options: ["hook", "visual", "cta"], default: "hook" },
    traffic_pct: { kind: "int", min: 5, max: 30, default: 10 },
  },
};

export const NODE_LABELS: Record<string, string> = {
  goal: "Goal",
  audience: "Audience",
  content: "Content",
  channel: "Channel",
  cadence: "Cadence",
  experiment: "Experiment",
};

export const NODE_COLORS: Record<string, string> = {
  goal: "#dc2626",
  audience: "#f59e0b",
  content: "#fca5a5",
  channel: "#22c55e",
  cadence: "#3b82f6",
  experiment: "#a855f7",
};

export function defaultParams(type: string): Record<string, string | number> {
  const spec = NODE_SPEC[type] ?? {};
  return Object.fromEntries(Object.entries(spec).map(([k, v]) => [k, v.default]));
}
