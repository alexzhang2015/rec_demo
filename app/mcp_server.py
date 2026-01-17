"""
AI点单推荐 MCP Server

提供给AI点单系统调用的商品推荐工具，基于 Model Context Protocol (MCP) 规范实现。

主要工具:
1. recommend_products - 智能商品推荐
2. get_user_preferences - 获取用户偏好
3. get_store_menu - 获取门店菜单

使用方式:
    uv run python -m app.mcp_server
"""

import asyncio
import json
import httpx
from typing import Optional
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# MCP Server 实例
server = Server("starbucks-ai-ordering")

# 推荐服务基础URL
RECOMMEND_API_BASE = "http://localhost:8000"


def get_current_time_period() -> str:
    """获取当前时段"""
    hour = datetime.now().hour
    if 6 <= hour < 11:
        return "morning"
    elif 11 <= hour < 14:
        return "lunch"
    elif 14 <= hour < 17:
        return "afternoon"
    else:
        return "evening"


def calculate_confidence(recommendation: dict) -> float:
    """
    计算推荐置信度

    基于以下因素:
    - 语义相似度得分
    - 历史行为匹配度
    - 上下文匹配度
    - 客制化匹配度
    """
    breakdown = recommendation.get("score_breakdown", {})

    # 基础语义相似度 (0-1)
    semantic_score = recommendation.get("similarity_score", 0.5)

    # 各因子权重
    weights = {
        "semantic": 0.35,
        "behavior": 0.25,
        "context": 0.20,
        "customization": 0.20
    }

    # 行为匹配度 (multiplier 转换为 0-1)
    behavior_mult = breakdown.get("behavior_multiplier", 1.0)
    behavior_score = min(1.0, (behavior_mult - 0.8) / 0.4) if behavior_mult > 0.8 else 0.5

    # 上下文匹配度
    context_factors = breakdown.get("context_factors", {})
    context_score = 0.5
    if context_factors:
        time_factor = context_factors.get("time_factor", {}).get("value", 1.0)
        weather_factor = context_factors.get("weather_factor", {}).get("value", 1.0)
        context_score = min(1.0, (time_factor + weather_factor - 1.6) / 0.8)

    # 客制化匹配度
    cust_mult = breakdown.get("customization_multiplier", 1.0)
    cust_score = min(1.0, (cust_mult - 0.8) / 0.4) if cust_mult > 0.8 else 0.5

    # 综合置信度
    confidence = (
        weights["semantic"] * semantic_score +
        weights["behavior"] * behavior_score +
        weights["context"] * context_score +
        weights["customization"] * cust_score
    )

    return round(min(1.0, max(0.0, confidence)), 3)


def apply_constraints(items: list, constraints: dict) -> list:
    """
    应用硬约束过滤

    支持的约束:
    - caffeine_free: 无咖啡因
    - low_calorie: 低卡 (<100卡)
    - dairy_free: 无乳制品
    - vegan: 纯素
    - max_price: 最高价格
    - categories: 指定品类列表
    - exclude_categories: 排除品类
    - temperature_only: 仅限温度 (hot/iced)
    """
    filtered = []

    for item in items:
        item_data = item.get("item", {})
        tags = [t.lower() for t in item_data.get("tags", [])]
        category = item_data.get("category", "").lower()
        calories = item_data.get("calories", 0)
        base_price = item_data.get("base_price", 0)
        available_temps = item_data.get("available_temperatures", [])

        # 无咖啡因约束
        if constraints.get("caffeine_free"):
            caffeine_tags = ["提神", "咖啡因", "espresso"]
            if any(t in " ".join(tags) for t in caffeine_tags):
                if category == "咖啡":
                    continue  # 咖啡类默认含咖啡因

        # 低卡约束
        if constraints.get("low_calorie") and calories >= 100:
            continue

        # 无乳制品约束
        if constraints.get("dairy_free"):
            dairy_tags = ["牛奶", "奶", "乳"]
            if any(t in item_data.get("name", "") for t in dairy_tags):
                continue

        # 最高价格约束
        max_price = constraints.get("max_price")
        if max_price and base_price > max_price:
            continue

        # 品类约束
        allowed_categories = constraints.get("categories")
        if allowed_categories and category not in [c.lower() for c in allowed_categories]:
            continue

        # 排除品类
        excluded_categories = constraints.get("exclude_categories")
        if excluded_categories and category in [c.lower() for c in excluded_categories]:
            continue

        # 温度约束
        temp_only = constraints.get("temperature_only")
        if temp_only:
            temp_map = {"hot": ["热", "特别热", "微热"], "iced": ["冰", "少冰", "去冰", "全冰"]}
            required_temps = temp_map.get(temp_only.lower(), [])
            if required_temps and not any(t in available_temps for t in required_temps):
                continue

        filtered.append(item)

    return filtered


def format_recommendation_for_ai(rec: dict, confidence: float) -> dict:
    """
    格式化推荐结果供AI点单使用
    """
    item = rec.get("item", {})
    suggested_cust = rec.get("suggested_customization", {})
    cust = suggested_cust.get("suggested_customization", {}) if suggested_cust else {}

    return {
        "product": {
            "sku": item.get("sku"),
            "name": item.get("name"),
            "english_name": item.get("english_name"),
            "category": item.get("category"),
            "base_price": item.get("base_price"),
            "calories": item.get("calories"),
            "description": item.get("description"),
            "tags": item.get("tags", []),
            "is_new": item.get("is_new", False),
            "is_seasonal": item.get("is_seasonal", False)
        },
        "customization": {
            "temperature": cust.get("temperature"),
            "cup_size": cust.get("cup_size"),
            "sugar_level": cust.get("sugar_level"),
            "milk_type": cust.get("milk_type"),
            "espresso_shots": cust.get("espresso_shots")
        },
        "pricing": {
            "base_price": item.get("base_price", 0),
            "customization_adjustment": suggested_cust.get("price_adjustment", 0) if suggested_cust else 0,
            "final_price": item.get("base_price", 0) + (suggested_cust.get("price_adjustment", 0) if suggested_cust else 0)
        },
        "recommendation_info": {
            "confidence": confidence,
            "confidence_level": "high" if confidence >= 0.7 else ("medium" if confidence >= 0.5 else "low"),
            "reason": rec.get("reason", ""),
            "reason_highlight": rec.get("reason_highlight", ""),
            "matched_keywords": rec.get("matched_keywords", []),
            "factors": {
                "semantic_similarity": rec.get("similarity_score", 0),
                "behavior_match": rec.get("score_breakdown", {}).get("behavior_multiplier", 1.0),
                "context_match": rec.get("score_breakdown", {}).get("context_multiplier", 1.0),
                "customization_match": rec.get("score_breakdown", {}).get("customization_multiplier", 1.0)
            }
        }
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的MCP工具"""
    return [
        Tool(
            name="recommend_products",
            description="""智能商品推荐工具 - 根据用户意图和上下文推荐星巴克饮品

适用场景:
- 用户说"来杯提神的" → 推荐咖啡类
- 用户说"有什么新品" → 推荐新品
- 用户说"适合减肥的" → 推荐低卡饮品
- 用户说"不要咖啡因" → 过滤无咖啡因饮品

返回包含:
- 推荐商品信息 (名称、价格、卡路里等)
- 推荐客制化配置 (温度、杯型、糖度等)
- 推荐置信度 (0-1)
- 推荐理由 (可直接用于AI回复)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "用户ID，用于获取历史偏好"
                    },
                    "query": {
                        "type": "string",
                        "description": "用户的自然语言描述，如'来杯提神的'、'有什么推荐'"
                    },
                    "store_id": {
                        "type": "string",
                        "description": "门店ID，用于获取库存和门店特色"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "硬约束条件",
                        "properties": {
                            "caffeine_free": {
                                "type": "boolean",
                                "description": "是否要求无咖啡因"
                            },
                            "low_calorie": {
                                "type": "boolean",
                                "description": "是否要求低卡(<100卡)"
                            },
                            "dairy_free": {
                                "type": "boolean",
                                "description": "是否要求无乳制品"
                            },
                            "max_price": {
                                "type": "number",
                                "description": "最高价格限制"
                            },
                            "categories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "限定品类，如['咖啡', '茶饮']"
                            },
                            "temperature_only": {
                                "type": "string",
                                "enum": ["hot", "iced"],
                                "description": "仅限温度类型"
                            }
                        }
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回推荐数量，默认2",
                        "default": 2
                    },
                    "context_override": {
                        "type": "object",
                        "description": "上下文覆盖 (可选)",
                        "properties": {
                            "time_period": {
                                "type": "string",
                                "enum": ["morning", "lunch", "afternoon", "evening"]
                            },
                            "weather": {
                                "type": "string",
                                "enum": ["hot", "cold", "rainy", "normal"]
                            }
                        }
                    }
                },
                "required": ["user_id", "query"]
            }
        ),
        Tool(
            name="get_user_preferences",
            description="""获取用户历史偏好 - 用于"老样子"、"上次那个"等场景

返回:
- 最近订单历史
- 高频商品
- 客制化偏好 (温度、糖度等)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "用户ID"
                    },
                    "preference_type": {
                        "type": "string",
                        "enum": ["recent_orders", "frequent_items", "customization_prefs", "all"],
                        "description": "偏好类型",
                        "default": "all"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_store_menu",
            description="""获取门店菜单 - 用于查询特定商品或浏览菜单

返回:
- 可售商品列表
- 库存状态
- 门店特色推荐""",
            inputSchema={
                "type": "object",
                "properties": {
                    "store_id": {
                        "type": "string",
                        "description": "门店ID"
                    },
                    "category": {
                        "type": "string",
                        "description": "筛选品类，如'咖啡'、'茶饮'"
                    },
                    "search_keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""

    if name == "recommend_products":
        return await handle_recommend_products(arguments)
    elif name == "get_user_preferences":
        return await handle_get_user_preferences(arguments)
    elif name == "get_store_menu":
        return await handle_get_store_menu(arguments)
    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False))]


async def handle_recommend_products(args: dict) -> list[TextContent]:
    """处理商品推荐请求"""
    user_id = args.get("user_id", "anonymous")
    query = args.get("query", "")
    store_id = args.get("store_id")
    constraints = args.get("constraints", {})
    top_k = args.get("top_k", 2)
    context_override = args.get("context_override", {})

    # 构建推荐API请求
    request_data = {
        "persona_type": "咖啡重度用户",  # 默认画像，会被query覆盖
        "user_id": user_id,
        "search_query": query,
        "top_k": max(top_k + 3, 6),  # 多请求一些用于约束过滤
        "enable_ab_test": True,
        "enable_behavior": True,
        "enable_session": True,
        "enable_context": True,
        "enable_explainability": True,
        "use_llm_for_reasons": True
    }

    # 添加门店信息
    if store_id:
        request_data["store_id"] = store_id

    # 添加上下文覆盖
    context = {}
    if context_override.get("time_period"):
        context["time_period"] = context_override["time_period"]
    if context_override.get("weather"):
        weather_map = {
            "hot": {"temperature": 32, "condition": "hot"},
            "cold": {"temperature": 5, "condition": "cold"},
            "rainy": {"temperature": 18, "condition": "rainy"},
            "normal": {"temperature": 22, "condition": "normal"}
        }
        context["weather"] = weather_map.get(context_override["weather"], weather_map["normal"])

    if context:
        request_data["context"] = context

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{RECOMMEND_API_BASE}/api/embedding/recommend/v2",
                json=request_data
            )
            response.raise_for_status()
            result = response.json()
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": f"推荐服务调用失败: {str(e)}",
            "fallback_suggestion": "建议询问用户更具体的需求"
        }, ensure_ascii=False, indent=2))]

    # 获取推荐结果
    recommendations = result.get("recommendations", [])

    # 应用硬约束过滤
    if constraints:
        recommendations = apply_constraints(recommendations, constraints)

    # 限制返回数量
    recommendations = recommendations[:top_k]

    # 格式化结果
    formatted_recommendations = []
    for rec in recommendations:
        confidence = calculate_confidence(rec)
        formatted = format_recommendation_for_ai(rec, confidence)
        formatted_recommendations.append(formatted)

    # 判断是否需要澄清
    need_clarification = False
    clarification_options = []

    if not formatted_recommendations:
        need_clarification = True
        clarification_options = [
            "您想喝咖啡还是茶饮？",
            "您有什么口味偏好吗？",
            "您对价格有要求吗？"
        ]
    elif len(formatted_recommendations) > 0:
        top_confidence = formatted_recommendations[0]["recommendation_info"]["confidence"]
        if top_confidence < 0.5:
            need_clarification = True
            clarification_options = [
                "您能描述得更具体一些吗？",
                "您平时喜欢喝什么类型的饮品？"
            ]

    # 构建响应
    response_data = {
        "success": True,
        "recommendations": formatted_recommendations,
        "meta": {
            "total_candidates": len(result.get("recommendations", [])),
            "filtered_count": len(formatted_recommendations),
            "constraints_applied": list(constraints.keys()) if constraints else [],
            "context": {
                "time_period": context_override.get("time_period") or get_current_time_period(),
                "store_id": store_id
            }
        },
        "need_clarification": need_clarification,
        "clarification_options": clarification_options,
        "suggested_response": generate_suggested_response(formatted_recommendations, need_clarification)
    }

    return [TextContent(type="text", text=json.dumps(response_data, ensure_ascii=False, indent=2))]


def generate_suggested_response(recommendations: list, need_clarification: bool) -> str:
    """生成建议的AI回复"""
    if need_clarification:
        return "我还不太确定您想要什么，能告诉我更多吗？比如您喜欢咖啡还是茶饮？"

    if not recommendations:
        return "抱歉，暂时没有找到符合您要求的饮品。您可以换个描述试试？"

    top_rec = recommendations[0]
    product = top_rec["product"]
    cust = top_rec["customization"]
    pricing = top_rec["pricing"]
    info = top_rec["recommendation_info"]

    # 构建基础推荐
    response = f"为您推荐{product['name']}"

    # 添加客制化
    cust_parts = []
    if cust.get("temperature"):
        cust_parts.append(cust["temperature"])
    if cust.get("cup_size"):
        size_map = {"TALL": "中杯", "GRANDE": "大杯", "VENTI": "超大杯"}
        cust_parts.append(size_map.get(cust["cup_size"], cust["cup_size"]))

    if cust_parts:
        response += f"，{'/'.join(cust_parts)}"

    # 添加价格
    response += f"，{pricing['final_price']}元"

    # 添加理由
    if info.get("reason"):
        response += f"。{info['reason']}"

    # 如果有备选
    if len(recommendations) > 1:
        alt = recommendations[1]["product"]["name"]
        response += f" 或者您也可以试试{alt}~"

    return response


async def handle_get_user_preferences(args: dict) -> list[TextContent]:
    """处理用户偏好查询"""
    user_id = args.get("user_id")
    preference_type = args.get("preference_type", "all")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 获取用户行为数据
            response = await client.get(
                f"{RECOMMEND_API_BASE}/api/behavior/{user_id}"
            )

            if response.status_code == 404:
                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "is_new_user": True,
                    "preferences": {},
                    "message": "新用户，暂无历史偏好"
                }, ensure_ascii=False, indent=2))]

            response.raise_for_status()
            behavior_data = response.json()

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": f"获取用户偏好失败: {str(e)}"
        }, ensure_ascii=False, indent=2))]

    result = {
        "success": True,
        "user_id": user_id,
        "is_new_user": behavior_data.get("is_new_user", True)
    }

    if preference_type in ["recent_orders", "all"]:
        result["recent_orders"] = behavior_data.get("recent_orders", [])[:5]

    if preference_type in ["frequent_items", "all"]:
        result["frequent_items"] = behavior_data.get("top_items", [])[:5]

    if preference_type in ["customization_prefs", "all"]:
        result["customization_preferences"] = behavior_data.get("customization_preference", {})

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def handle_get_store_menu(args: dict) -> list[TextContent]:
    """处理门店菜单查询"""
    store_id = args.get("store_id")
    category = args.get("category")
    search_keyword = args.get("search_keyword")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 获取菜单
            params = {}
            if category:
                params["category"] = category

            response = await client.get(
                f"{RECOMMEND_API_BASE}/api/menu",
                params=params
            )
            response.raise_for_status()
            menu_data = response.json()

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": f"获取菜单失败: {str(e)}"
        }, ensure_ascii=False, indent=2))]

    items = menu_data.get("items", [])

    # 关键词搜索
    if search_keyword:
        keyword_lower = search_keyword.lower()
        items = [
            item for item in items
            if keyword_lower in item.get("name", "").lower()
            or keyword_lower in item.get("description", "").lower()
            or any(keyword_lower in tag.lower() for tag in item.get("tags", []))
        ]

    # 获取门店库存 (如果有store_id)
    inventory = {}
    if store_id:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                inv_response = await client.get(
                    f"{RECOMMEND_API_BASE}/api/stores/{store_id}"
                )
                if inv_response.status_code == 200:
                    store_data = inv_response.json()
                    inventory = store_data.get("inventory", {})
        except:
            pass

    # 添加库存信息
    for item in items:
        sku = item.get("sku")
        if inventory:
            item["stock_status"] = inventory.get(sku, "unknown")
        else:
            item["stock_status"] = "available"

    result = {
        "success": True,
        "store_id": store_id,
        "total_items": len(items),
        "items": items,
        "categories": list(set(item.get("category") for item in items if item.get("category")))
    }

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    """启动MCP服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
