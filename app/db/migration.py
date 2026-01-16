"""
JSON 到 SQLite 数据迁移

功能:
1. 读取现有 JSON 文件
2. 将数据导入 SQLite 表
3. 迁移状态追踪（避免重复迁移）
"""
import json
import time
from pathlib import Path
from typing import Any

from app.db.connection import get_db

# JSON 文件路径
DATA_DIR = Path(__file__).parent.parent / "data"

JSON_FILES = {
    "experiments": DATA_DIR / "experiments.json",
    "feedback": DATA_DIR / "user_feedback.json",
    "behavior": DATA_DIR / "user_behavior.json",
    "orders": DATA_DIR / "user_orders.json",
    "presets": DATA_DIR / "user_presets.json",
    "carts": DATA_DIR / "carts.json",
    "completed_orders": DATA_DIR / "completed_orders.json",
}


async def is_migrated(source: str) -> bool:
    """检查是否已迁移"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT 1 FROM migration_status WHERE source = ?",
        (source,)
    )
    row = await cursor.fetchone()
    return row is not None


async def mark_migrated(source: str) -> None:
    """标记迁移完成"""
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO migration_status (id, source, migrated_at, status) VALUES (?, ?, ?, ?)",
        (hash(source) % 2147483647, source, time.time(), "completed")
    )
    await db.commit()


def load_json_file(path: Path) -> Any:
    """安全加载 JSON 文件"""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Migration] 加载 {path} 失败: {e}")
        return None


async def migrate_experiments() -> int:
    """迁移实验配置"""
    if await is_migrated("experiments"):
        return 0

    data = load_json_file(JSON_FILES["experiments"])
    if not data:
        await mark_migrated("experiments")
        return 0

    db = await get_db()
    count = 0

    for exp_id, exp in data.items():
        # 插入实验
        await db.execute(
            """
            INSERT OR IGNORE INTO experiments (experiment_id, name, description, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                exp.get("experiment_id", exp_id),
                exp.get("name", ""),
                exp.get("description", ""),
                exp.get("status", "active"),
                exp.get("created_at", time.time())
            )
        )

        # 插入变体
        for variant in exp.get("variants", []):
            await db.execute(
                """
                INSERT OR IGNORE INTO experiment_variants (experiment_id, variant_id, name, weight)
                VALUES (?, ?, ?, ?)
                """,
                (
                    exp.get("experiment_id", exp_id),
                    variant.get("id", ""),
                    variant.get("name", ""),
                    variant.get("weight", 50)
                )
            )
        count += 1

    await db.commit()
    await mark_migrated("experiments")
    print(f"[Migration] 迁移实验配置: {count} 条")
    return count


async def migrate_feedback() -> int:
    """迁移用户反馈"""
    if await is_migrated("feedback"):
        return 0

    data = load_json_file(JSON_FILES["feedback"])
    if not data:
        await mark_migrated("feedback")
        return 0

    db = await get_db()
    count = 0

    # 迁移反馈记录
    for fb in data.get("feedbacks", []):
        context_json = json.dumps(fb.get("context")) if fb.get("context") else None
        await db.execute(
            """
            INSERT INTO user_feedback (user_id, session_id, item_sku, feedback_type, experiment_id, variant, context, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fb.get("user_id", ""),
                fb.get("session_id", ""),
                fb.get("item_sku", ""),
                fb.get("feedback_type", ""),
                fb.get("experiment_id"),
                fb.get("variant"),
                context_json,
                fb.get("timestamp", time.time())
            )
        )
        count += 1

    # 迁移统计数据
    for sku, stats in data.get("stats", {}).items():
        await db.execute(
            """
            INSERT OR REPLACE INTO feedback_stats (item_sku, likes, dislikes, clicks, orders)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                sku,
                stats.get("likes", 0),
                stats.get("dislikes", 0),
                stats.get("clicks", 0),
                stats.get("orders", 0)
            )
        )

    await db.commit()
    await mark_migrated("feedback")
    print(f"[Migration] 迁移用户反馈: {count} 条")
    return count


async def migrate_behavior() -> int:
    """迁移用户行为"""
    if await is_migrated("behavior"):
        return 0

    data = load_json_file(JSON_FILES["behavior"])
    if not data:
        await mark_migrated("behavior")
        return 0

    db = await get_db()
    count = 0

    # 迁移行为数据（users 结构）
    for user_id, user_data in data.get("users", {}).items():
        # 迁移各类行为
        for action_type in ["views", "clicks", "orders", "customizations"]:
            action_name = action_type.rstrip("s")  # views -> view
            if action_name == "customization":
                action_name = "customize"

            for record in user_data.get(action_type, []):
                details_json = json.dumps(record.get("details")) if record.get("details") else None
                await db.execute(
                    """
                    INSERT INTO user_behavior (user_id, session_id, action, item_sku, details, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        record.get("session_id", ""),
                        action_name,
                        record.get("sku", ""),
                        details_json,
                        record.get("timestamp", time.time())
                    )
                )
                count += 1

    await db.commit()
    await mark_migrated("behavior")
    print(f"[Migration] 迁移用户行为: {count} 条")
    return count


async def migrate_orders() -> int:
    """迁移订单记录"""
    if await is_migrated("orders"):
        return 0

    data = load_json_file(JSON_FILES["orders"])
    if not data:
        await mark_migrated("orders")
        return 0

    db = await get_db()
    count = 0

    # 迁移订单列表
    for order in data.get("orders", []):
        tags_json = json.dumps(order.get("tags")) if order.get("tags") else None
        customization_json = json.dumps(order.get("customization")) if order.get("customization") else None

        await db.execute(
            """
            INSERT OR IGNORE INTO orders (order_id, user_id, item_sku, item_name, category, tags, base_price, final_price, customization, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order.get("order_id", f"order_{int(time.time() * 1000)}_{count}"),
                order.get("user_id", ""),
                order.get("item_sku", ""),
                order.get("item_name"),
                order.get("category"),
                tags_json,
                order.get("base_price"),
                order.get("final_price"),
                customization_json,
                order.get("session_id"),
                order.get("timestamp", time.time())
            )
        )
        count += 1

    # 迁移统计数据
    for sku, stats in data.get("stats", {}).items():
        unique_users = stats.get("unique_users", [])
        if isinstance(unique_users, set):
            unique_users = list(unique_users)
        unique_users_json = json.dumps(unique_users)

        await db.execute(
            """
            INSERT OR REPLACE INTO order_stats (item_sku, total_orders, total_revenue, unique_users)
            VALUES (?, ?, ?, ?)
            """,
            (
                sku,
                stats.get("total_orders", 0),
                stats.get("total_revenue", 0.0),
                unique_users_json
            )
        )

    await db.commit()
    await mark_migrated("orders")
    print(f"[Migration] 迁移订单记录: {count} 条")
    return count


async def migrate_presets() -> int:
    """迁移用户预设"""
    if await is_migrated("presets"):
        return 0

    data = load_json_file(JSON_FILES["presets"])
    if not data:
        await mark_migrated("presets")
        return 0

    db = await get_db()
    count = 0

    # 迁移预设
    for preset_id, preset in data.get("presets", {}).items():
        await db.execute(
            """
            INSERT OR IGNORE INTO user_presets (preset_id, user_id, name, default_temperature, default_cup_size, default_sugar_level, default_milk_type, extra_shot, whipped_cream, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                preset.get("preset_id", preset_id),
                preset.get("user_id", ""),
                preset.get("name", "我的预设"),
                preset.get("default_temperature"),
                preset.get("default_cup_size"),
                preset.get("default_sugar_level"),
                preset.get("default_milk_type"),
                1 if preset.get("extra_shot") else 0,
                1 if preset.get("whipped_cream") else 0,
                preset.get("created_at", time.time()),
                preset.get("updated_at", time.time())
            )
        )
        count += 1

    await db.commit()
    await mark_migrated("presets")
    print(f"[Migration] 迁移用户预设: {count} 条")
    return count


async def migrate_carts() -> int:
    """迁移购物车"""
    if await is_migrated("carts"):
        return 0

    data = load_json_file(JSON_FILES["carts"])
    if not data:
        await mark_migrated("carts")
        return 0

    db = await get_db()
    count = 0

    for session_id, cart in data.items():
        # 插入购物车
        await db.execute(
            """
            INSERT OR IGNORE INTO carts (session_id, user_id, total_price, total_items, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                cart.get("user_id"),
                cart.get("total_price", 0.0),
                cart.get("total_items", 0),
                cart.get("created_at", time.time()),
                cart.get("updated_at", time.time())
            )
        )

        # 插入购物车商品
        for item in cart.get("items", []):
            customization_json = json.dumps(item.get("customization")) if item.get("customization") else None
            tags_json = json.dumps(item.get("tags")) if item.get("tags") else None

            await db.execute(
                """
                INSERT OR IGNORE INTO cart_items (id, session_id, item_sku, item_name, category, quantity, customization, unit_price, final_price, image_url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("id", ""),
                    session_id,
                    item.get("item_sku", ""),
                    item.get("item_name", ""),
                    item.get("category", ""),
                    item.get("quantity", 1),
                    customization_json,
                    item.get("unit_price", 0.0),
                    item.get("final_price", 0.0),
                    item.get("image_url"),
                    tags_json
                )
            )
        count += 1

    await db.commit()
    await mark_migrated("carts")
    print(f"[Migration] 迁移购物车: {count} 条")
    return count


async def migrate_completed_orders() -> int:
    """迁移完成订单"""
    if await is_migrated("completed_orders"):
        return 0

    data = load_json_file(JSON_FILES["completed_orders"])
    if not data:
        await mark_migrated("completed_orders")
        return 0

    db = await get_db()
    count = 0

    for order in data.get("orders", []):
        order_id = order.get("order_id", "")

        # 插入订单
        await db.execute(
            """
            INSERT OR IGNORE INTO completed_orders (order_id, user_id, session_id, total_price, total_items, status, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                order.get("user_id"),
                order.get("session_id", ""),
                order.get("total_price", 0.0),
                order.get("total_items", 0),
                order.get("status", "CONFIRMED"),
                order.get("created_at", time.time()),
                order.get("completed_at")
            )
        )

        # 插入订单商品
        for item in order.get("items", []):
            customization_json = json.dumps(item.get("customization")) if item.get("customization") else None
            tags_json = json.dumps(item.get("tags")) if item.get("tags") else None

            await db.execute(
                """
                INSERT INTO completed_order_items (order_id, item_sku, item_name, category, quantity, customization, unit_price, final_price, image_url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    item.get("item_sku", ""),
                    item.get("item_name", ""),
                    item.get("category", ""),
                    item.get("quantity", 1),
                    customization_json,
                    item.get("unit_price", 0.0),
                    item.get("final_price", 0.0),
                    item.get("image_url"),
                    tags_json
                )
            )
        count += 1

    await db.commit()
    await mark_migrated("completed_orders")
    print(f"[Migration] 迁移完成订单: {count} 条")
    return count


async def migrate_from_json() -> dict:
    """执行所有 JSON 到 SQLite 的迁移"""
    results = {}

    print("[Migration] 开始 JSON → SQLite 数据迁移...")

    results["experiments"] = await migrate_experiments()
    results["feedback"] = await migrate_feedback()
    results["behavior"] = await migrate_behavior()
    results["orders"] = await migrate_orders()
    results["presets"] = await migrate_presets()
    results["carts"] = await migrate_carts()
    results["completed_orders"] = await migrate_completed_orders()

    total = sum(results.values())
    print(f"[Migration] 迁移完成，共迁移 {total} 条记录")

    return results
