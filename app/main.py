"""FastAPI 主应用"""
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.models import (
    Category, CupSize, Temperature, SugarLevel, MilkType,
    UserPreference, Customization
)
from app.data import MENU_ITEMS, get_menu_by_sku, get_menu_by_category, get_all_categories
from app.recommendation import recommendation_engine
from app.embedding_service import embedding_recommendation_engine
from app.db import init_db, close_db, migrate_from_json


# ============ 应用生命周期 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    print("[Startup] 初始化数据库...")
    await init_db()
    print("[Startup] 执行 JSON 到 SQLite 迁移...")
    await migrate_from_json()
    print("[Startup] 数据库初始化完成")

    yield

    # 关闭时清理资源
    print("[Shutdown] 关闭数据库连接...")
    await close_db()
    print("[Shutdown] 清理完成")


# ============ 上下文自动获取 ============

def get_auto_context() -> dict:
    """自动获取当前上下文（时间、季节等）"""
    now = datetime.now()
    hour = now.hour

    # 时间段分类
    if 5 <= hour < 11:
        time_of_day = "morning"
    elif 11 <= hour < 14:
        time_of_day = "lunch"
    elif 14 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 21:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    # 季节分类
    month = now.month
    if month in [3, 4, 5]:
        season = "spring"
    elif month in [6, 7, 8]:
        season = "summer"
    elif month in [9, 10, 11]:
        season = "autumn"
    else:
        season = "winter"

    # 工作日/周末
    day_type = "weekend" if now.weekday() >= 5 else "weekday"

    return {
        "time_of_day": time_of_day,
        "hour": hour,
        "season": season,
        "day_type": day_type,
        "month": month
    }


class EmbeddingRecommendRequest(BaseModel):
    """Embedding推荐请求"""
    persona_type: str
    custom_tags: Optional[list[str]] = None
    context: Optional[dict] = None
    top_k: int = 6


class EmbeddingRecommendV2Request(BaseModel):
    """增强版推荐请求"""
    persona_type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    custom_tags: Optional[list[str]] = None
    context: Optional[dict] = None
    top_k: int = 6
    enable_ab_test: bool = True
    enable_behavior: bool = True
    enable_session: bool = True
    enable_explainability: bool = True
    auto_context: bool = True  # 是否自动注入上下文


class CustomPreferenceRequest(BaseModel):
    """自定义偏好推荐请求"""
    custom_preference: str  # 用户自由文本描述
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    top_k: int = 6
    enable_ab_test: bool = True
    enable_behavior: bool = True
    enable_session: bool = True


class FeedbackRequest(BaseModel):
    """用户反馈请求"""
    user_id: str
    session_id: str
    item_sku: str
    feedback_type: str  # "like" | "dislike" | "click" | "order"
    experiment_id: Optional[str] = None
    variant: Optional[str] = None
    context: Optional[dict] = None


class BehaviorRequest(BaseModel):
    """用户行为请求"""
    user_id: str
    session_id: str
    action: str  # "view" | "click" | "order" | "customize"
    item_sku: str
    details: Optional[dict] = None


class SessionInteractionRequest(BaseModel):
    """Session交互请求"""
    session_id: str
    interaction_type: str  # "like" | "dislike" | "view" | "click"
    item_data: dict  # {sku, tags, category, price}

app = FastAPI(
    title="星巴克猜你喜欢 Demo",
    description="类似星巴克的个性化菜单推荐系统",
    version="1.0.0",
    lifespan=lifespan
)

# 静态文件和模板
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# 模拟用户偏好存储
user_preferences: dict[str, UserPreference] = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/menu")
async def get_menu():
    """获取完整菜单"""
    return {
        "items": [item.model_dump() for item in MENU_ITEMS],
        "categories": get_all_categories()
    }


@app.get("/api/menu/category/{category}")
async def get_menu_category(category: str):
    """获取分类菜单"""
    try:
        cat = Category[category.upper()]
        items = get_menu_by_category(cat)
        return {"items": [item.model_dump() for item in items]}
    except KeyError:
        return {"error": "分类不存在", "items": []}


@app.get("/api/menu/item/{sku}")
async def get_menu_item(sku: str):
    """获取单个菜单项"""
    item = get_menu_by_sku(sku)
    if item:
        return item.model_dump()
    return {"error": "商品不存在"}


@app.get("/api/recommendations")
async def get_recommendations(user_id: str = "guest", limit: int = 6):
    """获取个性化推荐"""
    user_pref = user_preferences.get(user_id)
    recommendations = recommendation_engine.get_recommendations(user_pref, limit)

    return {
        "user_id": user_id,
        "recommendations": [
            {
                "item": rec["item"].model_dump(),
                "score": round(rec["score"], 2),
                "reason": rec["reason"]
            }
            for rec in recommendations
        ]
    }


@app.get("/api/similar/{sku}")
async def get_similar_items(sku: str, limit: int = 4):
    """获取相似商品"""
    items = recommendation_engine.get_similar_items(sku, limit)
    return {"items": [item.model_dump() for item in items]}


@app.post("/api/user/preference")
async def update_user_preference(pref: UserPreference):
    """更新用户偏好"""
    user_preferences[pref.user_id] = pref
    return {"status": "success", "message": "偏好已更新"}


@app.post("/api/user/order")
async def record_order(user_id: str, sku: str):
    """记录用户订单（用于推荐）"""
    if user_id not in user_preferences:
        user_preferences[user_id] = UserPreference(user_id=user_id)

    user_preferences[user_id].order_history.append(sku)
    return {"status": "success"}


@app.get("/api/customization/options")
async def get_customization_options():
    """获取所有客制化选项"""
    return {
        "cup_sizes": [{"value": s.name, "label": s.value} for s in CupSize],
        "temperatures": [{"value": t.name, "label": t.value} for t in Temperature],
        "sugar_levels": [{"value": s.name, "label": s.value} for s in SugarLevel],
        "milk_types": [{"value": m.name, "label": m.value} for m in MilkType],
        "extras": [
            {"id": "extra_shot", "name": "加浓缩", "price": 4},
            {"id": "whipped_cream", "name": "奶油顶", "price": 0},
        ],
        "syrups": [
            {"id": "vanilla", "name": "香草糖浆", "price": 3},
            {"id": "caramel", "name": "焦糖糖浆", "price": 3},
            {"id": "hazelnut", "name": "榛果糖浆", "price": 3},
        ]
    }


@app.post("/api/calculate-price")
async def calculate_price(sku: str, customization: Customization):
    """计算客制化后的价格"""
    item = get_menu_by_sku(sku)
    if not item:
        return {"error": "商品不存在"}

    price = item.base_price

    # 杯型价格调整
    if customization.cup_size == CupSize.VENTI:
        price += 4
    elif customization.cup_size == CupSize.TALL:
        price -= 3

    # 额外选项
    if customization.extra_shot:
        price += 4

    if customization.milk_type in [MilkType.OAT, MilkType.COCONUT]:
        price += 3

    if customization.syrup:
        price += 3

    return {
        "base_price": item.base_price,
        "final_price": price,
        "adjustments": []
    }


# ============ Embedding增强推荐API ============

@app.get("/api/embedding/personas")
async def get_personas():
    """获取所有可用的用户画像类型"""
    return {
        "personas": embedding_recommendation_engine.get_available_personas()
    }


@app.post("/api/embedding/recommend")
async def embedding_recommend(request: EmbeddingRecommendRequest):
    """
    Embedding增强推荐

    返回完整的推荐过程，包括:
    - 用户画像生成
    - 向量化过程
    - 召回和重排
    - 推荐理由生成
    """
    result = embedding_recommendation_engine.recommend(
        persona_type=request.persona_type,
        custom_tags=request.custom_tags,
        context=request.context,
        top_k=request.top_k
    )
    return result


@app.get("/embedding", response_class=HTMLResponse)
async def embedding_demo(request: Request):
    """Embedding增强推荐演示页面"""
    return templates.TemplateResponse("embedding_demo.html", {"request": request})


# ============ 增强版推荐API (V2) ============

@app.post("/api/embedding/recommend/v2")
async def embedding_recommend_v2(request: EmbeddingRecommendV2Request):
    """
    增强版Embedding推荐

    集成以下功能:
    - A/B测试: 自动分配实验分组
    - 历史行为: 基于用户历史加权
    - Session个性化: 实时偏好调整
    - 解释性增强: 详细的推荐解释
    - 上下文自动获取: 时间/季节等自动注入
    """
    # 自动注入上下文
    context = request.context or {}
    if request.auto_context:
        auto_ctx = get_auto_context()
        # 合并上下文，用户传入的优先
        context = {**auto_ctx, **context}

    result = embedding_recommendation_engine.recommend_v2(
        persona_type=request.persona_type,
        user_id=request.user_id,
        session_id=request.session_id,
        custom_tags=request.custom_tags,
        context=context,
        top_k=request.top_k,
        enable_ab_test=request.enable_ab_test,
        enable_behavior=request.enable_behavior,
        enable_session=request.enable_session,
        enable_explainability=request.enable_explainability
    )

    # 添加上下文信息到返回结果
    result["context"] = context
    return result


@app.post("/api/embedding/recommend/custom")
async def embedding_recommend_custom(request: CustomPreferenceRequest):
    """
    自定义偏好推荐

    支持用户输入自由文本描述偏好，如：
    - "我想要低卡、提神、清爽的饮品"
    - "甜一点的奶茶，适合下午喝"
    """
    # 自动获取上下文
    context = get_auto_context()

    result = embedding_recommendation_engine.recommend_with_custom_preference(
        custom_preference=request.custom_preference,
        user_id=request.user_id,
        session_id=request.session_id,
        context=context,
        top_k=request.top_k,
        enable_ab_test=request.enable_ab_test,
        enable_behavior=request.enable_behavior,
        enable_session=request.enable_session
    )

    result["context"] = context
    return result


@app.get("/api/context")
async def get_current_context():
    """获取当前自动上下文"""
    return get_auto_context()


# ============ A/B测试API ============

@app.get("/api/experiments")
async def get_experiments():
    """获取所有A/B实验"""
    from app.experiment_service import ab_test_service
    experiments = await ab_test_service.get_all_experiments_async()
    return {"experiments": experiments}


@app.get("/api/experiments/{experiment_id}/variant")
async def get_user_variant(experiment_id: str, user_id: str):
    """获取用户在指定实验中的分组"""
    from app.experiment_service import ab_test_service
    variant = await ab_test_service.get_variant_async(experiment_id, user_id)
    return variant


@app.get("/api/experiments/{experiment_id}/stats")
async def get_experiment_stats(experiment_id: str):
    """获取实验统计数据"""
    from app.experiment_service import feedback_service
    stats = await feedback_service.get_experiment_stats_async(experiment_id)
    return {"experiment_id": experiment_id, "variant_stats": stats}


# ============ 用户反馈API ============

@app.post("/api/feedback")
async def record_feedback(request: FeedbackRequest):
    """记录用户反馈（点赞/踩/点击/下单）"""
    from app.experiment_service import feedback_service, UserFeedback

    feedback = UserFeedback(
        user_id=request.user_id,
        session_id=request.session_id,
        item_sku=request.item_sku,
        feedback_type=request.feedback_type,
        experiment_id=request.experiment_id,
        variant=request.variant,
        context=request.context
    )

    result = await feedback_service.record_feedback_async(feedback)
    return result


@app.get("/api/feedback/item/{item_sku}")
async def get_item_feedback_stats(item_sku: str):
    """获取商品反馈统计"""
    from app.experiment_service import feedback_service
    stats = await feedback_service.get_item_stats_async(item_sku)
    return {"item_sku": item_sku, "stats": stats}


# ============ 用户行为API ============

@app.post("/api/behavior")
async def record_behavior(request: BehaviorRequest):
    """记录用户行为（浏览/点击/下单/客制化）"""
    from app.experiment_service import behavior_service, UserBehavior

    behavior = UserBehavior(
        user_id=request.user_id,
        session_id=request.session_id,
        action=request.action,
        item_sku=request.item_sku,
        details=request.details
    )

    result = await behavior_service.record_behavior_async(behavior)
    return result


@app.get("/api/behavior/user/{user_id}")
async def get_user_behavior_profile(user_id: str):
    """获取用户行为画像"""
    from app.experiment_service import behavior_service
    profile = await behavior_service.get_user_profile_async(user_id)
    return profile


# ============ Session API ============

@app.post("/api/session/interaction")
async def record_session_interaction(request: SessionInteractionRequest):
    """记录Session内交互，实时更新偏好"""
    from app.experiment_service import session_service

    result = session_service.record_interaction(
        session_id=request.session_id,
        interaction_type=request.interaction_type,
        item_data=request.item_data
    )
    return result


@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """获取Session信息"""
    from app.experiment_service import session_service
    info = session_service.get_session_info(session_id)
    return info


@app.post("/api/session/{session_id}/init")
async def init_session(session_id: str, user_id: str = None):
    """初始化Session"""
    from app.experiment_service import session_service
    session = session_service.get_or_create_session(session_id, user_id)
    return {
        "session_id": session["session_id"],
        "user_id": session["user_id"],
        "created_at": session["created_at"]
    }


# ============ 订单历史API ============

class OrderRecordRequest(BaseModel):
    """订单记录请求"""
    user_id: str
    item_sku: str
    item_name: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    base_price: Optional[float] = None
    final_price: Optional[float] = None
    customization: Optional[dict] = None
    session_id: Optional[str] = None
    timestamp: Optional[float] = None  # 允许指定历史时间戳用于模拟


class BatchOrderRequest(BaseModel):
    """批量订单请求"""
    orders: list[OrderRecordRequest]


class SimulateOrdersRequest(BaseModel):
    """模拟订单请求"""
    user_id: str
    order_count: int = 10
    days_range: int = 60  # 订单分布的天数范围
    category_weights: Optional[dict[str, float]] = None  # 类别权重，如 {"咖啡": 0.6, "茶饮": 0.3}


@app.post("/api/orders")
async def record_order(request: OrderRecordRequest):
    """记录单个订单"""
    from app.experiment_service import behavior_service, OrderRecord

    order = OrderRecord(
        user_id=request.user_id,
        item_sku=request.item_sku,
        item_name=request.item_name,
        category=request.category,
        tags=request.tags,
        base_price=request.base_price,
        final_price=request.final_price,
        customization=request.customization,
        session_id=request.session_id,
        timestamp=request.timestamp
    )

    result = await behavior_service.record_order_async(order)
    return result


@app.post("/api/orders/batch")
async def batch_record_orders(request: BatchOrderRequest):
    """批量记录订单（用于测试/模拟）"""
    from app.experiment_service import behavior_service, OrderRecord
    from app.data import MENU_ITEMS

    # 构建SKU到商品的映射
    sku_to_item = {item.sku: item for item in MENU_ITEMS}

    orders = []
    for o in request.orders:
        # 自动填充商品信息
        item = sku_to_item.get(o.item_sku)
        orders.append(OrderRecord(
            user_id=o.user_id,
            item_sku=o.item_sku,
            item_name=o.item_name or (item.name if item else None),
            category=o.category or (item.category if item else None),
            tags=o.tags or ([tag for tag in item.tags] if item and item.tags else None),
            base_price=o.base_price or (item.base_price if item else None),
            final_price=o.final_price,
            customization=o.customization,
            session_id=o.session_id,
            timestamp=o.timestamp
        ))

    result = await behavior_service.batch_record_orders_async(orders)
    return result


@app.get("/api/orders/user/{user_id}")
async def get_user_orders(user_id: str, limit: int = 50):
    """获取用户订单历史"""
    from app.experiment_service import behavior_service

    orders = await behavior_service.get_user_orders_async(user_id, limit)
    profile = await behavior_service.get_user_profile_async(user_id)

    return {
        "user_id": user_id,
        "order_count": len(orders),
        "orders": orders,
        "profile": profile
    }


@app.post("/api/orders/simulate")
async def simulate_orders(request: SimulateOrdersRequest):
    """模拟生成订单历史（用于测试推荐效果）"""
    import random
    import time
    from app.experiment_service import behavior_service, OrderRecord
    from app.data import MENU_ITEMS

    # 按类别分组菜单
    items_by_category = {}
    for item in MENU_ITEMS:
        cat = item.category.value
        if cat not in items_by_category:
            items_by_category[cat] = []
        items_by_category[cat].append(item)

    # 获取类别权重
    category_weights = request.category_weights or {}
    if not category_weights:
        # 默认权重
        category_weights = {cat: 1.0 for cat in items_by_category.keys()}

    # 归一化权重
    total_weight = sum(category_weights.values())
    category_probs = {cat: w / total_weight for cat, w in category_weights.items()}

    # 生成模拟订单
    orders = []
    now = time.time()
    for i in range(request.order_count):
        # 随机选择类别
        cat = random.choices(
            list(category_probs.keys()),
            weights=list(category_probs.values())
        )[0]

        # 从该类别随机选择商品
        if cat in items_by_category and items_by_category[cat]:
            item = random.choice(items_by_category[cat])

            # 随机历史时间戳
            days_ago = random.uniform(0, request.days_range)
            timestamp = now - (days_ago * 24 * 3600)

            # 随机客制化
            customization = {}
            if random.random() > 0.5:
                customization["cup_size"] = random.choice(["TALL", "GRANDE", "VENTI"])
            if random.random() > 0.5:
                customization["temperature"] = random.choice(["HOT", "ICED"])

            order = OrderRecord(
                user_id=request.user_id,
                item_sku=item.sku,
                item_name=item.name,
                category=item.category.value,
                tags=item.tags,
                base_price=item.base_price,
                final_price=item.base_price + random.randint(-3, 5),
                customization=customization if customization else None,
                timestamp=timestamp
            )
            orders.append(order)

    # 批量记录
    result = await behavior_service.batch_record_orders_async(orders)

    return {
        "status": "simulated",
        "user_id": request.user_id,
        "order_count": len(orders),
        "days_range": request.days_range,
        "category_distribution": {
            cat: sum(1 for o in orders if o.category == cat)
            for cat in set(o.category for o in orders if o.category)
        },
        "result": result
    }


@app.get("/api/orders/stats")
async def get_order_stats():
    """获取订单统计概览"""
    from app.experiment_service import behavior_service

    return await behavior_service.get_order_stats_async()


@app.get("/api/orders/boost/{user_id}/{item_sku}")
async def get_order_boost(user_id: str, item_sku: str):
    """获取特定用户对特定商品的订单权重加成（调试用）"""
    from app.experiment_service import behavior_service
    from app.data import get_menu_by_sku

    item = get_menu_by_sku(item_sku)
    if not item:
        return {"error": "商品不存在"}

    boost_detail = await behavior_service.get_order_based_recommendation_boost_async(
        user_id=user_id,
        item_sku=item_sku,
        item_category=item.category.value,
        item_tags=item.tags,
        item_price=item.base_price
    )

    return {
        "user_id": user_id,
        "item_sku": item_sku,
        "item_name": item.name,
        "boost_detail": boost_detail
    }


# ============ 预设API ============

class PresetCreateRequest(BaseModel):
    """创建预设请求"""
    user_id: str
    name: str
    default_temperature: Optional[str] = None
    default_cup_size: Optional[str] = None
    default_sugar_level: Optional[str] = None
    default_milk_type: Optional[str] = None
    extra_shot: bool = False
    whipped_cream: bool = False


class PresetUpdateRequest(BaseModel):
    """更新预设请求"""
    name: Optional[str] = None
    default_temperature: Optional[str] = None
    default_cup_size: Optional[str] = None
    default_sugar_level: Optional[str] = None
    default_milk_type: Optional[str] = None
    extra_shot: Optional[bool] = None
    whipped_cream: Optional[bool] = None


@app.post("/api/presets")
async def create_preset(request: PresetCreateRequest):
    """创建用户客制化预设"""
    from app.experiment_service import preset_service

    preset_data = {
        "user_id": request.user_id,
        "name": request.name,
        "default_temperature": request.default_temperature,
        "default_cup_size": request.default_cup_size,
        "default_sugar_level": request.default_sugar_level,
        "default_milk_type": request.default_milk_type,
        "extra_shot": request.extra_shot,
        "whipped_cream": request.whipped_cream
    }

    result = await preset_service.create_preset_async(preset_data)
    return result


@app.get("/api/presets/user/{user_id}")
async def get_user_presets(user_id: str):
    """获取用户的所有预设"""
    from app.experiment_service import preset_service

    presets = await preset_service.get_user_presets_async(user_id)
    return {
        "user_id": user_id,
        "preset_count": len(presets),
        "presets": presets
    }


@app.get("/api/presets/{preset_id}")
async def get_preset(preset_id: str):
    """获取单个预设详情"""
    from app.experiment_service import preset_service

    preset = await preset_service.get_preset_async(preset_id)
    if not preset:
        return {"status": "error", "message": "preset not found"}
    return {"preset": preset}


@app.put("/api/presets/{preset_id}")
async def update_preset(preset_id: str, request: PresetUpdateRequest):
    """更新预设"""
    from app.experiment_service import preset_service

    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    result = await preset_service.update_preset_async(preset_id, updates)
    return result


@app.delete("/api/presets/{preset_id}")
async def delete_preset(preset_id: str):
    """删除预设"""
    from app.experiment_service import preset_service

    result = await preset_service.delete_preset_async(preset_id)
    return result


@app.post("/api/presets/{preset_id}/apply/{item_sku}")
async def apply_preset_to_item(preset_id: str, item_sku: str):
    """将预设应用到商品，考虑商品约束"""
    from app.experiment_service import preset_service
    from app.data import get_menu_by_sku

    item = get_menu_by_sku(item_sku)
    if not item:
        return {"status": "error", "message": "商品不存在"}

    # 获取商品约束
    item_constraints = None
    if item.customization_constraints:
        item_constraints = item.customization_constraints.model_dump()

    result = await preset_service.apply_preset_to_item_async(
        preset_id,
        item_constraints,
        [t.value for t in item.available_temperatures],
        [s.value for s in item.available_sizes],
        item.base_price
    )

    if result.get("status") == "error":
        return result

    return {
        "item_sku": item_sku,
        "item_name": item.name,
        **result
    }


# ============ 增强版演示页面 ============

@app.get("/embedding-v2", response_class=HTMLResponse)
async def embedding_demo_v2(request: Request):
    """增强版Embedding推荐演示页面"""
    return templates.TemplateResponse("embedding_demo_v2.html", {"request": request})


@app.get("/presentation", response_class=HTMLResponse)
async def presentation(request: Request):
    """技术方案汇报PPT"""
    return templates.TemplateResponse("presentation.html", {"request": request})


# ============ 购物车API ============

@app.get("/api/cart/{session_id}")
async def get_cart(session_id: str):
    """获取购物车"""
    from app.cart_service import cart_service

    cart = await cart_service.get_cart_async(session_id)
    return cart.model_dump()


@app.post("/api/cart/add")
async def add_to_cart(request: dict):
    """添加商品到购物车"""
    from app.cart_service import cart_service
    from app.models import AddToCartRequest, Customization

    # 构建请求对象
    customization = None
    if request.get("customization"):
        customization = Customization(**request["customization"])

    add_request = AddToCartRequest(
        session_id=request["session_id"],
        user_id=request.get("user_id"),
        item_sku=request["item_sku"],
        quantity=request.get("quantity", 1),
        customization=customization
    )

    result = await cart_service.add_to_cart_async(add_request)
    return result


@app.put("/api/cart/item/{session_id}/{item_id}")
async def update_cart_item(session_id: str, item_id: str, request: dict):
    """更新购物车商品"""
    from app.cart_service import cart_service
    from app.models import UpdateCartItemRequest, Customization

    customization = None
    if request.get("customization"):
        customization = Customization(**request["customization"])

    update_request = UpdateCartItemRequest(
        quantity=request.get("quantity"),
        customization=customization
    )

    result = await cart_service.update_cart_item_async(session_id, item_id, update_request)
    return result


@app.delete("/api/cart/item/{session_id}/{item_id}")
async def remove_cart_item(session_id: str, item_id: str):
    """删除购物车商品"""
    from app.cart_service import cart_service

    result = await cart_service.remove_cart_item_async(session_id, item_id)
    return result


@app.delete("/api/cart/{session_id}")
async def clear_cart(session_id: str):
    """清空购物车"""
    from app.cart_service import cart_service

    result = await cart_service.clear_cart_async(session_id)
    return result


@app.post("/api/cart/checkout")
async def checkout_cart(request: dict):
    """结算购物车生成订单"""
    from app.cart_service import cart_service
    from app.models import CheckoutRequest

    checkout_request = CheckoutRequest(
        session_id=request["session_id"],
        user_id=request.get("user_id")
    )

    result = await cart_service.checkout_async(checkout_request)
    return result


@app.get("/api/cart/orders/{user_id}")
async def get_cart_orders(user_id: str, limit: int = 20):
    """获取用户订单历史"""
    from app.cart_service import cart_service

    orders = await cart_service.get_user_orders_async(user_id, limit)
    return {
        "user_id": user_id,
        "order_count": len(orders),
        "orders": orders
    }


@app.get("/api/cart/order/{order_id}")
async def get_order_detail(order_id: str):
    """获取订单详情"""
    from app.cart_service import cart_service

    order = await cart_service.get_order_async(order_id)
    if not order:
        return {"status": "error", "message": "订单不存在"}
    return {"status": "success", "order": order}


@app.get("/api/cart/stats")
async def get_cart_stats():
    """获取订单统计"""
    from app.cart_service import cart_service

    return await cart_service.get_order_stats_async()


# ============ 管理API ============

@app.post("/api/admin/migrate")
async def migrate_json_to_sqlite():
    """手动执行 JSON 到 SQLite 迁移"""
    from app.db import migrate_from_json
    result = await migrate_from_json()
    return {"status": "migrated", "result": result}
