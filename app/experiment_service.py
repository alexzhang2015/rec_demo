"""
实验与个性化服务

功能:
1. A/B测试框架 - 支持多算法对比
2. 用户反馈收集 - 点赞/踩记录
3. 用户历史行为 - 订单/浏览/点击
4. Session实时个性化 - 动态偏好调整

数据存储: SQLite (app/data/recommendation.db)
"""
import json
import time
import hashlib
import random
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import defaultdict
from pydantic import BaseModel

from app.db.connection import get_db

# 数据存储路径（保留用于向后兼容）
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ============ 数据模型 ============

class UserFeedback(BaseModel):
    """用户反馈"""
    user_id: str
    session_id: str
    item_sku: str
    feedback_type: str  # "like" | "dislike" | "click" | "order"
    experiment_id: Optional[str] = None
    variant: Optional[str] = None
    context: Optional[dict] = None
    timestamp: Optional[float] = None


class UserBehavior(BaseModel):
    """用户行为"""
    user_id: str
    session_id: str
    action: str  # "view" | "click" | "order" | "customize"
    item_sku: str
    details: Optional[dict] = None
    timestamp: Optional[float] = None


class OrderRecord(BaseModel):
    """详细订单记录"""
    user_id: str
    item_sku: str
    item_name: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    base_price: Optional[float] = None
    final_price: Optional[float] = None
    customization: Optional[dict] = None  # {cup_size, temperature, sugar_level, milk_type, extras}
    session_id: Optional[str] = None
    timestamp: Optional[float] = None


class Experiment(BaseModel):
    """A/B实验配置"""
    experiment_id: str
    name: str
    description: str
    variants: list[dict]  # [{"id": "control", "weight": 50}, {"id": "treatment", "weight": 50}]
    status: str = "active"  # "active" | "paused" | "completed"
    created_at: Optional[float] = None


# ============ 辅助函数 ============

def _run_async(coro):
    """在同步上下文中运行异步函数"""
    try:
        loop = asyncio.get_running_loop()
        # 如果在异步上下文中，创建任务
        return asyncio.ensure_future(coro)
    except RuntimeError:
        # 没有运行中的事件循环，创建新的
        return asyncio.run(coro)


# ============ A/B测试服务 ============

class ABTestService:
    """A/B测试框架"""

    def __init__(self):
        self._experiments_cache: dict = {}
        self._initialized = False

    async def _ensure_initialized(self):
        """确保服务已初始化"""
        if self._initialized:
            return
        await self._load_experiments()
        await self._init_default_experiments()
        self._initialized = True

    async def _load_experiments(self) -> dict:
        """从数据库加载实验配置"""
        db = await get_db()

        cursor = await db.execute("SELECT * FROM experiments")
        rows = await cursor.fetchall()

        experiments = {}
        for row in rows:
            exp_id = row["experiment_id"]

            # 获取该实验的变体
            var_cursor = await db.execute(
                "SELECT variant_id, name, weight FROM experiment_variants WHERE experiment_id = ?",
                (exp_id,)
            )
            variants = await var_cursor.fetchall()

            experiments[exp_id] = {
                "experiment_id": exp_id,
                "name": row["name"],
                "description": row["description"],
                "status": row["status"],
                "created_at": row["created_at"],
                "variants": [
                    {"id": v["variant_id"], "name": v["name"], "weight": v["weight"]}
                    for v in variants
                ]
            }

        self._experiments_cache = experiments
        return experiments

    async def _save_experiment(self, exp: dict):
        """保存实验到数据库"""
        db = await get_db()

        # 插入或更新实验
        await db.execute(
            """
            INSERT OR REPLACE INTO experiments (experiment_id, name, description, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                exp["experiment_id"],
                exp["name"],
                exp.get("description", ""),
                exp.get("status", "active"),
                exp.get("created_at", time.time())
            )
        )

        # 删除旧变体
        await db.execute(
            "DELETE FROM experiment_variants WHERE experiment_id = ?",
            (exp["experiment_id"],)
        )

        # 插入新变体
        for variant in exp.get("variants", []):
            await db.execute(
                """
                INSERT INTO experiment_variants (experiment_id, variant_id, name, weight)
                VALUES (?, ?, ?, ?)
                """,
                (
                    exp["experiment_id"],
                    variant["id"],
                    variant.get("name", variant["id"]),
                    variant.get("weight", 50)
                )
            )

        await db.commit()
        self._experiments_cache[exp["experiment_id"]] = exp

    async def _init_default_experiments(self):
        """初始化默认实验"""
        default_experiments = [
            {
                "experiment_id": "rec_algorithm",
                "name": "推荐算法对比",
                "description": "对比不同推荐算法的效果",
                "variants": [
                    {"id": "embedding", "name": "Embedding语义匹配", "weight": 34},
                    {"id": "embedding_plus", "name": "Embedding+历史行为", "weight": 33},
                    {"id": "hybrid", "name": "混合推荐(Embedding+规则)", "weight": 33}
                ],
                "status": "active",
                "created_at": time.time()
            },
            {
                "experiment_id": "reason_style",
                "name": "推荐理由风格",
                "description": "测试不同推荐理由表述方式",
                "variants": [
                    {"id": "concise", "name": "简洁版", "weight": 50},
                    {"id": "detailed", "name": "详细版", "weight": 50}
                ],
                "status": "active",
                "created_at": time.time()
            },
            {
                "experiment_id": "customization_strategy",
                "name": "客制化推荐策略",
                "description": "测试不同的客制化推荐策略",
                "variants": [
                    {"id": "user_history", "name": "基于用户历史", "weight": 34},
                    {"id": "item_popular", "name": "基于商品热门配置", "weight": 33},
                    {"id": "hybrid", "name": "混合策略", "weight": 33}
                ],
                "status": "active",
                "created_at": time.time()
            },
            {
                "experiment_id": "customization_display",
                "name": "客制化展示方式",
                "description": "测试客制化建议的不同展示方式",
                "variants": [
                    {"id": "inline", "name": "内联展示", "weight": 50},
                    {"id": "expandable", "name": "可展开展示", "weight": 50}
                ],
                "status": "active",
                "created_at": time.time()
            },
            {
                "experiment_id": "context_weight",
                "name": "上下文因子权重",
                "description": "测试不同上下文因子权重对推荐效果的影响",
                "variants": [
                    {"id": "low", "name": "低权重(1.1x)", "weight": 33},
                    {"id": "medium", "name": "中权重(1.3x)", "weight": 34},
                    {"id": "high", "name": "高权重(1.5x)", "weight": 33}
                ],
                "status": "active",
                "created_at": time.time()
            },
            {
                "experiment_id": "weather_adaptation",
                "name": "天气适配策略",
                "description": "测试天气因素对推荐的影响程度",
                "variants": [
                    {"id": "none", "name": "不启用", "weight": 25},
                    {"id": "temperature_only", "name": "仅温度", "weight": 25},
                    {"id": "full", "name": "完整适配", "weight": 50}
                ],
                "status": "active",
                "created_at": time.time()
            }
        ]

        for exp in default_experiments:
            if exp["experiment_id"] not in self._experiments_cache:
                await self._save_experiment(exp)

    async def get_variant_async(self, experiment_id: str, user_id: str) -> dict:
        """
        为用户分配实验分组（异步版本）
        使用用户ID哈希确保同一用户始终进入同一分组
        """
        await self._ensure_initialized()

        exp = self._experiments_cache.get(experiment_id)
        if not exp or exp["status"] != "active":
            return {"variant": "control", "experiment_id": experiment_id}

        # 基于用户ID的确定性分组
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        cumulative = 0
        for variant in exp["variants"]:
            cumulative += variant["weight"]
            if bucket < cumulative:
                return {
                    "variant": variant["id"],
                    "variant_name": variant["name"],
                    "experiment_id": experiment_id,
                    "experiment_name": exp["name"]
                }

        return {"variant": exp["variants"][0]["id"], "experiment_id": experiment_id}

    def get_variant(self, experiment_id: str, user_id: str) -> dict:
        """为用户分配实验分组（同步版本，用于向后兼容）"""
        # 如果缓存为空，使用同步方式初始化
        if not self._experiments_cache:
            try:
                loop = asyncio.get_running_loop()
                # 在异步上下文中，直接从缓存返回或返回默认值
                exp = self._experiments_cache.get(experiment_id)
                if not exp:
                    return {"variant": "control", "experiment_id": experiment_id}
            except RuntimeError:
                # 同步上下文，运行初始化
                asyncio.run(self._ensure_initialized())

        exp = self._experiments_cache.get(experiment_id)
        if not exp or exp["status"] != "active":
            return {"variant": "control", "experiment_id": experiment_id}

        # 基于用户ID的确定性分组
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        cumulative = 0
        for variant in exp["variants"]:
            cumulative += variant["weight"]
            if bucket < cumulative:
                return {
                    "variant": variant["id"],
                    "variant_name": variant["name"],
                    "experiment_id": experiment_id,
                    "experiment_name": exp["name"]
                }

        return {"variant": exp["variants"][0]["id"], "experiment_id": experiment_id}

    async def get_all_experiments_async(self) -> list[dict]:
        """获取所有实验（异步版本）"""
        await self._ensure_initialized()
        return list(self._experiments_cache.values())

    def get_all_experiments(self) -> list[dict]:
        """获取所有实验（同步版本）"""
        return list(self._experiments_cache.values())

    async def create_experiment_async(self, exp: Experiment) -> dict:
        """创建新实验（异步版本）"""
        await self._ensure_initialized()
        exp_dict = exp.model_dump()
        exp_dict["created_at"] = time.time()
        await self._save_experiment(exp_dict)
        return exp_dict

    def create_experiment(self, exp: Experiment) -> dict:
        """创建新实验（同步版本）"""
        exp_dict = exp.model_dump()
        exp_dict["created_at"] = time.time()
        try:
            asyncio.get_running_loop()
            # 在异步上下文中，直接更新缓存
            self._experiments_cache[exp.experiment_id] = exp_dict
        except RuntimeError:
            asyncio.run(self._save_experiment(exp_dict))
        return exp_dict


# ============ 用户反馈服务 ============

class FeedbackService:
    """用户反馈收集服务"""

    def __init__(self):
        self._stats_cache: dict = {}

    async def record_feedback_async(self, feedback: UserFeedback) -> dict:
        """记录用户反馈（异步版本）"""
        db = await get_db()
        timestamp = time.time()

        context_json = json.dumps(feedback.context) if feedback.context else None

        await db.execute(
            """
            INSERT INTO user_feedback (user_id, session_id, item_sku, feedback_type, experiment_id, variant, context, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback.user_id,
                feedback.session_id,
                feedback.item_sku,
                feedback.feedback_type,
                feedback.experiment_id,
                feedback.variant,
                context_json,
                timestamp
            )
        )

        # 更新统计
        await db.execute(
            """
            INSERT INTO feedback_stats (item_sku, likes, dislikes, clicks, orders)
            VALUES (?, 0, 0, 0, 0)
            ON CONFLICT(item_sku) DO NOTHING
            """,
            (feedback.item_sku,)
        )

        if feedback.feedback_type == "like":
            await db.execute(
                "UPDATE feedback_stats SET likes = likes + 1 WHERE item_sku = ?",
                (feedback.item_sku,)
            )
        elif feedback.feedback_type == "dislike":
            await db.execute(
                "UPDATE feedback_stats SET dislikes = dislikes + 1 WHERE item_sku = ?",
                (feedback.item_sku,)
            )
        elif feedback.feedback_type == "click":
            await db.execute(
                "UPDATE feedback_stats SET clicks = clicks + 1 WHERE item_sku = ?",
                (feedback.item_sku,)
            )
        elif feedback.feedback_type == "order":
            await db.execute(
                "UPDATE feedback_stats SET orders = orders + 1 WHERE item_sku = ?",
                (feedback.item_sku,)
            )

        await db.commit()

        # 获取更新后的统计
        cursor = await db.execute(
            "SELECT * FROM feedback_stats WHERE item_sku = ?",
            (feedback.item_sku,)
        )
        row = await cursor.fetchone()
        stats = dict(row) if row else {"likes": 0, "dislikes": 0, "clicks": 0, "orders": 0}

        return {
            "status": "recorded",
            "item_stats": stats,
            "timestamp": timestamp
        }

    def record_feedback(self, feedback: UserFeedback) -> dict:
        """记录用户反馈（同步版本）"""
        try:
            asyncio.get_running_loop()
            # 在异步上下文中，返回一个协程占位符
            return {"status": "pending", "message": "Use record_feedback_async in async context"}
        except RuntimeError:
            return asyncio.run(self.record_feedback_async(feedback))

    async def get_item_stats_async(self, item_sku: str) -> dict:
        """获取商品反馈统计（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT * FROM feedback_stats WHERE item_sku = ?",
            (item_sku,)
        )
        row = await cursor.fetchone()

        if row:
            stats = {
                "likes": row["likes"],
                "dislikes": row["dislikes"],
                "clicks": row["clicks"],
                "orders": row["orders"]
            }
        else:
            stats = {"likes": 0, "dislikes": 0, "clicks": 0, "orders": 0}

        total = stats["likes"] + stats["dislikes"]
        if total > 0:
            stats["like_ratio"] = round(stats["likes"] / total, 2)
        else:
            stats["like_ratio"] = None

        return stats

    def get_item_stats(self, item_sku: str) -> dict:
        """获取商品反馈统计（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"likes": 0, "dislikes": 0, "clicks": 0, "orders": 0, "like_ratio": None}
        except RuntimeError:
            return asyncio.run(self.get_item_stats_async(item_sku))

    async def get_experiment_stats_async(self, experiment_id: str) -> dict:
        """获取实验维度的反馈统计（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            """
            SELECT variant, feedback_type, COUNT(*) as count
            FROM user_feedback
            WHERE experiment_id = ?
            GROUP BY variant, feedback_type
            """,
            (experiment_id,)
        )
        rows = await cursor.fetchall()

        variant_stats = defaultdict(lambda: {"likes": 0, "dislikes": 0, "clicks": 0, "orders": 0})

        for row in rows:
            variant = row["variant"] or "unknown"
            fb_type = row["feedback_type"]
            count = row["count"]
            if fb_type in variant_stats[variant]:
                variant_stats[variant][fb_type] = count

        # 计算转化率
        results = {}
        for variant, stats in variant_stats.items():
            total_interactions = stats["clicks"] + stats["likes"] + stats["dislikes"]
            results[variant] = {
                **stats,
                "conversion_rate": round(stats["orders"] / total_interactions, 4) if total_interactions > 0 else 0,
                "satisfaction_rate": round(stats["likes"] / (stats["likes"] + stats["dislikes"]), 4)
                    if (stats["likes"] + stats["dislikes"]) > 0 else None
            }

        return results

    def get_experiment_stats(self, experiment_id: str) -> dict:
        """获取实验维度的反馈统计（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {}
        except RuntimeError:
            return asyncio.run(self.get_experiment_stats_async(experiment_id))


# ============ 用户行为服务 ============

class BehaviorService:
    """用户历史行为服务"""

    # 时间衰减参数
    TIME_DECAY_HALFLIFE_DAYS = 30  # 半衰期30天

    def __init__(self):
        pass

    def _calculate_time_decay(self, timestamp: float) -> float:
        """计算时间衰减系数（指数衰减）"""
        days_ago = (time.time() - timestamp) / (24 * 3600)
        # 指数衰减: weight = 0.5 ^ (days / halflife)
        decay = 0.5 ** (days_ago / self.TIME_DECAY_HALFLIFE_DAYS)
        return max(decay, 0.1)  # 最低保留10%权重

    async def record_order_async(self, order: OrderRecord) -> dict:
        """记录详细订单（异步版本）"""
        db = await get_db()
        timestamp = order.timestamp or time.time()
        order_id = f"order_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        tags_json = json.dumps(order.tags) if order.tags else None
        customization_json = json.dumps(order.customization) if order.customization else None

        await db.execute(
            """
            INSERT INTO orders (order_id, user_id, item_sku, item_name, category, tags, base_price, final_price, customization, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                order.user_id,
                order.item_sku,
                order.item_name,
                order.category,
                tags_json,
                order.base_price,
                order.final_price,
                customization_json,
                order.session_id,
                timestamp
            )
        )

        # 更新统计
        sku = order.item_sku
        cursor = await db.execute(
            "SELECT unique_users FROM order_stats WHERE item_sku = ?",
            (sku,)
        )
        row = await cursor.fetchone()

        if row:
            unique_users = json.loads(row["unique_users"]) if row["unique_users"] else []
            if order.user_id not in unique_users:
                unique_users.append(order.user_id)
            await db.execute(
                """
                UPDATE order_stats
                SET total_orders = total_orders + 1,
                    total_revenue = total_revenue + ?,
                    unique_users = ?
                WHERE item_sku = ?
                """,
                (order.final_price or order.base_price or 0, json.dumps(unique_users), sku)
            )
        else:
            await db.execute(
                """
                INSERT INTO order_stats (item_sku, total_orders, total_revenue, unique_users)
                VALUES (?, 1, ?, ?)
                """,
                (sku, order.final_price or order.base_price or 0, json.dumps([order.user_id]))
            )

        await db.commit()

        # 获取用户订单数
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM orders WHERE user_id = ?",
            (order.user_id,)
        )
        row = await cursor.fetchone()
        user_total = row["count"] if row else 0

        return {
            "status": "recorded",
            "order_id": order_id,
            "user_total_orders": user_total
        }

    def record_order(self, order: OrderRecord) -> dict:
        """记录详细订单（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.record_order_async(order))

    async def batch_record_orders_async(self, orders: list[OrderRecord]) -> dict:
        """批量记录订单（异步版本）"""
        results = []
        for order in orders:
            result = await self.record_order_async(order)
            results.append(result)
        return {
            "status": "batch_recorded",
            "count": len(results),
            "results": results
        }

    def batch_record_orders(self, orders: list[OrderRecord]) -> dict:
        """批量记录订单（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.batch_record_orders_async(orders))

    async def get_user_orders_async(self, user_id: str, limit: int = 50) -> list[dict]:
        """获取用户订单历史（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            """
            SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        rows = await cursor.fetchall()

        orders = []
        for row in rows:
            order = dict(row)
            if order.get("tags"):
                order["tags"] = json.loads(order["tags"])
            if order.get("customization"):
                order["customization"] = json.loads(order["customization"])
            orders.append(order)

        return orders

    def get_user_orders(self, user_id: str, limit: int = 50) -> list[dict]:
        """获取用户订单历史（同步版本）"""
        try:
            asyncio.get_running_loop()
            return []
        except RuntimeError:
            return asyncio.run(self.get_user_orders_async(user_id, limit))

    async def record_behavior_async(self, behavior: UserBehavior) -> dict:
        """记录用户行为（异步版本）"""
        db = await get_db()

        details_json = json.dumps(behavior.details) if behavior.details else None

        await db.execute(
            """
            INSERT INTO user_behavior (user_id, session_id, action, item_sku, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                behavior.user_id,
                behavior.session_id,
                behavior.action,
                behavior.item_sku,
                details_json,
                time.time()
            )
        )

        # 如果是订单行为，同时记录到详细订单表
        if behavior.action == "order":
            details = behavior.details or {}
            order_record = OrderRecord(
                user_id=behavior.user_id,
                item_sku=behavior.item_sku,
                item_name=details.get("name"),
                category=details.get("category"),
                tags=details.get("tags"),
                base_price=details.get("base_price"),
                final_price=details.get("final_price"),
                customization=details.get("customization"),
                session_id=behavior.session_id
            )
            await self.record_order_async(order_record)

        await db.commit()
        return {"status": "recorded", "action": behavior.action}

    def record_behavior(self, behavior: UserBehavior) -> dict:
        """记录用户行为（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.record_behavior_async(behavior))

    async def get_user_profile_async(self, user_id: str) -> dict:
        """获取用户画像（异步版本）"""
        db = await get_db()
        user_orders = await self.get_user_orders_async(user_id)

        # 获取行为数据
        cursor = await db.execute(
            """
            SELECT action, COUNT(*) as count
            FROM user_behavior
            WHERE user_id = ?
            GROUP BY action
            """,
            (user_id,)
        )
        behavior_rows = await cursor.fetchall()
        behavior_counts = {row["action"]: row["count"] for row in behavior_rows}

        if not user_orders and not behavior_counts:
            return {
                "user_id": user_id,
                "is_new_user": True,
                "order_count": 0,
                "favorite_items": [],
                "category_preference": {},
                "tag_preference": {},
                "customization_preference": {}
            }

        # 使用详细订单数据统计购买频次（带时间衰减）
        sku_scores = defaultdict(float)
        category_scores = defaultdict(float)
        tag_scores = defaultdict(float)
        customization_counts = defaultdict(lambda: defaultdict(int))
        total_spend = 0

        for order in user_orders:
            decay = self._calculate_time_decay(order.get("timestamp", time.time()))

            # SKU购买加权
            sku_scores[order["item_sku"]] += decay

            # 类别偏好
            if order.get("category"):
                category_scores[order["category"]] += decay

            # 标签偏好
            for tag in (order.get("tags") or []):
                tag_scores[tag] += decay

            # 客制化偏好
            if order.get("customization"):
                for key, value in order["customization"].items():
                    customization_counts[key][str(value)] += 1

            # 消费金额
            total_spend += order.get("final_price") or order.get("base_price") or 0

        # 按加权分数排序
        favorite_items = sorted(sku_scores.items(), key=lambda x: -x[1])[:5]

        # 从点击数据补充偏好
        cursor = await db.execute(
            """
            SELECT item_sku, details, timestamp
            FROM user_behavior
            WHERE user_id = ? AND action = 'click'
            ORDER BY timestamp DESC
            LIMIT 50
            """,
            (user_id,)
        )
        click_rows = await cursor.fetchall()

        for row in click_rows:
            details = json.loads(row["details"]) if row["details"] else {}
            decay = self._calculate_time_decay(row["timestamp"])
            if "category" in details:
                category_scores[details["category"]] += decay * 0.3
            for tag in details.get("tags", []):
                tag_scores[tag] += decay * 0.3

        # 归一化客制化偏好
        customization_preference = {}
        for key, value_counts in customization_counts.items():
            total = sum(value_counts.values())
            customization_preference[key] = {
                v: round(c / total, 2) for v, c in sorted(value_counts.items(), key=lambda x: -x[1])[:3]
            }

        # 获取最后活跃时间
        cursor = await db.execute(
            "SELECT MAX(timestamp) as last_active FROM user_behavior WHERE user_id = ?",
            (user_id,)
        )
        last_active_row = await cursor.fetchone()
        last_active = last_active_row["last_active"] if last_active_row else None

        return {
            "user_id": user_id,
            "is_new_user": False,
            "order_count": len(user_orders),
            "view_count": behavior_counts.get("view", 0),
            "click_count": behavior_counts.get("click", 0),
            "total_spend": round(total_spend, 2),
            "favorite_items": [{"sku": sku, "score": round(score, 2)} for sku, score in favorite_items],
            "category_preference": dict(sorted(category_scores.items(), key=lambda x: -x[1])[:5]),
            "tag_preference": dict(sorted(tag_scores.items(), key=lambda x: -x[1])[:10]),
            "customization_preference": customization_preference,
            "last_active": last_active,
            "recent_orders": user_orders[:5]
        }

    def get_user_profile(self, user_id: str) -> dict:
        """获取用户画像（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {
                "user_id": user_id,
                "is_new_user": True,
                "order_count": 0,
                "favorite_items": [],
                "category_preference": {},
                "tag_preference": {},
                "customization_preference": {}
            }
        except RuntimeError:
            return asyncio.run(self.get_user_profile_async(user_id))

    def get_behavior_based_boost(self, user_id: str, item_sku: str, item_category: str, item_tags: list) -> float:
        """基于用户历史行为计算推荐加权（同步版本）"""
        try:
            asyncio.get_running_loop()
            return 1.0
        except RuntimeError:
            return asyncio.run(self._get_behavior_based_boost_async(user_id, item_sku, item_category, item_tags))

    async def _get_behavior_based_boost_async(self, user_id: str, item_sku: str, item_category: str, item_tags: list) -> float:
        """基于用户历史行为计算推荐加权（异步版本）"""
        user_orders = await self.get_user_orders_async(user_id)
        profile = await self.get_user_profile_async(user_id)

        if profile["is_new_user"]:
            return 1.0

        boost = 1.0

        # 1. 复购加权（带时间衰减）
        repurchase_score = 0
        for order in user_orders:
            if order["item_sku"] == item_sku:
                decay = self._calculate_time_decay(order.get("timestamp", time.time()))
                repurchase_score += decay * 0.2
        boost *= 1.0 + min(repurchase_score, 1.0)

        # 2. 类别偏好加权
        cat_pref = profile.get("category_preference", {})
        total_cat_score = sum(cat_pref.values())
        if item_category in cat_pref and total_cat_score > 0:
            cat_ratio = cat_pref[item_category] / total_cat_score
            boost *= 1.0 + (cat_ratio * 0.4)

        # 3. 标签偏好加权
        tag_pref = profile.get("tag_preference", {})
        total_tag_score = sum(tag_pref.values())
        if total_tag_score > 0:
            matched_tag_score = sum(tag_pref.get(tag, 0) for tag in item_tags)
            tag_ratio = matched_tag_score / total_tag_score
            boost *= 1.0 + (tag_ratio * 0.3)

        return min(boost, 2.5)

    async def get_order_based_recommendation_boost_async(
        self,
        user_id: str,
        item_sku: str,
        item_category: str,
        item_tags: list,
        item_price: float = None
    ) -> dict:
        """获取基于订单历史的推荐加权（异步版本）"""
        user_orders = await self.get_user_orders_async(user_id)

        if not user_orders:
            return {
                "total_boost": 1.0,
                "factors": {
                    "repurchase": 1.0,
                    "category": 1.0,
                    "tag": 1.0,
                    "price_match": 1.0
                },
                "explanation": "新用户，无历史订单数据"
            }

        factors = {}
        explanations = []

        # 1. 复购因素
        repurchase_score = 0
        repurchase_count = 0
        for order in user_orders:
            if order["item_sku"] == item_sku:
                repurchase_count += 1
                decay = self._calculate_time_decay(order.get("timestamp", time.time()))
                repurchase_score += decay * 0.25

        factors["repurchase"] = 1.0 + min(repurchase_score, 1.0)
        if repurchase_count > 0:
            explanations.append(f"曾购买{repurchase_count}次")

        # 2. 类别因素
        category_counts = defaultdict(float)
        for order in user_orders:
            if order.get("category"):
                decay = self._calculate_time_decay(order.get("timestamp", time.time()))
                category_counts[order["category"]] += decay

        total_cat = sum(category_counts.values())
        if total_cat > 0 and item_category in category_counts:
            cat_ratio = category_counts[item_category] / total_cat
            factors["category"] = 1.0 + (cat_ratio * 0.5)
            if cat_ratio > 0.3:
                explanations.append(f"偏好{item_category}类别")
        else:
            factors["category"] = 1.0

        # 3. 标签因素
        tag_scores = defaultdict(float)
        for order in user_orders:
            decay = self._calculate_time_decay(order.get("timestamp", time.time()))
            for tag in (order.get("tags") or []):
                tag_scores[tag] += decay

        total_tag = sum(tag_scores.values())
        matched_tags = [tag for tag in item_tags if tag in tag_scores]
        if total_tag > 0 and matched_tags:
            matched_score = sum(tag_scores[tag] for tag in matched_tags)
            tag_ratio = matched_score / total_tag
            factors["tag"] = 1.0 + (tag_ratio * 0.4)
            explanations.append(f"偏好标签: {', '.join(matched_tags[:2])}")
        else:
            factors["tag"] = 1.0

        # 4. 价格匹配因素
        if item_price:
            order_prices = [o.get("final_price") or o.get("base_price") for o in user_orders if o.get("final_price") or o.get("base_price")]
            if order_prices:
                avg_price = sum(order_prices) / len(order_prices)
                price_ratio = item_price / avg_price if avg_price > 0 else 1
                if 0.7 <= price_ratio <= 1.5:
                    factors["price_match"] = 1.1
                    if price_ratio > 1.2:
                        explanations.append("符合消费升级偏好")
                elif price_ratio < 0.7:
                    factors["price_match"] = 0.95
                else:
                    factors["price_match"] = 0.9
            else:
                factors["price_match"] = 1.0
        else:
            factors["price_match"] = 1.0

        total_boost = factors["repurchase"] * factors["category"] * factors["tag"] * factors["price_match"]
        total_boost = min(total_boost, 3.0)

        return {
            "total_boost": round(total_boost, 3),
            "factors": {k: round(v, 3) for k, v in factors.items()},
            "explanation": "；".join(explanations) if explanations else "综合历史订单偏好"
        }

    def get_order_based_recommendation_boost(
        self,
        user_id: str,
        item_sku: str,
        item_category: str,
        item_tags: list,
        item_price: float = None
    ) -> dict:
        """获取基于订单历史的推荐加权（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {
                "total_boost": 1.0,
                "factors": {"repurchase": 1.0, "category": 1.0, "tag": 1.0, "price_match": 1.0},
                "explanation": "新用户，无历史订单数据"
            }
        except RuntimeError:
            return asyncio.run(self.get_order_based_recommendation_boost_async(
                user_id, item_sku, item_category, item_tags, item_price
            ))

    async def get_customization_based_boost_async(
        self,
        user_id: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str]
    ) -> dict:
        """基于用户客制化偏好计算商品推荐加权（异步版本）"""
        # 中英文映射
        TEMP_MAP = {"HOT": ["热", "HOT"], "ICED": ["冰", "ICED"], "BLENDED": ["冰沙", "BLENDED"]}
        SIZE_MAP = {"TALL": ["中杯", "TALL"], "GRANDE": ["大杯", "GRANDE"], "VENTI": ["超大杯", "VENTI"]}
        MILK_MAP = {
            "WHOLE": ["全脂牛奶", "全脂奶", "WHOLE"],
            "SKIM": ["脱脂牛奶", "脱脂奶", "SKIM"],
            "OAT": ["燕麦奶", "OAT"],
            "SOY": ["豆奶", "SOY"],
            "ALMOND": ["杏仁奶", "ALMOND"],
            "COCONUT": ["椰奶", "COCONUT"]
        }
        SUGAR_MAP = {
            "NONE": ["无糖", "NONE"],
            "LIGHT": ["微糖", "少糖", "LIGHT"],
            "HALF": ["半糖", "HALF"],
            "STANDARD": ["全糖", "标准糖", "STANDARD"],
            "EXTRA": ["多糖", "EXTRA"]
        }

        def matches_preference(pref_value: str, item_values: list, mapping: dict) -> bool:
            if not item_values:
                return True
            pref_variants = mapping.get(pref_value.upper(), [pref_value])
            for variant in pref_variants:
                for item_val in item_values:
                    if variant == item_val or variant.upper() == str(item_val).upper():
                        return True
            return False

        profile = await self.get_user_profile_async(user_id)
        customization_pref = profile.get("customization_preference", {})

        # 🆕 获取用户预设，如果有预设则使用预设作为基础偏好
        user_presets = await preset_service.get_user_presets_async(user_id)
        preset_prefs = {}
        has_preset = len(user_presets) > 0

        if has_preset:
            preset = user_presets[0]
            if preset.get("default_temperature"):
                preset_prefs["temperature"] = {preset["default_temperature"]: 0.9}
            if preset.get("default_cup_size"):
                preset_prefs["cup_size"] = {preset["default_cup_size"]: 0.9}
            if preset.get("default_sugar_level"):
                preset_prefs["sugar_level"] = {preset["default_sugar_level"]: 0.9}
            if preset.get("default_milk_type"):
                preset_prefs["milk_type"] = {preset["default_milk_type"]: 0.9}

        # 合并偏好
        if not customization_pref and preset_prefs:
            customization_pref = preset_prefs

        if (profile["is_new_user"] and not has_preset) or not customization_pref:
            return {
                "total_boost": 1.0,
                "factors": {
                    "temperature_match": 1.0,
                    "size_match": 1.0,
                    "milk_match": 1.0,
                    "sugar_match": 1.0
                },
                "explanation": "新用户，无客制化偏好数据"
            }

        factors = {}
        explanations = []

        # 1. 温度偏好匹配
        temp_pref = customization_pref.get("temperature", {})
        if temp_pref and item_available_temperatures:
            preferred_temp = max(temp_pref.items(), key=lambda x: x[1])[0] if temp_pref else None
            if preferred_temp:
                if matches_preference(preferred_temp, item_available_temperatures, TEMP_MAP):
                    factors["temperature_match"] = 1.15
                    pref_ratio = temp_pref.get(preferred_temp, 0)
                    if pref_ratio > 0.6:
                        temp_display = {"HOT": "热", "ICED": "冰", "BLENDED": "冰沙"}.get(preferred_temp.upper(), preferred_temp)
                        explanations.append(f"支持您偏好的{temp_display}饮品")
                else:
                    factors["temperature_match"] = 0.9
            else:
                factors["temperature_match"] = 1.0
        else:
            factors["temperature_match"] = 1.0

        # 2. 杯型偏好匹配
        size_pref = customization_pref.get("cup_size", {})
        if size_pref and item_available_sizes:
            preferred_size = max(size_pref.items(), key=lambda x: x[1])[0] if size_pref else None
            if preferred_size:
                if matches_preference(preferred_size, item_available_sizes, SIZE_MAP):
                    factors["size_match"] = 1.1
                else:
                    factors["size_match"] = 0.95
            else:
                factors["size_match"] = 1.0
        else:
            factors["size_match"] = 1.0

        # 3. 奶类偏好匹配
        milk_pref = customization_pref.get("milk_type", {})
        if milk_pref and item_constraints:
            available_milks = item_constraints.get("available_milk_types")
            if available_milks:
                preferred_milk = max(milk_pref.items(), key=lambda x: x[1])[0] if milk_pref else None
                if preferred_milk:
                    if matches_preference(preferred_milk, available_milks, MILK_MAP):
                        factors["milk_match"] = 1.2
                        pref_ratio = milk_pref.get(preferred_milk, 0)
                        if pref_ratio > 0.5:
                            milk_name_map = {
                                "OAT": "燕麦奶", "WHOLE": "全脂奶", "SKIM": "脱脂奶",
                                "SOY": "豆奶", "COCONUT": "椰奶", "NONE": "不加奶"
                            }
                            milk_display = milk_name_map.get(preferred_milk.upper(), preferred_milk)
                            explanations.append(f"支持您常选的{milk_display}")
                    else:
                        factors["milk_match"] = 0.85
                else:
                    factors["milk_match"] = 1.0
            else:
                preferred_milk = max(milk_pref.items(), key=lambda x: x[1])[0] if milk_pref else None
                if preferred_milk and preferred_milk.upper() != "NONE":
                    factors["milk_match"] = 0.95
                else:
                    factors["milk_match"] = 1.05
        else:
            factors["milk_match"] = 1.0

        # 4. 糖度偏好匹配
        sugar_pref = customization_pref.get("sugar_level", {})
        if sugar_pref and item_constraints:
            available_sugars = item_constraints.get("available_sugar_levels")
            if available_sugars:
                preferred_sugar = max(sugar_pref.items(), key=lambda x: x[1])[0] if sugar_pref else None
                if preferred_sugar:
                    if matches_preference(preferred_sugar, available_sugars, SUGAR_MAP):
                        factors["sugar_match"] = 1.15
                        pref_ratio = sugar_pref.get(preferred_sugar, 0)
                        if pref_ratio > 0.5:
                            sugar_name_map = {
                                "STANDARD": "全糖", "LIGHT": "少糖", "HALF": "半糖",
                                "NONE": "无糖", "EXTRA": "多糖"
                            }
                            sugar_display = sugar_name_map.get(preferred_sugar.upper(), preferred_sugar)
                            explanations.append(f"可选{sugar_display}")
                    else:
                        factors["sugar_match"] = 0.9
                else:
                    factors["sugar_match"] = 1.0
            else:
                factors["sugar_match"] = 1.0
        else:
            factors["sugar_match"] = 1.0

        total_boost = (
            factors["temperature_match"] *
            factors["size_match"] *
            factors["milk_match"] *
            factors["sugar_match"]
        )
        total_boost = max(0.8, min(1.5, total_boost))

        return {
            "total_boost": round(total_boost, 3),
            "factors": {k: round(v, 3) for k, v in factors.items()},
            "explanation": "；".join(explanations) if explanations else "客制化偏好综合匹配"
        }

    def get_customization_based_boost(
        self,
        user_id: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str]
    ) -> dict:
        """基于用户客制化偏好计算商品推荐加权（同步版本）"""
        import concurrent.futures

        def run_async_in_thread():
            """在新线程中运行异步代码"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.get_customization_based_boost_async(
                        user_id, item_constraints, item_available_temperatures, item_available_sizes
                    )
                )
            finally:
                loop.close()

        try:
            asyncio.get_running_loop()
            # 有运行中的事件循环，使用线程池执行
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_in_thread)
                return future.result(timeout=10)
        except RuntimeError:
            # 没有运行中的事件循环，直接运行
            return asyncio.run(self.get_customization_based_boost_async(
                user_id, item_constraints, item_available_temperatures, item_available_sizes
            ))

    async def get_suggested_customization_for_item_async(
        self,
        user_id: str,
        item_sku: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str],
        item_base_price: float,
        weather_context: Optional[dict] = None  # 🆕 添加天气上下文参数
    ) -> dict:
        """为用户推荐特定商品的最佳客制化组合（异步版本）"""
        profile = await self.get_user_profile_async(user_id)
        customization_pref = profile.get("customization_preference", {})

        # 🆕 获取用户预设，如果有预设则使用预设作为基础偏好
        user_presets = await preset_service.get_user_presets_async(user_id)
        preset_prefs = {}
        has_preset = len(user_presets) > 0

        if has_preset:
            # 使用第一个预设作为默认偏好
            preset = user_presets[0]
            if preset.get("default_temperature"):
                preset_prefs["temperature"] = {preset["default_temperature"]: 0.9}
            if preset.get("default_cup_size"):
                preset_prefs["cup_size"] = {preset["default_cup_size"]: 0.9}
            if preset.get("default_sugar_level"):
                preset_prefs["sugar_level"] = {preset["default_sugar_level"]: 0.9}
            if preset.get("default_milk_type"):
                preset_prefs["milk_type"] = {preset["default_milk_type"]: 0.9}
            if preset.get("extra_shot"):
                preset_prefs["extra_shot"] = {"True": 0.9}
            if preset.get("whipped_cream"):
                preset_prefs["whipped_cream"] = {"True": 0.9}

        # 合并偏好：订单历史优先，预设作为补充
        merged_pref = {}
        for key in ["temperature", "cup_size", "sugar_level", "milk_type", "extra_shot", "whipped_cream"]:
            if customization_pref.get(key):
                merged_pref[key] = customization_pref[key]
            elif preset_prefs.get(key):
                merged_pref[key] = preset_prefs[key]

        # 使用合并后的偏好
        customization_pref = merged_pref if merged_pref else customization_pref

        suggested = {}
        reasons = []
        confidence_factors = []
        price_adjustment = 0.0
        used_preset = has_preset and not profile.get("customization_preference")

        # 1. 温度推荐 (🆕 考虑天气因子)
        weather_temp_boost = {}  # 天气对温度的加权
        weather_reason_text = None

        if weather_context:
            weather_temp = weather_context.get("temperature", 25)  # 实际温度
            boost_temps = weather_context.get("boost_temperatures", [])
            demote_temps = weather_context.get("demote_temperatures", [])

            # 根据天气计算温度偏好加权
            for bt in boost_temps:
                weather_temp_boost[bt.upper()] = 0.3  # 天气推荐的温度加权30%
            for dt in demote_temps:
                weather_temp_boost[dt.upper()] = -0.2  # 天气不推荐的温度减权20%

            # 生成天气原因
            if weather_temp <= 15 and "HOT" in [t.upper() for t in boost_temps]:
                weather_reason_text = f"天气{weather_temp}°C较冷推荐热饮"
            elif weather_temp >= 28 and "ICED" in [t.upper() for t in boost_temps]:
                weather_reason_text = f"天气{weather_temp}°C较热推荐冰饮"

        if item_available_temperatures:
            temp_pref = customization_pref.get("temperature", {})
            temp_values_upper = [t.upper() for t in item_available_temperatures]

            # 🆕 合并用户偏好和天气因子
            combined_temp_scores = {}
            for temp in item_available_temperatures:
                temp_upper = temp.upper()
                user_pref_score = temp_pref.get(temp, 0) + temp_pref.get(temp_upper, 0)
                weather_boost = weather_temp_boost.get(temp_upper, 0)
                combined_temp_scores[temp] = user_pref_score + weather_boost

            if combined_temp_scores:
                # 按综合得分排序
                sorted_temps = sorted(combined_temp_scores.items(), key=lambda x: -x[1])
                best_temp, best_score = sorted_temps[0]

                suggested["temperature"] = best_temp
                # 置信度基于用户偏好部分
                user_pref_score = temp_pref.get(best_temp, 0) + temp_pref.get(best_temp.upper(), 0)
                confidence_factors.append(max(user_pref_score, 0.4))

                best_temp_upper = best_temp.upper()
                temp_display = {"HOT": "热", "ICED": "冰", "WARM": "温"}.get(best_temp_upper, best_temp)

                # 添加推荐原因
                if weather_reason_text and weather_temp_boost.get(best_temp_upper, 0) > 0:
                    reasons.append(weather_reason_text)
                elif user_pref_score > 0.5:
                    reasons.append(f"您偏好{temp_display}饮")
            else:
                if item_constraints and item_constraints.get("default_temperature"):
                    suggested["temperature"] = item_constraints["default_temperature"]
                else:
                    suggested["temperature"] = item_available_temperatures[0]
                confidence_factors.append(0.3)

        # 记录天气因子影响 (用于可视化展示)
        suggested["_weather_temp_boost"] = weather_temp_boost

        # 2. 杯型推荐
        if item_available_sizes:
            size_pref = customization_pref.get("cup_size", {})
            if size_pref:
                for size, ratio in sorted(size_pref.items(), key=lambda x: -x[1]):
                    size_upper = size.upper()
                    size_values = [s.upper() for s in item_available_sizes]
                    if size_upper in size_values or size in item_available_sizes:
                        suggested["cup_size"] = size
                        confidence_factors.append(ratio)
                        if size_upper == "VENTI":
                            price_adjustment += 4
                        elif size_upper == "TALL":
                            price_adjustment -= 3
                        break
                else:
                    suggested["cup_size"] = "GRANDE"
                    confidence_factors.append(0.3)
            else:
                suggested["cup_size"] = "GRANDE"
                confidence_factors.append(0.5)

        # 3. 糖度推荐
        if item_constraints and item_constraints.get("available_sugar_levels"):
            available_sugars = item_constraints["available_sugar_levels"]
            sugar_pref = customization_pref.get("sugar_level", {})
            if sugar_pref:
                for sugar, ratio in sorted(sugar_pref.items(), key=lambda x: -x[1]):
                    sugar_upper = sugar.upper()
                    sugar_values = [s.upper() if isinstance(s, str) else s for s in available_sugars]
                    if sugar_upper in sugar_values or sugar in available_sugars:
                        suggested["sugar_level"] = sugar
                        confidence_factors.append(ratio)
                        if ratio > 0.4:
                            sugar_display = {
                                "NONE": "无糖", "LIGHT": "微糖", "HALF": "半糖",
                                "LESS": "少糖", "FULL": "全糖"
                            }.get(sugar_upper, sugar)
                            reasons.append(f"您常选{sugar_display}")
                        break
                else:
                    if item_constraints.get("default_sugar_level"):
                        suggested["sugar_level"] = item_constraints["default_sugar_level"]
                    else:
                        suggested["sugar_level"] = available_sugars[0] if available_sugars else None
                    confidence_factors.append(0.3)
            else:
                if item_constraints.get("default_sugar_level"):
                    suggested["sugar_level"] = item_constraints["default_sugar_level"]
                elif available_sugars:
                    suggested["sugar_level"] = available_sugars[0]
                confidence_factors.append(0.5)

        # 4. 奶类推荐
        if item_constraints and item_constraints.get("available_milk_types"):
            available_milks = item_constraints["available_milk_types"]
            milk_pref = customization_pref.get("milk_type", {})
            if milk_pref:
                for milk, ratio in sorted(milk_pref.items(), key=lambda x: -x[1]):
                    milk_upper = milk.upper()
                    milk_values = [m.upper() if isinstance(m, str) else m for m in available_milks]
                    if milk_upper in milk_values or milk in available_milks:
                        suggested["milk_type"] = milk
                        confidence_factors.append(ratio)
                        if milk_upper in ["OAT", "COCONUT"]:
                            price_adjustment += 3
                            if ratio > 0.4:
                                milk_display = {"OAT": "燕麦奶", "COCONUT": "椰奶"}.get(milk_upper, milk)
                                reasons.append(f"您常选{milk_display}")
                        elif ratio > 0.5:
                            milk_display = {
                                "WHOLE": "全脂奶", "SKIM": "脱脂奶", "SOY": "豆奶", "NONE": "不加奶"
                            }.get(milk_upper, milk)
                            if milk_display != "不加奶":
                                reasons.append(f"您偏好{milk_display}")
                        break
                else:
                    if item_constraints.get("default_milk_type"):
                        suggested["milk_type"] = item_constraints["default_milk_type"]
                    elif available_milks:
                        suggested["milk_type"] = available_milks[0]
                    confidence_factors.append(0.3)
            else:
                if item_constraints.get("default_milk_type"):
                    suggested["milk_type"] = item_constraints["default_milk_type"]
                elif available_milks:
                    suggested["milk_type"] = available_milks[0]
                confidence_factors.append(0.5)

        # 5. 额外选项推荐
        if item_constraints:
            if item_constraints.get("supports_espresso_adjustment"):
                extra_shot_pref = customization_pref.get("extra_shot", {})
                if extra_shot_pref.get("True", 0) > 0.3 or extra_shot_pref.get("true", 0) > 0.3:
                    suggested["extra_shot"] = True
                    price_adjustment += 4
                    reasons.append("您常选加浓缩")
                else:
                    suggested["extra_shot"] = False

            if item_constraints.get("supports_whipped_cream"):
                cream_pref = customization_pref.get("whipped_cream", {})
                if cream_pref.get("True", 0) > 0.3 or cream_pref.get("true", 0) > 0.3:
                    suggested["whipped_cream"] = True
                    reasons.append("您喜欢加奶油")
                else:
                    suggested["whipped_cream"] = False

        if confidence_factors:
            confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            confidence = 0.5

        # 🆕 如果有预设，即使是新用户也使用预设推荐
        # 确定置信度来源
        confidence_source = "history"  # 默认来源是历史偏好
        if profile["is_new_user"] and not has_preset:
            confidence = min(confidence, 0.4)
            reasons = ["推荐默认配置"]
            confidence_source = "default"
        elif used_preset and not reasons:
            preset_name = user_presets[0].get("name", "我的预设")
            reasons = [f"基于您的预设「{preset_name}」推荐"]
            # 预设置信度基于confidence_factors的平均值，但至少0.6
            confidence = max(confidence, 0.6)
            confidence_source = "preset"
        elif has_preset:
            confidence_source = "preset_history"  # 预设+历史混合

        estimated_final_price = item_base_price + price_adjustment

        # 🆕 根据来源设置推荐理由
        if reasons:
            reason_text = "；".join(reasons[:3])
        elif has_preset:
            reason_text = "基于您的预设推荐"
        else:
            reason_text = "综合您的历史偏好推荐"

        return {
            "suggested_customization": suggested,
            "confidence": round(confidence, 2),
            "confidence_source": confidence_source,  # 新增: 置信度来源
            "reason": reason_text,
            "estimated_price_adjustment": round(price_adjustment, 2),
            "estimated_final_price": round(estimated_final_price, 2)
        }

    def get_suggested_customization_for_item(
        self,
        user_id: str,
        item_sku: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str],
        item_base_price: float,
        weather_context: Optional[dict] = None  # 🆕 添加天气上下文参数
    ) -> dict:
        """为用户推荐特定商品的最佳客制化组合（同步版本）"""
        import concurrent.futures

        def run_async_in_thread():
            """在新线程中运行异步代码"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.get_suggested_customization_for_item_async(
                        user_id, item_sku, item_constraints, item_available_temperatures,
                        item_available_sizes, item_base_price, weather_context
                    )
                )
            finally:
                loop.close()

        try:
            asyncio.get_running_loop()
            # 有运行中的事件循环，使用线程池执行
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_in_thread)
                return future.result(timeout=10)
        except RuntimeError:
            # 没有运行中的事件循环，直接运行
            return asyncio.run(self.get_suggested_customization_for_item_async(
                user_id, item_sku, item_constraints, item_available_temperatures,
                item_available_sizes, item_base_price, weather_context
            ))

    async def get_order_stats_async(self) -> dict:
        """获取订单统计概览（异步版本）"""
        db = await get_db()

        cursor = await db.execute("SELECT COUNT(*) as count FROM orders")
        total_orders = (await cursor.fetchone())["count"]

        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) as count FROM orders")
        total_users = (await cursor.fetchone())["count"]

        cursor = await db.execute("""
            SELECT item_sku, total_orders, unique_users
            FROM order_stats
        """)
        rows = await cursor.fetchall()

        item_stats = {}
        for row in rows:
            unique_users = json.loads(row["unique_users"]) if row["unique_users"] else []
            item_stats[row["item_sku"]] = {
                "total_orders": row["total_orders"],
                "unique_users": len(unique_users)
            }

        return {
            "total_orders": total_orders,
            "total_users": total_users,
            "item_stats": item_stats
        }

    def get_order_stats(self) -> dict:
        """获取订单统计概览（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"total_orders": 0, "total_users": 0, "item_stats": {}}
        except RuntimeError:
            return asyncio.run(self.get_order_stats_async())


# ============ Session实时个性化 ============

class SessionService:
    """Session级别实时个性化"""

    def __init__(self):
        self.sessions: dict[str, dict] = {}

    def get_or_create_session(self, session_id: str, user_id: str = None) -> dict:
        """获取或创建session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "user_id": user_id or f"guest_{session_id[:8]}",
                "created_at": time.time(),
                "last_active": time.time(),
                "interactions": [],
                "realtime_preferences": {
                    "liked_tags": [],
                    "disliked_tags": [],
                    "viewed_categories": [],
                    "price_range": None,
                    "temperature_preference": None
                },
                "experiment_assignments": {}
            }

        session = self.sessions[session_id]
        session["last_active"] = time.time()
        return session

    def record_interaction(self, session_id: str, interaction_type: str, item_data: dict) -> dict:
        """记录session内交互，实时更新偏好"""
        session = self.get_or_create_session(session_id)

        interaction = {
            "type": interaction_type,
            "item": item_data,
            "timestamp": time.time()
        }
        session["interactions"].append(interaction)
        session["interactions"] = session["interactions"][-50:]

        prefs = session["realtime_preferences"]

        if interaction_type == "like":
            for tag in item_data.get("tags", []):
                if tag not in prefs["liked_tags"]:
                    prefs["liked_tags"].append(tag)

        elif interaction_type == "dislike":
            for tag in item_data.get("tags", []):
                if tag not in prefs["disliked_tags"]:
                    prefs["disliked_tags"].append(tag)
                if tag in prefs["liked_tags"]:
                    prefs["liked_tags"].remove(tag)

        elif interaction_type in ["view", "click"]:
            category = item_data.get("category")
            if category and category not in prefs["viewed_categories"]:
                prefs["viewed_categories"].append(category)

            price = item_data.get("price")
            if price:
                if prefs["price_range"] is None:
                    prefs["price_range"] = {"min": price, "max": price, "avg": price, "count": 1}
                else:
                    pr = prefs["price_range"]
                    pr["min"] = min(pr["min"], price)
                    pr["max"] = max(pr["max"], price)
                    pr["avg"] = (pr["avg"] * pr["count"] + price) / (pr["count"] + 1)
                    pr["count"] += 1

        return {
            "recorded": True,
            "current_preferences": prefs
        }

    def get_session_boost(self, session_id: str, item_tags: list, item_category: str, item_price: float) -> float:
        """基于session实时偏好计算推荐加权"""
        session = self.sessions.get(session_id)
        if not session:
            return 1.0

        prefs = session["realtime_preferences"]
        boost = 1.0

        liked_match = sum(1 for tag in item_tags if tag in prefs["liked_tags"])
        boost *= 1.0 + (liked_match * 0.15)

        disliked_match = sum(1 for tag in item_tags if tag in prefs["disliked_tags"])
        boost *= max(0.3, 1.0 - (disliked_match * 0.3))

        if item_category in prefs["viewed_categories"]:
            boost *= 1.1

        if prefs["price_range"] and prefs["price_range"]["count"] >= 3:
            pr = prefs["price_range"]
            if pr["min"] <= item_price <= pr["max"]:
                boost *= 1.05

        return min(boost, 2.5)

    def get_session_info(self, session_id: str) -> dict:
        """获取session信息"""
        session = self.sessions.get(session_id)
        if not session:
            return {"exists": False}

        return {
            "exists": True,
            "session_id": session_id,
            "user_id": session["user_id"],
            "interaction_count": len(session["interactions"]),
            "duration_seconds": int(time.time() - session["created_at"]),
            "realtime_preferences": session["realtime_preferences"]
        }

    def cleanup_expired_sessions(self, max_age_seconds: int = 3600):
        """清理过期session"""
        now = time.time()
        expired = [
            sid for sid, s in self.sessions.items()
            if now - s["last_active"] > max_age_seconds
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)


# ============ 解释性增强服务 ============

class ExplainabilityService:
    """推荐解释性增强"""

    def generate_detailed_explanation(
        self,
        item: dict,
        user_profile: dict,
        match_score: float,
        session_boost: float,
        behavior_boost: float,
        embedding_similarity: float,
        matched_keywords: list[str],
        experiment_info: dict = None
    ) -> dict:
        """生成详细的推荐解释"""

        factors = []

        if embedding_similarity > 0.7:
            factors.append({
                "type": "semantic",
                "label": "语义高度匹配",
                "score": round(embedding_similarity, 2),
                "description": f"与您的偏好「{user_profile.get('search_query', '')[:20]}...」高度相关",
                "weight": 0.4
            })
        elif embedding_similarity > 0.5:
            factors.append({
                "type": "semantic",
                "label": "语义较为匹配",
                "score": round(embedding_similarity, 2),
                "description": "符合您的口味偏好",
                "weight": 0.3
            })

        if matched_keywords:
            factors.append({
                "type": "keyword",
                "label": "偏好关键词匹配",
                "matched": matched_keywords[:3],
                "description": f"匹配了您偏好的「{'、'.join(matched_keywords[:3])}」",
                "weight": 0.2
            })

        if behavior_boost > 1.1:
            factors.append({
                "type": "history",
                "label": "历史偏好加成",
                "boost": round(behavior_boost, 2),
                "description": "基于您的购买和浏览历史",
                "weight": 0.2
            })

        if session_boost > 1.1:
            factors.append({
                "type": "realtime",
                "label": "实时偏好加成",
                "boost": round(session_boost, 2),
                "description": "根据本次浏览偏好调整",
                "weight": 0.15
            })
        elif session_boost < 0.9:
            factors.append({
                "type": "realtime",
                "label": "实时偏好降权",
                "boost": round(session_boost, 2),
                "description": "与本次浏览偏好不太匹配",
                "weight": -0.1
            })

        if item.get("is_new"):
            factors.append({
                "type": "feature",
                "label": "新品推荐",
                "description": "最新上市商品",
                "weight": 0.1
            })

        if item.get("is_seasonal"):
            factors.append({
                "type": "feature",
                "label": "季节限定",
                "description": "当季特色商品",
                "weight": 0.1
            })

        total_weight = sum(abs(f.get("weight", 0)) for f in factors)
        for factor in factors:
            if total_weight > 0:
                factor["contribution"] = round(abs(factor.get("weight", 0)) / total_weight * 100, 1)

        primary_reason = factors[0] if factors else {"label": "综合推荐"}

        return {
            "summary": f"基于{primary_reason['label']}为您推荐",
            "match_score": round(match_score, 4),
            "score_breakdown": {
                "base_embedding_score": round(embedding_similarity, 4),
                "behavior_multiplier": round(behavior_boost, 2),
                "session_multiplier": round(session_boost, 2),
                "final_score": round(match_score, 4)
            },
            "factors": factors,
            "experiment": experiment_info,
            "confidence": "high" if match_score > 0.7 else "medium" if match_score > 0.5 else "low"
        }


# ============ 预设服务 ============

class PresetService:
    """用户客制化预设服务"""

    def __init__(self):
        pass

    async def create_preset_async(self, preset: dict) -> dict:
        """创建用户预设（异步版本）"""
        user_id = preset.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}

        db = await get_db()
        preset_id = f"preset_{user_id}_{int(time.time() * 1000)}"
        now = time.time()

        await db.execute(
            """
            INSERT INTO user_presets (preset_id, user_id, name, default_temperature, default_cup_size, default_sugar_level, default_milk_type, extra_shot, whipped_cream, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                preset_id,
                user_id,
                preset.get("name", "我的预设"),
                preset.get("default_temperature"),
                preset.get("default_cup_size"),
                preset.get("default_sugar_level"),
                preset.get("default_milk_type"),
                1 if preset.get("extra_shot") else 0,
                1 if preset.get("whipped_cream") else 0,
                now,
                now
            )
        )
        await db.commit()

        preset_data = {
            "preset_id": preset_id,
            "user_id": user_id,
            "name": preset.get("name", "我的预设"),
            "default_temperature": preset.get("default_temperature"),
            "default_cup_size": preset.get("default_cup_size"),
            "default_sugar_level": preset.get("default_sugar_level"),
            "default_milk_type": preset.get("default_milk_type"),
            "extra_shot": preset.get("extra_shot", False),
            "whipped_cream": preset.get("whipped_cream", False),
            "created_at": now,
            "updated_at": now
        }

        return {
            "status": "created",
            "preset": preset_data
        }

    def create_preset(self, preset: dict) -> dict:
        """创建用户预设（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.create_preset_async(preset))

    async def get_user_presets_async(self, user_id: str) -> list[dict]:
        """获取用户的所有预设（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT * FROM user_presets WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()

        return [
            {
                "preset_id": row["preset_id"],
                "user_id": row["user_id"],
                "name": row["name"],
                "default_temperature": row["default_temperature"],
                "default_cup_size": row["default_cup_size"],
                "default_sugar_level": row["default_sugar_level"],
                "default_milk_type": row["default_milk_type"],
                "extra_shot": bool(row["extra_shot"]),
                "whipped_cream": bool(row["whipped_cream"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]

    def get_user_presets(self, user_id: str) -> list[dict]:
        """获取用户的所有预设（同步版本）"""
        try:
            asyncio.get_running_loop()
            return []
        except RuntimeError:
            return asyncio.run(self.get_user_presets_async(user_id))

    async def get_preset_async(self, preset_id: str) -> Optional[dict]:
        """获取单个预设（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT * FROM user_presets WHERE preset_id = ?",
            (preset_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return {
            "preset_id": row["preset_id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "default_temperature": row["default_temperature"],
            "default_cup_size": row["default_cup_size"],
            "default_sugar_level": row["default_sugar_level"],
            "default_milk_type": row["default_milk_type"],
            "extra_shot": bool(row["extra_shot"]),
            "whipped_cream": bool(row["whipped_cream"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    def get_preset(self, preset_id: str) -> Optional[dict]:
        """获取单个预设（同步版本）"""
        try:
            asyncio.get_running_loop()
            return None
        except RuntimeError:
            return asyncio.run(self.get_preset_async(preset_id))

    async def update_preset_async(self, preset_id: str, updates: dict) -> dict:
        """更新预设（异步版本）"""
        db = await get_db()

        # 检查预设是否存在
        cursor = await db.execute(
            "SELECT 1 FROM user_presets WHERE preset_id = ?",
            (preset_id,)
        )
        if not await cursor.fetchone():
            return {"status": "error", "message": "preset not found"}

        allowed_fields = [
            "name", "default_temperature", "default_cup_size",
            "default_sugar_level", "default_milk_type",
            "extra_shot", "whipped_cream"
        ]

        set_clauses = []
        values = []
        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"{field} = ?")
                val = updates[field]
                if field in ["extra_shot", "whipped_cream"]:
                    val = 1 if val else 0
                values.append(val)

        if set_clauses:
            set_clauses.append("updated_at = ?")
            values.append(time.time())
            values.append(preset_id)

            await db.execute(
                f"UPDATE user_presets SET {', '.join(set_clauses)} WHERE preset_id = ?",
                values
            )
            await db.commit()

        preset = await self.get_preset_async(preset_id)
        return {"status": "updated", "preset": preset}

    def update_preset(self, preset_id: str, updates: dict) -> dict:
        """更新预设（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.update_preset_async(preset_id, updates))

    async def delete_preset_async(self, preset_id: str) -> dict:
        """删除预设（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT 1 FROM user_presets WHERE preset_id = ?",
            (preset_id,)
        )
        if not await cursor.fetchone():
            return {"status": "error", "message": "preset not found"}

        await db.execute(
            "DELETE FROM user_presets WHERE preset_id = ?",
            (preset_id,)
        )
        await db.commit()

        return {"status": "deleted", "preset_id": preset_id}

    def delete_preset(self, preset_id: str) -> dict:
        """删除预设（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.delete_preset_async(preset_id))

    def apply_preset_to_item(
        self,
        preset_id: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str],
        item_base_price: float
    ) -> dict:
        """将预设应用到商品（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "error", "message": "Use async version"}
        except RuntimeError:
            return asyncio.run(self.apply_preset_to_item_async(
                preset_id, item_constraints, item_available_temperatures,
                item_available_sizes, item_base_price
            ))

    async def apply_preset_to_item_async(
        self,
        preset_id: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str],
        item_base_price: float
    ) -> dict:
        """将预设应用到商品（异步版本）"""
        preset = await self.get_preset_async(preset_id)
        if not preset:
            return {"status": "error", "message": "preset not found"}

        applied = {}
        conflicts = []
        price_adjustment = 0.0

        # 温度
        if preset.get("default_temperature"):
            temp = preset["default_temperature"]
            temp_values = [t.upper() for t in item_available_temperatures]
            if temp.upper() in temp_values or temp in item_available_temperatures:
                applied["temperature"] = temp
            else:
                conflicts.append({
                    "field": "temperature",
                    "preset_value": temp,
                    "available": item_available_temperatures,
                    "applied": item_available_temperatures[0] if item_available_temperatures else None
                })
                applied["temperature"] = item_available_temperatures[0] if item_available_temperatures else None

        # 杯型
        if preset.get("default_cup_size"):
            size = preset["default_cup_size"]
            size_values = [s.upper() for s in item_available_sizes]
            if size.upper() in size_values or size in item_available_sizes:
                applied["cup_size"] = size
                if size.upper() == "VENTI":
                    price_adjustment += 4
                elif size.upper() == "TALL":
                    price_adjustment -= 3
            else:
                conflicts.append({
                    "field": "cup_size",
                    "preset_value": size,
                    "available": item_available_sizes,
                    "applied": "GRANDE"
                })
                applied["cup_size"] = "GRANDE"

        # 糖度
        if preset.get("default_sugar_level") and item_constraints:
            sugar = preset["default_sugar_level"]
            available_sugars = item_constraints.get("available_sugar_levels", [])
            if available_sugars:
                sugar_values = [s.upper() if isinstance(s, str) else s for s in available_sugars]
                if sugar.upper() in sugar_values or sugar in available_sugars:
                    applied["sugar_level"] = sugar
                else:
                    conflicts.append({
                        "field": "sugar_level",
                        "preset_value": sugar,
                        "available": available_sugars,
                        "applied": available_sugars[0] if available_sugars else None
                    })
                    applied["sugar_level"] = available_sugars[0] if available_sugars else None

        # 奶类
        if preset.get("default_milk_type") and item_constraints:
            milk = preset["default_milk_type"]
            available_milks = item_constraints.get("available_milk_types", [])
            if available_milks:
                milk_values = [m.upper() if isinstance(m, str) else m for m in available_milks]
                if milk.upper() in milk_values or milk in available_milks:
                    applied["milk_type"] = milk
                    if milk.upper() in ["OAT", "COCONUT"]:
                        price_adjustment += 3
                else:
                    conflicts.append({
                        "field": "milk_type",
                        "preset_value": milk,
                        "available": available_milks,
                        "applied": available_milks[0] if available_milks else None
                    })
                    applied["milk_type"] = available_milks[0] if available_milks else None

        # 加浓缩
        if preset.get("extra_shot") and item_constraints:
            if item_constraints.get("supports_espresso_adjustment"):
                applied["extra_shot"] = True
                price_adjustment += 4
            else:
                conflicts.append({
                    "field": "extra_shot",
                    "preset_value": True,
                    "reason": "商品不支持加浓缩",
                    "applied": False
                })
                applied["extra_shot"] = False

        # 奶油
        if preset.get("whipped_cream") and item_constraints:
            if item_constraints.get("supports_whipped_cream"):
                applied["whipped_cream"] = True
            else:
                conflicts.append({
                    "field": "whipped_cream",
                    "preset_value": True,
                    "reason": "商品不支持奶油顶",
                    "applied": False
                })
                applied["whipped_cream"] = False

        return {
            "status": "applied",
            "preset_name": preset.get("name"),
            "applied_customization": applied,
            "conflicts": conflicts,
            "has_conflicts": len(conflicts) > 0,
            "estimated_price_adjustment": round(price_adjustment, 2),
            "estimated_final_price": round(item_base_price + price_adjustment, 2)
        }


# ============ 转化漏斗服务 ============

class ConversionFunnelService:
    """转化漏斗追踪服务"""

    # 漏斗事件类型
    EVENT_TYPES = ["impression", "click", "add_to_cart", "order", "reorder"]

    def __init__(self):
        self._metrics_cache: dict = {}

    async def record_event_async(
        self,
        user_id: str,
        session_id: str,
        event_type: str,
        item_sku: str = None,
        store_id: str = None,
        experiment_id: str = None,
        variant: str = None,
        context: dict = None
    ) -> dict:
        """记录转化漏斗事件"""
        if event_type not in self.EVENT_TYPES:
            return {"status": "error", "message": f"Invalid event type: {event_type}"}

        db = await get_db()

        await db.execute(
            """
            INSERT INTO conversion_events
            (user_id, session_id, event_type, item_sku, store_id, experiment_id, variant, context, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                event_type,
                item_sku,
                store_id,
                experiment_id,
                variant,
                json.dumps(context) if context else None,
                time.time()
            )
        )

        # 更新上下文维度指标
        if context:
            await self._update_context_metrics(event_type, context, experiment_id, variant)

        await db.commit()

        return {
            "status": "recorded",
            "event_type": event_type,
            "user_id": user_id,
            "session_id": session_id
        }

    def record_event(self, *args, **kwargs) -> dict:
        """同步版本"""
        return _run_async(self.record_event_async(*args, **kwargs))

    async def _update_context_metrics(
        self,
        event_type: str,
        context: dict,
        experiment_id: str = None,
        variant: str = None
    ):
        """更新上下文维度指标汇总"""
        db = await get_db()
        today = datetime.now().strftime("%Y-%m-%d")

        # 需要追踪的维度
        dimensions = [
            ("time_of_day", context.get("time_of_day")),
            ("weather", context.get("weather", {}).get("weather_type") if isinstance(context.get("weather"), dict) else context.get("weather")),
            ("store_type", context.get("store_type")),
            ("day_type", context.get("day_type")),
            ("season", context.get("season")),
            ("scenario", context.get("active_scenario_id"))
        ]

        # 事件类型到字段映射
        event_field_map = {
            "impression": "impressions",
            "click": "clicks",
            "add_to_cart": "add_to_carts",
            "order": "orders"
        }

        field = event_field_map.get(event_type)
        if not field:
            return

        for dim_type, dim_value in dimensions:
            if dim_value:
                # 使用 UPSERT 语法
                await db.execute(
                    f"""
                    INSERT INTO context_metrics
                    (date, dimension_type, dimension_value, {field}, experiment_id, variant)
                    VALUES (?, ?, ?, 1, ?, ?)
                    ON CONFLICT(date, dimension_type, dimension_value, experiment_id, variant)
                    DO UPDATE SET {field} = {field} + 1
                    """,
                    (today, dim_type, dim_value, experiment_id or "", variant or "")
                )

    async def get_funnel_stats_async(
        self,
        start_date: str = None,
        end_date: str = None,
        experiment_id: str = None,
        variant: str = None
    ) -> dict:
        """获取漏斗统计数据"""
        db = await get_db()

        where_clauses = []
        params = []

        if start_date:
            where_clauses.append("timestamp >= ?")
            params.append(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        if end_date:
            where_clauses.append("timestamp <= ?")
            params.append(datetime.strptime(end_date, "%Y-%m-%d").timestamp() + 86400)
        if experiment_id:
            where_clauses.append("experiment_id = ?")
            params.append(experiment_id)
        if variant:
            where_clauses.append("variant = ?")
            params.append(variant)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # 获取各阶段统计
        cursor = await db.execute(
            f"""
            SELECT event_type, COUNT(*) as count, COUNT(DISTINCT user_id) as unique_users
            FROM conversion_events
            WHERE {where_sql}
            GROUP BY event_type
            """,
            params
        )
        rows = await cursor.fetchall()

        stats = {event: {"count": 0, "unique_users": 0} for event in self.EVENT_TYPES}
        for row in rows:
            stats[row["event_type"]] = {
                "count": row["count"],
                "unique_users": row["unique_users"]
            }

        # 计算转化率
        impressions = stats["impression"]["count"]
        clicks = stats["click"]["count"]
        add_to_carts = stats["add_to_cart"]["count"]
        orders = stats["order"]["count"]

        funnel = {
            "impression": {
                **stats["impression"],
                "rate": 1.0
            },
            "click": {
                **stats["click"],
                "rate": round(clicks / impressions, 4) if impressions > 0 else 0
            },
            "add_to_cart": {
                **stats["add_to_cart"],
                "rate": round(add_to_carts / clicks, 4) if clicks > 0 else 0
            },
            "order": {
                **stats["order"],
                "rate": round(orders / add_to_carts, 4) if add_to_carts > 0 else 0
            }
        }

        overall_conversion = round(orders / impressions, 4) if impressions > 0 else 0

        return {
            "funnel": funnel,
            "overall_conversion_rate": overall_conversion,
            "total_impressions": impressions,
            "total_orders": orders
        }

    def get_funnel_stats(self, *args, **kwargs) -> dict:
        """同步版本"""
        return _run_async(self.get_funnel_stats_async(*args, **kwargs))

    async def get_context_metrics_async(
        self,
        dimension_type: str,
        start_date: str = None,
        end_date: str = None
    ) -> dict:
        """获取上下文维度统计"""
        db = await get_db()

        where_clauses = ["dimension_type = ?"]
        params = [dimension_type]

        if start_date:
            where_clauses.append("date >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("date <= ?")
            params.append(end_date)

        where_sql = " AND ".join(where_clauses)

        cursor = await db.execute(
            f"""
            SELECT dimension_value,
                   SUM(impressions) as impressions,
                   SUM(clicks) as clicks,
                   SUM(add_to_carts) as add_to_carts,
                   SUM(orders) as orders,
                   SUM(revenue) as revenue
            FROM context_metrics
            WHERE {where_sql}
            GROUP BY dimension_value
            ORDER BY SUM(orders) DESC
            """,
            params
        )
        rows = await cursor.fetchall()

        metrics = []
        for row in rows:
            impressions = row["impressions"] or 0
            orders = row["orders"] or 0
            conversion_rate = round(orders / impressions, 4) if impressions > 0 else 0

            metrics.append({
                "dimension_value": row["dimension_value"],
                "impressions": impressions,
                "clicks": row["clicks"] or 0,
                "add_to_carts": row["add_to_carts"] or 0,
                "orders": orders,
                "revenue": row["revenue"] or 0,
                "conversion_rate": conversion_rate
            })

        return {
            "dimension_type": dimension_type,
            "metrics": metrics
        }

    def get_context_metrics(self, *args, **kwargs) -> dict:
        """同步版本"""
        return _run_async(self.get_context_metrics_async(*args, **kwargs))

    async def get_ab_analysis_async(self, experiment_id: str) -> dict:
        """获取A/B实验分析结果"""
        db = await get_db()

        # 获取各变体的统计数据
        cursor = await db.execute(
            """
            SELECT variant,
                   COUNT(*) as total_events,
                   SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END) as impressions,
                   SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as clicks,
                   SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as add_to_carts,
                   SUM(CASE WHEN event_type = 'order' THEN 1 ELSE 0 END) as orders
            FROM conversion_events
            WHERE experiment_id = ?
            GROUP BY variant
            """,
            (experiment_id,)
        )
        rows = await cursor.fetchall()

        if not rows:
            return {
                "experiment_id": experiment_id,
                "status": "no_data",
                "variants": [],
                "winner": None
            }

        variants = []
        for row in rows:
            impressions = row["impressions"] or 0
            orders = row["orders"] or 0
            conversion_rate = round(orders / impressions, 4) if impressions > 0 else 0

            variants.append({
                "variant": row["variant"],
                "impressions": impressions,
                "clicks": row["clicks"] or 0,
                "add_to_carts": row["add_to_carts"] or 0,
                "orders": orders,
                "conversion_rate": conversion_rate
            })

        # 找出最佳变体
        variants.sort(key=lambda x: x["conversion_rate"], reverse=True)
        winner = variants[0] if variants else None
        baseline = variants[-1] if len(variants) > 1 else None

        # 计算提升
        lift = 0
        if baseline and baseline["conversion_rate"] > 0:
            lift = round(
                (winner["conversion_rate"] - baseline["conversion_rate"]) / baseline["conversion_rate"],
                4
            )

        # 模拟置信度计算（实际应使用卡方检验或贝叶斯方法）
        total_samples = sum(v["impressions"] for v in variants)
        confidence = min(0.99, 0.5 + (total_samples / 10000) * 0.4) if total_samples > 100 else 0.5
        p_value = max(0.01, 1 - confidence)

        return {
            "experiment_id": experiment_id,
            "status": "active",
            "variants": variants,
            "winner": winner["variant"] if winner else None,
            "lift": lift,
            "confidence": round(confidence, 2),
            "p_value": round(p_value, 3),
            "total_samples": total_samples,
            "is_significant": confidence >= 0.95
        }

    def get_ab_analysis(self, experiment_id: str) -> dict:
        """同步版本"""
        return _run_async(self.get_ab_analysis_async(experiment_id))

    async def simulate_data_async(
        self,
        days: int = 7,
        events_per_day: int = 100
    ) -> dict:
        """模拟转化漏斗数据（用于演示）"""
        import random
        from datetime import timedelta

        db = await get_db()
        now = datetime.now()

        time_of_days = ["morning", "lunch", "afternoon", "evening", "night"]
        weather_types = ["hot", "rainy", "cold", "sunny", "cloudy"]
        store_types = ["mall", "office", "station", "university"]
        scenarios = ["office_morning_rush", "weekend_leisure", "student_study", "travel_rush"]
        experiments = ["context_weight", "weather_adaptation"]
        variants_map = {
            "context_weight": ["low", "medium", "high"],
            "weather_adaptation": ["none", "temperature_only", "full"]
        }

        total_events = 0

        for day_offset in range(days):
            event_date = now - timedelta(days=day_offset)

            for _ in range(events_per_day):
                user_id = f"user_{random.randint(1000, 9999)}"
                session_id = f"session_{random.randint(10000, 99999)}"

                # 随机上下文
                context = {
                    "time_of_day": random.choice(time_of_days),
                    "weather": {"weather_type": random.choice(weather_types)},
                    "store_type": random.choice(store_types),
                    "day_type": "weekend" if event_date.weekday() >= 5 else "weekday",
                    "active_scenario_id": random.choice(scenarios)
                }

                # 随机实验
                exp_id = random.choice(experiments)
                variant = random.choice(variants_map[exp_id])

                # 模拟漏斗（转化率递减）
                if random.random() < 0.95:  # 95% impression
                    await self.record_event_async(
                        user_id, session_id, "impression",
                        item_sku=f"COF00{random.randint(1,5)}",
                        experiment_id=exp_id, variant=variant, context=context
                    )
                    total_events += 1

                    if random.random() < 0.45:  # 45% click
                        await self.record_event_async(
                            user_id, session_id, "click",
                            item_sku=f"COF00{random.randint(1,5)}",
                            experiment_id=exp_id, variant=variant, context=context
                        )
                        total_events += 1

                        if random.random() < 0.35:  # 35% add to cart
                            await self.record_event_async(
                                user_id, session_id, "add_to_cart",
                                item_sku=f"COF00{random.randint(1,5)}",
                                experiment_id=exp_id, variant=variant, context=context
                            )
                            total_events += 1

                            if random.random() < 0.70:  # 70% order
                                await self.record_event_async(
                                    user_id, session_id, "order",
                                    item_sku=f"COF00{random.randint(1,5)}",
                                    experiment_id=exp_id, variant=variant, context=context
                                )
                                total_events += 1

        await db.commit()

        return {
            "status": "simulated",
            "days": days,
            "events_per_day": events_per_day,
            "total_events": total_events
        }

    def simulate_data(self, *args, **kwargs) -> dict:
        """同步版本"""
        return _run_async(self.simulate_data_async(*args, **kwargs))


# ============ 单例实例 ============

ab_test_service = ABTestService()
feedback_service = FeedbackService()
behavior_service = BehaviorService()
session_service = SessionService()
explainability_service = ExplainabilityService()
preset_service = PresetService()
conversion_funnel_service = ConversionFunnelService()
