"""
数据库表结构定义

表结构:
1. experiments / experiment_variants - A/B 实验配置
2. user_feedback / feedback_stats - 用户反馈
3. user_behavior - 用户行为追踪
4. orders / order_stats - 订单记录
5. user_presets - 用户客制化预设
6. carts / cart_items - 购物车
7. completed_orders / completed_order_items - 完成订单
"""

SCHEMA_SQL = """
-- ============ A/B 实验表 ============

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at REAL DEFAULT (unixepoch())
);

CREATE TABLE IF NOT EXISTS experiment_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    variant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    weight INTEGER DEFAULT 50,
    UNIQUE (experiment_id, variant_id)
);

CREATE INDEX IF NOT EXISTS idx_experiment_variants_exp ON experiment_variants(experiment_id);


-- ============ 用户反馈表 ============

CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    item_sku TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    experiment_id TEXT,
    variant TEXT,
    context TEXT,
    timestamp REAL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_feedback_user ON user_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_item ON user_feedback(item_sku);
CREATE INDEX IF NOT EXISTS idx_feedback_experiment ON user_feedback(experiment_id);

CREATE TABLE IF NOT EXISTS feedback_stats (
    item_sku TEXT PRIMARY KEY,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0
);


-- ============ 用户行为表 ============

CREATE TABLE IF NOT EXISTS user_behavior (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    action TEXT NOT NULL,
    item_sku TEXT NOT NULL,
    details TEXT,
    timestamp REAL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_behavior_user ON user_behavior(user_id);
CREATE INDEX IF NOT EXISTS idx_behavior_session ON user_behavior(session_id);


-- ============ 订单表 ============

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    item_sku TEXT NOT NULL,
    item_name TEXT,
    category TEXT,
    tags TEXT,
    base_price REAL,
    final_price REAL,
    customization TEXT,
    session_id TEXT,
    timestamp REAL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_sku ON orders(item_sku);
CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp);

CREATE TABLE IF NOT EXISTS order_stats (
    item_sku TEXT PRIMARY KEY,
    total_orders INTEGER DEFAULT 0,
    total_revenue REAL DEFAULT 0.0,
    unique_users TEXT DEFAULT '[]'
);


-- ============ 用户预设表 ============

CREATE TABLE IF NOT EXISTS user_presets (
    preset_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT DEFAULT '我的预设',
    default_temperature TEXT,
    default_cup_size TEXT,
    default_sugar_level TEXT,
    default_milk_type TEXT,
    extra_shot INTEGER DEFAULT 0,
    whipped_cream INTEGER DEFAULT 0,
    created_at REAL DEFAULT (unixepoch()),
    updated_at REAL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_presets_user ON user_presets(user_id);


-- ============ 购物车表 ============

CREATE TABLE IF NOT EXISTS carts (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    total_price REAL DEFAULT 0.0,
    total_items INTEGER DEFAULT 0,
    created_at REAL DEFAULT (unixepoch()),
    updated_at REAL DEFAULT (unixepoch())
);

CREATE TABLE IF NOT EXISTS cart_items (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES carts(session_id) ON DELETE CASCADE,
    item_sku TEXT NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    customization TEXT,
    unit_price REAL NOT NULL,
    final_price REAL NOT NULL,
    image_url TEXT,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_cart_items_session ON cart_items(session_id);


-- ============ 完成订单表 ============

CREATE TABLE IF NOT EXISTS completed_orders (
    order_id TEXT PRIMARY KEY,
    user_id TEXT,
    session_id TEXT NOT NULL,
    total_price REAL NOT NULL,
    total_items INTEGER NOT NULL,
    status TEXT DEFAULT 'CONFIRMED',
    created_at REAL DEFAULT (unixepoch()),
    completed_at REAL
);

CREATE INDEX IF NOT EXISTS idx_completed_orders_user ON completed_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_completed_orders_session ON completed_orders(session_id);

CREATE TABLE IF NOT EXISTS completed_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL REFERENCES completed_orders(order_id) ON DELETE CASCADE,
    item_sku TEXT NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    customization TEXT,
    unit_price REAL NOT NULL,
    final_price REAL NOT NULL,
    image_url TEXT,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_completed_order_items_order ON completed_order_items(order_id);


-- ============ 迁移状态表 ============

CREATE TABLE IF NOT EXISTS migration_status (
    id INTEGER PRIMARY KEY,
    migrated_at REAL DEFAULT (unixepoch()),
    source TEXT,
    status TEXT DEFAULT 'completed'
);


-- ============ 门店表 ============

CREATE TABLE IF NOT EXISTS stores (
    store_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    district TEXT,
    address TEXT,
    store_type TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    opening_hours TEXT,
    features TEXT,
    busy_hours TEXT,
    created_at REAL DEFAULT (unixepoch()),
    updated_at REAL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_stores_city ON stores(city);
CREATE INDEX IF NOT EXISTS idx_stores_type ON stores(store_type);

CREATE TABLE IF NOT EXISTS store_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id TEXT NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    item_sku TEXT NOT NULL,
    inventory_level TEXT DEFAULT 'high',
    last_updated REAL DEFAULT (unixepoch()),
    UNIQUE (store_id, item_sku)
);

CREATE INDEX IF NOT EXISTS idx_store_inventory_store ON store_inventory(store_id);


-- ============ 转化漏斗事件表 ============

CREATE TABLE IF NOT EXISTS conversion_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    item_sku TEXT,
    store_id TEXT,
    experiment_id TEXT,
    variant TEXT,
    context TEXT,
    timestamp REAL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_conversion_user ON conversion_events(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_session ON conversion_events(session_id);
CREATE INDEX IF NOT EXISTS idx_conversion_event_type ON conversion_events(event_type);
CREATE INDEX IF NOT EXISTS idx_conversion_timestamp ON conversion_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversion_experiment ON conversion_events(experiment_id);


-- ============ 上下文维度指标汇总表 ============

CREATE TABLE IF NOT EXISTS context_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    dimension_type TEXT NOT NULL,
    dimension_value TEXT NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    add_to_carts INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0,
    revenue REAL DEFAULT 0.0,
    experiment_id TEXT,
    variant TEXT,
    UNIQUE (date, dimension_type, dimension_value, experiment_id, variant)
);

CREATE INDEX IF NOT EXISTS idx_context_metrics_date ON context_metrics(date);
CREATE INDEX IF NOT EXISTS idx_context_metrics_dimension ON context_metrics(dimension_type, dimension_value);


-- ============ A/B实验结果汇总表 ============

CREATE TABLE IF NOT EXISTS experiment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL,
    variant TEXT NOT NULL,
    date TEXT NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    add_to_carts INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0,
    revenue REAL DEFAULT 0.0,
    conversion_rate REAL DEFAULT 0.0,
    UNIQUE (experiment_id, variant, date)
);

CREATE INDEX IF NOT EXISTS idx_experiment_results_exp ON experiment_results(experiment_id);
"""
