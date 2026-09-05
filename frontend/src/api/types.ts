export interface User {
  id: string;
  email: string;
  full_name: string;
  plan: string;
}

export interface Connection {
  id: string;
  platform: string;
  handle: string;
  status: "active" | "expired";
  mode: "sim" | "real" | "browser";
  enabled?: boolean;
  connected_at: string;
  expires_at: string;
  last_sync_at: string;
}

export interface Recommend {
  ranking: { platform: string; score: number; reason: string }[];
  best: string;
  provider: string;
  has_data: boolean;
}

export interface GraphNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  params: Record<string, string | number>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
}

export interface Graph {
  version: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Strategy {
  id: string;
  product_id: string;
  graph_json: string;
  version: number;
  product?: Product;
  graph?: Graph;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  logo_path: string | null;
  preset: string | null;
}

export interface LogEntry {
  node_id: string;
  type: string;
  persona: string;
  provider: string;
  ms: number;
  excerpt: string;
}

export interface Execution {
  id: string;
  strategy_id: string;
  status: "running" | "completed" | "failed";
  started_at: string;
  finished_at: string | null;
  logs: LogEntry[];
}

export interface Post {
  id: string;
  platform: string;
  content_text: string;
  asset_notes: string;
  scheduled_at: string;
  status: string;
  impressions: number | null;
  likes: number | null;
  comments: number | null;
  shares: number | null;
}

export interface Overview {
  run_rate: string;
  run_rate_delta: string;
  resolution_rate: number;
  resolution_target: number;
  connected_channels: number;
  active_fleet: number;
  roi_pct: number;
  pipelines: { id: string; name: string; description: string; yield_usd: string; status: string; strategy_id: string }[];
}

export interface Engagement {
  volume: { hour: string; volume: number }[];
  channels: { platform: string; posts: number; impressions: number; likes: number; comments: number; shares: number }[];
  resolution_rate: number;
  total_posts: number;
  total_impressions: number;
}

export interface Competitor {
  id: string;
  name: string;
  notes: string;
  url: string;
  analysis_json: string | null;
}

export interface Billing {
  plan: string;
  tier: { label: string; price: number; agents: number; tokens: string; nodes: number };
  quotas: {
    agents: { used: number; max: number };
    tokens: { used_label: string; max: string };
    nodes: { used: number; max: number };
  };
  invoices: { id: string; date: string; amount: string; status: string }[];
}
