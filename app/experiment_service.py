"""
实验与个性化服务

功能:
1. A/B测试框架 - 支持多算法对比
2. 用户反馈收集 - 点赞/踩记录
3. 用户历史行为 - 订单/浏览/点击
4. Session实时个性化 - 动态偏好调整
"""
import json
import time
import hashlib
import random
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import defaultdict
from pydantic import BaseModel

# 数据存储路径
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

FEEDBACK_FILE = DATA_DIR / "user_feedback.json"
BEHAVIOR_FILE = DATA_DIR / "user_behavior.json"
EXPERIMENT_FILE = DATA_DIR / "experiments.json"


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


# ============ A/B测试服务 ============

class ABTestService:
    """A/B测试框架"""

    def __init__(self):
        self.experiments = self._load_experiments()
        self._init_default_experiments()

    def _load_experiments(self) -> dict:
        """加载实验配置"""
        if EXPERIMENT_FILE.exists():
            try:
                with open(EXPERIMENT_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_experiments(self):
        """保存实验配置"""
        with open(EXPERIMENT_FILE, "w") as f:
            json.dump(self.experiments, f, ensure_ascii=False, indent=2)

    def _init_default_experiments(self):
        """初始化默认实验"""
        if "rec_algorithm" not in self.experiments:
            self.experiments["rec_algorithm"] = {
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
            }

        if "reason_style" not in self.experiments:
            self.experiments["reason_style"] = {
                "experiment_id": "reason_style",
                "name": "推荐理由风格",
                "description": "测试不同推荐理由表述方式",
                "variants": [
                    {"id": "concise", "name": "简洁版", "weight": 50},
                    {"id": "detailed", "name": "详细版", "weight": 50}
                ],
                "status": "active",
                "created_at": time.time()
            }

        # 客制化推荐策略实验
        if "customization_strategy" not in self.experiments:
            self.experiments["customization_strategy"] = {
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
            }

        # 客制化展示方式实验
        if "customization_display" not in self.experiments:
            self.experiments["customization_display"] = {
                "experiment_id": "customization_display",
                "name": "客制化展示方式",
                "description": "测试客制化建议的不同展示方式",
                "variants": [
                    {"id": "inline", "name": "内联展示", "weight": 50},
                    {"id": "expandable", "name": "可展开展示", "weight": 50}
                ],
                "status": "active",
                "created_at": time.time()
            }

        self._save_experiments()

    def get_variant(self, experiment_id: str, user_id: str) -> dict:
        """
        为用户分配实验分组
        使用用户ID哈希确保同一用户始终进入同一分组
        """
        exp = self.experiments.get(experiment_id)
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

    def get_all_experiments(self) -> list[dict]:
        """获取所有实验"""
        return list(self.experiments.values())

    def create_experiment(self, exp: Experiment) -> dict:
        """创建新实验"""
        exp_dict = exp.model_dump()
        exp_dict["created_at"] = time.time()
        self.experiments[exp.experiment_id] = exp_dict
        self._save_experiments()
        return exp_dict


# ============ 用户反馈服务 ============

class FeedbackService:
    """用户反馈收集服务"""

    def __init__(self):
        self.feedback_data = self._load_feedback()

    def _load_feedback(self) -> dict:
        """加载反馈数据"""
        if FEEDBACK_FILE.exists():
            try:
                with open(FEEDBACK_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"feedbacks": [], "stats": {}}

    def _save_feedback(self):
        """保存反馈数据"""
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)

    def record_feedback(self, feedback: UserFeedback) -> dict:
        """记录用户反馈"""
        fb_dict = feedback.model_dump()
        fb_dict["timestamp"] = time.time()

        self.feedback_data["feedbacks"].append(fb_dict)

        # 更新统计
        item_key = feedback.item_sku
        if item_key not in self.feedback_data["stats"]:
            self.feedback_data["stats"][item_key] = {
                "likes": 0, "dislikes": 0, "clicks": 0, "orders": 0
            }

        stats = self.feedback_data["stats"][item_key]
        if feedback.feedback_type == "like":
            stats["likes"] += 1
        elif feedback.feedback_type == "dislike":
            stats["dislikes"] += 1
        elif feedback.feedback_type == "click":
            stats["clicks"] += 1
        elif feedback.feedback_type == "order":
            stats["orders"] += 1

        self._save_feedback()

        return {
            "status": "recorded",
            "item_stats": stats,
            "timestamp": fb_dict["timestamp"]
        }

    def get_item_stats(self, item_sku: str) -> dict:
        """获取商品反馈统计"""
        stats = self.feedback_data["stats"].get(item_sku, {
            "likes": 0, "dislikes": 0, "clicks": 0, "orders": 0
        })

        total = stats["likes"] + stats["dislikes"]
        if total > 0:
            stats["like_ratio"] = round(stats["likes"] / total, 2)
        else:
            stats["like_ratio"] = None

        return stats

    def get_experiment_stats(self, experiment_id: str) -> dict:
        """获取实验维度的反馈统计"""
        variant_stats = defaultdict(lambda: {"likes": 0, "dislikes": 0, "clicks": 0, "orders": 0})

        for fb in self.feedback_data["feedbacks"]:
            if fb.get("experiment_id") == experiment_id:
                variant = fb.get("variant", "unknown")
                fb_type = fb.get("feedback_type")
                if fb_type in variant_stats[variant]:
                    variant_stats[variant][fb_type] += 1

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


# ============ 用户行为服务 ============

# 订单数据文件
ORDER_FILE = DATA_DIR / "user_orders.json"


class BehaviorService:
    """用户历史行为服务"""

    # 时间衰减参数
    TIME_DECAY_HALFLIFE_DAYS = 30  # 半衰期30天

    def __init__(self):
        self.behavior_data = self._load_behavior()
        self.order_data = self._load_orders()

    def _load_behavior(self) -> dict:
        """加载行为数据"""
        if BEHAVIOR_FILE.exists():
            try:
                with open(BEHAVIOR_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"users": {}}

    def _load_orders(self) -> dict:
        """加载订单数据"""
        if ORDER_FILE.exists():
            try:
                with open(ORDER_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"orders": [], "user_order_index": {}, "stats": {}}

    def _save_behavior(self):
        """保存行为数据"""
        with open(BEHAVIOR_FILE, "w") as f:
            json.dump(self.behavior_data, f, ensure_ascii=False, indent=2)

    def _save_orders(self):
        """保存订单数据"""
        with open(ORDER_FILE, "w") as f:
            json.dump(self.order_data, f, ensure_ascii=False, indent=2)

    def _calculate_time_decay(self, timestamp: float) -> float:
        """计算时间衰减系数（指数衰减）"""
        days_ago = (time.time() - timestamp) / (24 * 3600)
        # 指数衰减: weight = 0.5 ^ (days / halflife)
        decay = 0.5 ** (days_ago / self.TIME_DECAY_HALFLIFE_DAYS)
        return max(decay, 0.1)  # 最低保留10%权重

    def record_order(self, order: OrderRecord) -> dict:
        """记录详细订单（增强版）"""
        order_dict = order.model_dump()
        order_dict["timestamp"] = order.timestamp or time.time()
        order_dict["order_id"] = f"order_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        # 添加到订单列表
        self.order_data["orders"].append(order_dict)

        # 更新用户订单索引
        user_id = order.user_id
        if user_id not in self.order_data["user_order_index"]:
            self.order_data["user_order_index"][user_id] = []
        self.order_data["user_order_index"][user_id].append(len(self.order_data["orders"]) - 1)

        # 更新统计
        sku = order.item_sku
        if sku not in self.order_data["stats"]:
            self.order_data["stats"][sku] = {
                "total_orders": 0,
                "total_revenue": 0,
                "unique_users": set(),
                "customization_counts": {}
            }
        stats = self.order_data["stats"][sku]
        stats["total_orders"] += 1
        stats["total_revenue"] += order.final_price or order.base_price or 0
        if isinstance(stats["unique_users"], set):
            stats["unique_users"].add(user_id)
            stats["unique_users"] = list(stats["unique_users"])
        elif user_id not in stats["unique_users"]:
            stats["unique_users"].append(user_id)

        # 统计客制化偏好
        if order.customization:
            for key, value in order.customization.items():
                if key not in stats["customization_counts"]:
                    stats["customization_counts"][key] = {}
                if str(value) not in stats["customization_counts"][key]:
                    stats["customization_counts"][key][str(value)] = 0
                stats["customization_counts"][key][str(value)] += 1

        self._save_orders()

        return {
            "status": "recorded",
            "order_id": order_dict["order_id"],
            "user_total_orders": len(self.order_data["user_order_index"].get(user_id, []))
        }

    def batch_record_orders(self, orders: list[OrderRecord]) -> dict:
        """批量记录订单（用于测试/模拟）"""
        results = []
        for order in orders:
            result = self.record_order(order)
            results.append(result)
        return {
            "status": "batch_recorded",
            "count": len(results),
            "results": results
        }

    def get_user_orders(self, user_id: str, limit: int = 50) -> list[dict]:
        """获取用户订单历史"""
        indices = self.order_data["user_order_index"].get(user_id, [])
        orders = []
        for idx in indices[-limit:]:
            if idx < len(self.order_data["orders"]):
                orders.append(self.order_data["orders"][idx])
        return orders

    def record_behavior(self, behavior: UserBehavior) -> dict:
        """记录用户行为"""
        user_id = behavior.user_id

        if user_id not in self.behavior_data["users"]:
            self.behavior_data["users"][user_id] = {
                "views": [],
                "clicks": [],
                "orders": [],
                "customizations": [],
                "category_affinity": {},
                "tag_affinity": {},
                "last_active": None
            }

        user_data = self.behavior_data["users"][user_id]
        user_data["last_active"] = time.time()

        record = {
            "sku": behavior.item_sku,
            "session_id": behavior.session_id,
            "timestamp": time.time(),
            "details": behavior.details or {}
        }

        if behavior.action == "view":
            user_data["views"].append(record)
            # 限制历史长度
            user_data["views"] = user_data["views"][-100:]
        elif behavior.action == "click":
            user_data["clicks"].append(record)
            user_data["clicks"] = user_data["clicks"][-100:]
        elif behavior.action == "order":
            user_data["orders"].append(record)
            # 同时记录到详细订单表
            details = behavior.details or {}
            order_record = OrderRecord(
                user_id=user_id,
                item_sku=behavior.item_sku,
                item_name=details.get("name"),
                category=details.get("category"),
                tags=details.get("tags"),
                base_price=details.get("base_price"),
                final_price=details.get("final_price"),
                customization=details.get("customization"),
                session_id=behavior.session_id
            )
            self.record_order(order_record)
        elif behavior.action == "customize":
            user_data["customizations"].append(record)
            user_data["customizations"] = user_data["customizations"][-50:]

        self._save_behavior()

        return {"status": "recorded", "action": behavior.action}

    def get_user_profile(self, user_id: str) -> dict:
        """获取用户画像（基于历史行为）"""
        user_data = self.behavior_data["users"].get(user_id)
        user_orders = self.get_user_orders(user_id)

        if not user_data and not user_orders:
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
        if user_data:
            for click in user_data.get("clicks", [])[-50:]:
                details = click.get("details", {})
                decay = self._calculate_time_decay(click.get("timestamp", time.time()))
                if "category" in details:
                    category_scores[details["category"]] += decay * 0.3  # 点击权重较低
                for tag in details.get("tags", []):
                    tag_scores[tag] += decay * 0.3

        # 归一化客制化偏好
        customization_preference = {}
        for key, value_counts in customization_counts.items():
            total = sum(value_counts.values())
            customization_preference[key] = {
                v: round(c / total, 2) for v, c in sorted(value_counts.items(), key=lambda x: -x[1])[:3]
            }

        return {
            "user_id": user_id,
            "is_new_user": False,
            "order_count": len(user_orders),
            "view_count": len(user_data.get("views", [])) if user_data else 0,
            "click_count": len(user_data.get("clicks", [])) if user_data else 0,
            "total_spend": round(total_spend, 2),
            "favorite_items": [{"sku": sku, "score": round(score, 2)} for sku, score in favorite_items],
            "category_preference": dict(sorted(category_scores.items(), key=lambda x: -x[1])[:5]),
            "tag_preference": dict(sorted(tag_scores.items(), key=lambda x: -x[1])[:10]),
            "customization_preference": customization_preference,
            "last_active": user_data.get("last_active") if user_data else None,
            "recent_orders": user_orders[-5:]
        }

    def get_behavior_based_boost(self, user_id: str, item_sku: str, item_category: str, item_tags: list) -> float:
        """基于用户历史行为计算推荐加权（增强版：带时间衰减）"""
        user_orders = self.get_user_orders(user_id)
        profile = self.get_user_profile(user_id)

        if profile["is_new_user"]:
            return 1.0

        boost = 1.0

        # 1. 复购加权（带时间衰减）
        repurchase_score = 0
        for order in user_orders:
            if order["item_sku"] == item_sku:
                decay = self._calculate_time_decay(order.get("timestamp", time.time()))
                repurchase_score += decay * 0.2  # 每次购买+20%衰减后权重
        boost *= 1.0 + min(repurchase_score, 1.0)  # 最多+100%

        # 2. 类别偏好加权
        cat_pref = profile.get("category_preference", {})
        total_cat_score = sum(cat_pref.values())
        if item_category in cat_pref and total_cat_score > 0:
            cat_ratio = cat_pref[item_category] / total_cat_score
            boost *= 1.0 + (cat_ratio * 0.4)  # 最多+40%

        # 3. 标签偏好加权
        tag_pref = profile.get("tag_preference", {})
        total_tag_score = sum(tag_pref.values())
        if total_tag_score > 0:
            matched_tag_score = sum(tag_pref.get(tag, 0) for tag in item_tags)
            tag_ratio = matched_tag_score / total_tag_score
            boost *= 1.0 + (tag_ratio * 0.3)  # 最多+30%

        # 4. 消费水平匹配（可选：如果有价格信息）
        # 高消费用户对高价商品有加权

        return min(boost, 2.5)  # 最多2.5倍加权

    def get_order_based_recommendation_boost(
        self,
        user_id: str,
        item_sku: str,
        item_category: str,
        item_tags: list,
        item_price: float = None
    ) -> dict:
        """获取基于订单历史的推荐加权（详细版，返回各因素分解）"""
        user_orders = self.get_user_orders(user_id)

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
                # 价格在用户习惯范围内(0.7-1.5倍)给予加权
                if 0.7 <= price_ratio <= 1.5:
                    factors["price_match"] = 1.1
                    if price_ratio > 1.2:
                        explanations.append("符合消费升级偏好")
                elif price_ratio < 0.7:
                    factors["price_match"] = 0.95  # 价格过低轻微降权
                else:
                    factors["price_match"] = 0.9  # 价格过高降权
            else:
                factors["price_match"] = 1.0
        else:
            factors["price_match"] = 1.0

        # 计算总加权
        total_boost = factors["repurchase"] * factors["category"] * factors["tag"] * factors["price_match"]
        total_boost = min(total_boost, 3.0)  # 上限3倍

        return {
            "total_boost": round(total_boost, 3),
            "factors": {k: round(v, 3) for k, v in factors.items()},
            "explanation": "；".join(explanations) if explanations else "综合历史订单偏好"
        }

    def get_customization_based_boost(
        self,
        user_id: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str]
    ) -> dict:
        """
        基于用户客制化偏好计算商品推荐加权

        Args:
            user_id: 用户ID
            item_constraints: 商品的客制化约束（CustomizationConstraints.model_dump()）
            item_available_temperatures: 商品支持的温度列表
            item_available_sizes: 商品支持的杯型列表

        Returns:
            {
                "total_boost": float,  # 0.8-1.5
                "factors": {
                    "temperature_match": float,
                    "size_match": float,
                    "milk_match": float,
                    "sugar_match": float
                },
                "explanation": str
            }
        """
        # 中英文映射（因为商品数据使用中文，用户偏好使用枚举值）
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
            """检查用户偏好是否匹配商品支持的选项（支持中英文映射）"""
            if not item_values:
                return True  # 无约束时视为匹配
            pref_variants = mapping.get(pref_value.upper(), [pref_value])
            for variant in pref_variants:
                for item_val in item_values:
                    if variant == item_val or variant.upper() == str(item_val).upper():
                        return True
            return False
        profile = self.get_user_profile(user_id)
        customization_pref = profile.get("customization_preference", {})

        # 新用户或无偏好数据，返回中性加权
        if profile["is_new_user"] or not customization_pref:
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
            # 找用户最常选的温度
            preferred_temp = max(temp_pref.items(), key=lambda x: x[1])[0] if temp_pref else None
            if preferred_temp:
                # 使用中英文映射检查商品是否支持用户偏好的温度
                if matches_preference(preferred_temp, item_available_temperatures, TEMP_MAP):
                    factors["temperature_match"] = 1.15  # 匹配加权15%
                    pref_ratio = temp_pref.get(preferred_temp, 0)
                    if pref_ratio > 0.6:
                        temp_display = {"HOT": "热", "ICED": "冰", "BLENDED": "冰沙"}.get(preferred_temp.upper(), preferred_temp)
                        explanations.append(f"支持您偏好的{temp_display}饮品")
                else:
                    factors["temperature_match"] = 0.9  # 不匹配降权10%
            else:
                factors["temperature_match"] = 1.0
        else:
            factors["temperature_match"] = 1.0

        # 2. 杯型偏好匹配
        size_pref = customization_pref.get("cup_size", {})
        if size_pref and item_available_sizes:
            preferred_size = max(size_pref.items(), key=lambda x: x[1])[0] if size_pref else None
            if preferred_size:
                # 使用中英文映射检查杯型匹配
                if matches_preference(preferred_size, item_available_sizes, SIZE_MAP):
                    factors["size_match"] = 1.1  # 匹配加权10%
                else:
                    factors["size_match"] = 0.95  # 不匹配轻微降权
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
                    # 使用中英文映射检查商品是否支持用户偏好的奶类
                    if matches_preference(preferred_milk, available_milks, MILK_MAP):
                        factors["milk_match"] = 1.2  # 奶类匹配加权较高20%
                        pref_ratio = milk_pref.get(preferred_milk, 0)
                        if pref_ratio > 0.5:
                            milk_name_map = {
                                "OAT": "燕麦奶", "WHOLE": "全脂奶", "SKIM": "脱脂奶",
                                "SOY": "豆奶", "COCONUT": "椰奶", "NONE": "不加奶"
                            }
                            milk_display = milk_name_map.get(preferred_milk.upper(), preferred_milk)
                            explanations.append(f"支持您常选的{milk_display}")
                    else:
                        factors["milk_match"] = 0.85  # 不支持降权15%
                else:
                    factors["milk_match"] = 1.0
            else:
                # 商品不支持奶类定制（如美式咖啡）
                # 如果用户偏好加奶，轻微降权
                preferred_milk = max(milk_pref.items(), key=lambda x: x[1])[0] if milk_pref else None
                if preferred_milk and preferred_milk.upper() != "NONE":
                    factors["milk_match"] = 0.95
                else:
                    factors["milk_match"] = 1.05  # 用户不加奶，商品也不加奶，轻微加权
        else:
            factors["milk_match"] = 1.0

        # 4. 糖度偏好匹配
        sugar_pref = customization_pref.get("sugar_level", {})
        if sugar_pref and item_constraints:
            available_sugars = item_constraints.get("available_sugar_levels")
            if available_sugars:
                preferred_sugar = max(sugar_pref.items(), key=lambda x: x[1])[0] if sugar_pref else None
                if preferred_sugar:
                    # 使用中英文映射检查商品是否支持用户偏好的糖度
                    if matches_preference(preferred_sugar, available_sugars, SUGAR_MAP):
                        factors["sugar_match"] = 1.15  # 糖度匹配加权15%
                        pref_ratio = sugar_pref.get(preferred_sugar, 0)
                        if pref_ratio > 0.5:
                            sugar_name_map = {
                                "STANDARD": "全糖", "LIGHT": "少糖", "HALF": "半糖",
                                "NONE": "无糖", "EXTRA": "多糖"
                            }
                            sugar_display = sugar_name_map.get(preferred_sugar.upper(), preferred_sugar)
                            explanations.append(f"可选{sugar_display}")
                    else:
                        factors["sugar_match"] = 0.9  # 不支持降权10%
                else:
                    factors["sugar_match"] = 1.0
            else:
                factors["sugar_match"] = 1.0
        else:
            factors["sugar_match"] = 1.0

        # 计算总加权
        total_boost = (
            factors["temperature_match"] *
            factors["size_match"] *
            factors["milk_match"] *
            factors["sugar_match"]
        )

        # 限制范围在 0.8-1.5
        total_boost = max(0.8, min(1.5, total_boost))

        return {
            "total_boost": round(total_boost, 3),
            "factors": {k: round(v, 3) for k, v in factors.items()},
            "explanation": "；".join(explanations) if explanations else "客制化偏好综合匹配"
        }

    def get_suggested_customization_for_item(
        self,
        user_id: str,
        item_sku: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str],
        item_base_price: float
    ) -> dict:
        """
        为用户推荐特定商品的最佳客制化组合

        Args:
            user_id: 用户ID
            item_sku: 商品SKU
            item_constraints: 商品客制化约束
            item_available_temperatures: 商品支持的温度列表
            item_available_sizes: 商品支持的杯型列表
            item_base_price: 商品基础价格

        Returns:
            {
                "suggested_customization": {
                    "temperature": "ICED",
                    "cup_size": "GRANDE",
                    "sugar_level": "NONE",
                    "milk_type": "OAT"
                },
                "confidence": 0.78,
                "reason": "您偏好冰饮；您常选燕麦奶",
                "estimated_price_adjustment": 3.0,
                "estimated_final_price": 41.0
            }
        """
        profile = self.get_user_profile(user_id)
        customization_pref = profile.get("customization_preference", {})

        suggested = {}
        reasons = []
        confidence_factors = []
        price_adjustment = 0.0

        # 1. 温度推荐
        if item_available_temperatures:
            temp_pref = customization_pref.get("temperature", {})
            if temp_pref:
                # 找用户偏好的温度，检查商品是否支持
                for temp, ratio in sorted(temp_pref.items(), key=lambda x: -x[1]):
                    temp_upper = temp.upper()
                    temp_values = [t.upper() for t in item_available_temperatures]
                    if temp_upper in temp_values or temp in item_available_temperatures:
                        suggested["temperature"] = temp
                        confidence_factors.append(ratio)
                        if ratio > 0.5:
                            temp_display = {"HOT": "热", "ICED": "冰", "WARM": "温"}.get(temp_upper, temp)
                            reasons.append(f"您偏好{temp_display}饮")
                        break
                else:
                    # 用户偏好不可用，选默认
                    if item_constraints and item_constraints.get("default_temperature"):
                        suggested["temperature"] = item_constraints["default_temperature"]
                    else:
                        suggested["temperature"] = item_available_temperatures[0]
                    confidence_factors.append(0.3)
            else:
                # 新用户，选默认或第一个
                if item_constraints and item_constraints.get("default_temperature"):
                    suggested["temperature"] = item_constraints["default_temperature"]
                else:
                    suggested["temperature"] = item_available_temperatures[0]
                confidence_factors.append(0.5)

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
                        # 计算杯型价格调整
                        if size_upper == "VENTI":
                            price_adjustment += 4
                        elif size_upper == "TALL":
                            price_adjustment -= 3
                        break
                else:
                    suggested["cup_size"] = "GRANDE"  # 默认大杯
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
                        # 特殊奶类加价
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
            # 加浓缩
            if item_constraints.get("supports_extra_shot"):
                extra_shot_pref = customization_pref.get("extra_shot", {})
                if extra_shot_pref.get("True", 0) > 0.3 or extra_shot_pref.get("true", 0) > 0.3:
                    suggested["extra_shot"] = True
                    price_adjustment += 4
                    reasons.append("您常选加浓缩")
                else:
                    suggested["extra_shot"] = False

            # 奶油
            if item_constraints.get("supports_whipped_cream"):
                cream_pref = customization_pref.get("whipped_cream", {})
                if cream_pref.get("True", 0) > 0.3 or cream_pref.get("true", 0) > 0.3:
                    suggested["whipped_cream"] = True
                    reasons.append("您喜欢加奶油")
                else:
                    suggested["whipped_cream"] = False

        # 计算置信度
        if confidence_factors:
            confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            confidence = 0.5

        # 新用户置信度降低
        if profile["is_new_user"]:
            confidence = min(confidence, 0.4)
            reasons = ["推荐默认配置"]

        estimated_final_price = item_base_price + price_adjustment

        return {
            "suggested_customization": suggested,
            "confidence": round(confidence, 2),
            "reason": "；".join(reasons[:3]) if reasons else "综合您的历史偏好推荐",
            "estimated_price_adjustment": round(price_adjustment, 2),
            "estimated_final_price": round(estimated_final_price, 2)
        }

    def get_order_stats(self) -> dict:
        """获取订单统计概览"""
        return {
            "total_orders": len(self.order_data["orders"]),
            "total_users": len(self.order_data["user_order_index"]),
            "item_stats": {
                sku: {
                    "total_orders": stats["total_orders"],
                    "unique_users": len(stats["unique_users"]) if isinstance(stats["unique_users"], list) else 0
                }
                for sku, stats in self.order_data["stats"].items()
            }
        }


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

        # 限制交互历史长度
        session["interactions"] = session["interactions"][-50:]

        prefs = session["realtime_preferences"]

        # 实时更新偏好
        if interaction_type == "like":
            for tag in item_data.get("tags", []):
                if tag not in prefs["liked_tags"]:
                    prefs["liked_tags"].append(tag)

        elif interaction_type == "dislike":
            for tag in item_data.get("tags", []):
                if tag not in prefs["disliked_tags"]:
                    prefs["disliked_tags"].append(tag)
                # 从喜欢列表移除
                if tag in prefs["liked_tags"]:
                    prefs["liked_tags"].remove(tag)

        elif interaction_type in ["view", "click"]:
            category = item_data.get("category")
            if category and category not in prefs["viewed_categories"]:
                prefs["viewed_categories"].append(category)

            # 更新价格偏好
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

        # 喜欢的标签加权
        liked_match = sum(1 for tag in item_tags if tag in prefs["liked_tags"])
        boost *= 1.0 + (liked_match * 0.15)  # 每匹配一个+15%

        # 不喜欢的标签降权
        disliked_match = sum(1 for tag in item_tags if tag in prefs["disliked_tags"])
        boost *= max(0.3, 1.0 - (disliked_match * 0.3))  # 每匹配一个-30%，最低30%

        # 浏览过的类别轻微加权
        if item_category in prefs["viewed_categories"]:
            boost *= 1.1

        # 价格区间偏好
        if prefs["price_range"] and prefs["price_range"]["count"] >= 3:
            pr = prefs["price_range"]
            if pr["min"] <= item_price <= pr["max"]:
                boost *= 1.05  # 价格在用户偏好区间内

        return min(boost, 2.5)  # 最多2.5倍

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

        # 1. 语义匹配因素
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

        # 2. 关键词匹配
        if matched_keywords:
            factors.append({
                "type": "keyword",
                "label": "偏好关键词匹配",
                "matched": matched_keywords[:3],
                "description": f"匹配了您偏好的「{'、'.join(matched_keywords[:3])}」",
                "weight": 0.2
            })

        # 3. 历史行为因素
        if behavior_boost > 1.1:
            factors.append({
                "type": "history",
                "label": "历史偏好加成",
                "boost": round(behavior_boost, 2),
                "description": "基于您的购买和浏览历史",
                "weight": 0.2
            })

        # 4. 实时偏好因素
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

        # 5. 商品特性因素
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

        # 计算各因素贡献占比
        total_weight = sum(abs(f.get("weight", 0)) for f in factors)
        for factor in factors:
            if total_weight > 0:
                factor["contribution"] = round(abs(factor.get("weight", 0)) / total_weight * 100, 1)

        # 生成摘要
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

PRESET_FILE = DATA_DIR / "user_presets.json"


class PresetService:
    """用户客制化预设服务"""

    def __init__(self):
        self.presets = self._load_presets()

    def _load_presets(self) -> dict:
        """加载预设数据"""
        if PRESET_FILE.exists():
            try:
                with open(PRESET_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"presets": {}, "user_index": {}}

    def _save_presets(self):
        """保存预设数据"""
        with open(PRESET_FILE, "w") as f:
            json.dump(self.presets, f, ensure_ascii=False, indent=2)

    def create_preset(self, preset: dict) -> dict:
        """
        创建用户预设

        Args:
            preset: {
                "user_id": str,
                "name": str,
                "default_temperature": str (optional),
                "default_cup_size": str (optional),
                "default_sugar_level": str (optional),
                "default_milk_type": str (optional),
                "extra_shot": bool (optional),
                "whipped_cream": bool (optional)
            }

        Returns:
            {"status": "created", "preset": {...}}
        """
        user_id = preset.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}

        preset_id = f"preset_{user_id}_{int(time.time() * 1000)}"
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
            "created_at": time.time(),
            "updated_at": time.time()
        }

        # 存储预设
        self.presets["presets"][preset_id] = preset_data

        # 更新用户索引
        if user_id not in self.presets["user_index"]:
            self.presets["user_index"][user_id] = []
        self.presets["user_index"][user_id].append(preset_id)

        self._save_presets()

        return {
            "status": "created",
            "preset": preset_data
        }

    def get_user_presets(self, user_id: str) -> list[dict]:
        """获取用户的所有预设"""
        preset_ids = self.presets["user_index"].get(user_id, [])
        return [
            self.presets["presets"][pid]
            for pid in preset_ids
            if pid in self.presets["presets"]
        ]

    def get_preset(self, preset_id: str) -> Optional[dict]:
        """获取单个预设"""
        return self.presets["presets"].get(preset_id)

    def update_preset(self, preset_id: str, updates: dict) -> dict:
        """更新预设"""
        if preset_id not in self.presets["presets"]:
            return {"status": "error", "message": "preset not found"}

        preset = self.presets["presets"][preset_id]
        allowed_fields = [
            "name", "default_temperature", "default_cup_size",
            "default_sugar_level", "default_milk_type",
            "extra_shot", "whipped_cream"
        ]

        for field in allowed_fields:
            if field in updates:
                preset[field] = updates[field]

        preset["updated_at"] = time.time()
        self._save_presets()

        return {"status": "updated", "preset": preset}

    def delete_preset(self, preset_id: str) -> dict:
        """删除预设"""
        if preset_id not in self.presets["presets"]:
            return {"status": "error", "message": "preset not found"}

        preset = self.presets["presets"][preset_id]
        user_id = preset["user_id"]

        # 从预设列表删除
        del self.presets["presets"][preset_id]

        # 从用户索引删除
        if user_id in self.presets["user_index"]:
            self.presets["user_index"][user_id] = [
                pid for pid in self.presets["user_index"][user_id]
                if pid != preset_id
            ]

        self._save_presets()
        return {"status": "deleted", "preset_id": preset_id}

    def apply_preset_to_item(
        self,
        preset_id: str,
        item_constraints: Optional[dict],
        item_available_temperatures: list[str],
        item_available_sizes: list[str],
        item_base_price: float
    ) -> dict:
        """
        将预设应用到商品，考虑商品约束

        Returns:
            {
                "applied_customization": {...},
                "conflicts": [...],
                "estimated_price_adjustment": float,
                "estimated_final_price": float
            }
        """
        preset = self.get_preset(preset_id)
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
            if item_constraints.get("supports_extra_shot"):
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


# ============ 单例实例 ============

ab_test_service = ABTestService()
feedback_service = FeedbackService()
behavior_service = BehaviorService()
session_service = SessionService()
explainability_service = ExplainabilityService()
preset_service = PresetService()
