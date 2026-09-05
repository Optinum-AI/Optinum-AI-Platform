CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT DEFAULT '',
    plan TEXT DEFAULT 'free',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    logo_path TEXT,
    preset TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS connections (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    platform TEXT NOT NULL CHECK (platform IN ('linkedin','facebook','youtube','instagram','tiktok','x','discord')),
    handle TEXT NOT NULL,
    access_token TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    mode TEXT DEFAULT 'sim',
    enabled INTEGER DEFAULT 1,
    refresh_token TEXT,
    external_account_id TEXT,
    connected_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_sync_at TEXT NOT NULL,
    UNIQUE(user_id, platform)
);

CREATE TABLE IF NOT EXISTS strategies (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    graph_json TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL REFERENCES strategies(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    status TEXT DEFAULT 'running',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    logs_json TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES executions(id),
    connection_id TEXT,
    platform TEXT NOT NULL,
    content_text TEXT NOT NULL,
    asset_notes TEXT DEFAULT '',
    scheduled_at TEXT NOT NULL,
    status TEXT DEFAULT 'scheduled',
    external_id TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS metrics (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL REFERENCES posts(id),
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    resolved INTEGER DEFAULT 0,
    hour_bucket TEXT NOT NULL,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_posts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    platform TEXT NOT NULL,
    content_text TEXT NOT NULL,
    asset_path TEXT,
    status TEXT NOT NULL,
    external_id TEXT,
    error TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS competitors (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    notes TEXT DEFAULT '',
    url TEXT DEFAULT '',
    analysis_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
