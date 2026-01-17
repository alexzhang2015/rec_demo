"""
购物车服务

功能:
1. 购物车管理 - 添加/删除/更新商品
2. 价格计算 - 含客制化的价格计算
3. 订单生成 - 购物车转订单
4. 数据持久化 - SQLite存储

数据存储: SQLite (app/data/recommendation.db)
"""
import json
import time
import random
import asyncio
from pathlib import Path
from typing import Optional

from app.models import (
    Cart, CartItem, CompletedOrder, OrderStatus,
    Customization, CupSize, MilkType,
    AddToCartRequest, UpdateCartItemRequest, CheckoutRequest
)
from app.data import get_menu_by_sku
from app.db.connection import get_db

# 数据存储路径（保留用于向后兼容）
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


class CartService:
    """购物车服务"""

    def __init__(self):
        pass

    def _calculate_item_price(self, base_price: float, customization: Optional[Customization]) -> float:
        """计算含客制化的商品单价"""
        price = base_price

        if customization:
            # 杯型加价
            if customization.cup_size == CupSize.VENTI:
                price += 4
            elif customization.cup_size == CupSize.TALL:
                price -= 3

            # 额外浓缩加价 (默认2份，多于2份则加价)
            if customization.espresso_shots > 2:
                price += 4 * (customization.espresso_shots - 2)

            # 特殊奶类加价
            if customization.milk_type in [MilkType.OAT, MilkType.COCONUT]:
                price += 3

            # 无糖风味糖浆加价
            if customization.sugar_free_flavor:
                price += 3

        return price

    def _generate_cart_item_id(self) -> str:
        """生成购物车项ID"""
        return f"cart_item_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

    def _generate_order_id(self) -> str:
        """生成订单ID"""
        return f"ORD{int(time.time())}{random.randint(100, 999)}"

    async def _recalculate_cart_totals_async(self, session_id: str) -> dict:
        """重新计算购物车总计（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT final_price, quantity FROM cart_items WHERE session_id = ?",
            (session_id,)
        )
        rows = await cursor.fetchall()

        total_price = 0.0
        total_items = 0
        for row in rows:
            total_price += row["final_price"] * row["quantity"]
            total_items += row["quantity"]

        await db.execute(
            "UPDATE carts SET total_price = ?, total_items = ?, updated_at = ? WHERE session_id = ?",
            (round(total_price, 2), total_items, time.time(), session_id)
        )
        await db.commit()

        return {"total_price": round(total_price, 2), "total_items": total_items}

    async def get_cart_async(self, session_id: str) -> Cart:
        """获取购物车（异步版本）"""
        db = await get_db()

        # 检查购物车是否存在
        cursor = await db.execute(
            "SELECT * FROM carts WHERE session_id = ?",
            (session_id,)
        )
        cart_row = await cursor.fetchone()

        now = time.time()
        if not cart_row:
            # 创建新购物车
            await db.execute(
                """
                INSERT INTO carts (session_id, user_id, total_price, total_items, created_at, updated_at)
                VALUES (?, NULL, 0.0, 0, ?, ?)
                """,
                (session_id, now, now)
            )
            await db.commit()
            cart_data = {
                "session_id": session_id,
                "user_id": None,
                "items": [],
                "total_price": 0.0,
                "total_items": 0,
                "created_at": now,
                "updated_at": now
            }
        else:
            # 获取购物车商品
            cursor = await db.execute(
                "SELECT * FROM cart_items WHERE session_id = ?",
                (session_id,)
            )
            item_rows = await cursor.fetchall()

            items = []
            for row in item_rows:
                item = {
                    "id": row["id"],
                    "item_sku": row["item_sku"],
                    "item_name": row["item_name"],
                    "category": row["category"],
                    "quantity": row["quantity"],
                    "customization": json.loads(row["customization"]) if row["customization"] else None,
                    "unit_price": row["unit_price"],
                    "final_price": row["final_price"],
                    "image_url": row["image_url"],
                    "tags": json.loads(row["tags"]) if row["tags"] else []
                }
                items.append(item)

            cart_data = {
                "session_id": cart_row["session_id"],
                "user_id": cart_row["user_id"],
                "items": items,
                "total_price": cart_row["total_price"],
                "total_items": cart_row["total_items"],
                "created_at": cart_row["created_at"],
                "updated_at": cart_row["updated_at"]
            }

        return Cart(**cart_data)

    def get_cart(self, session_id: str) -> Cart:
        """获取购物车（同步版本）"""
        try:
            asyncio.get_running_loop()
            # 在异步上下文中返回空购物车
            return Cart(
                session_id=session_id,
                user_id=None,
                items=[],
                total_price=0.0,
                total_items=0,
                created_at=time.time(),
                updated_at=time.time()
            )
        except RuntimeError:
            return asyncio.run(self.get_cart_async(session_id))

    async def add_to_cart_async(self, request: AddToCartRequest) -> dict:
        """添加商品到购物车（异步版本）"""
        # 获取商品信息
        menu_item = get_menu_by_sku(request.item_sku)
        if not menu_item:
            return {"status": "error", "message": "商品不存在"}

        db = await get_db()

        # 确保购物车存在
        await self.get_cart_async(request.session_id)

        # 更新用户ID
        if request.user_id:
            await db.execute(
                "UPDATE carts SET user_id = ? WHERE session_id = ?",
                (request.user_id, request.session_id)
            )

        # 计算价格
        customization = request.customization
        final_price = self._calculate_item_price(menu_item.base_price, customization)
        customization_dict = customization.model_dump() if customization else None
        customization_json = json.dumps(customization_dict) if customization_dict else None

        # 检查是否已有相同商品和客制化
        cursor = await db.execute(
            "SELECT id, quantity FROM cart_items WHERE session_id = ? AND item_sku = ?",
            (request.session_id, request.item_sku)
        )
        rows = await cursor.fetchall()

        existing_item = None
        for row in rows:
            # 需要比较客制化
            cursor2 = await db.execute(
                "SELECT customization FROM cart_items WHERE id = ?",
                (row["id"],)
            )
            item_row = await cursor2.fetchone()
            item_customization = json.loads(item_row["customization"]) if item_row["customization"] else None
            if item_customization == customization_dict:
                existing_item = row
                break

        if existing_item:
            # 增加数量
            new_quantity = existing_item["quantity"] + request.quantity
            await db.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (new_quantity, existing_item["id"])
            )
        else:
            # 添加新项
            item_id = self._generate_cart_item_id()
            tags_json = json.dumps(menu_item.tags) if menu_item.tags else None

            await db.execute(
                """
                INSERT INTO cart_items (id, session_id, item_sku, item_name, category, quantity, customization, unit_price, final_price, image_url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    request.session_id,
                    menu_item.sku,
                    menu_item.name,
                    menu_item.category.value,
                    request.quantity,
                    customization_json,
                    menu_item.base_price,
                    final_price,
                    menu_item.image_url,
                    tags_json
                )
            )

        await db.commit()

        # 重新计算总计
        await self._recalculate_cart_totals_async(request.session_id)

        # 获取更新后的购物车
        cart = await self.get_cart_async(request.session_id)

        return {
            "status": "added",
            "cart": cart.model_dump(),
            "message": f"已添加 {menu_item.name} x{request.quantity}"
        }

    def add_to_cart(self, request: AddToCartRequest) -> dict:
        """添加商品到购物车（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.add_to_cart_async(request))

    async def update_cart_item_async(self, session_id: str, item_id: str, request: UpdateCartItemRequest) -> dict:
        """更新购物车商品（异步版本）"""
        db = await get_db()

        # 检查商品是否存在
        cursor = await db.execute(
            "SELECT * FROM cart_items WHERE session_id = ? AND id = ?",
            (session_id, item_id)
        )
        item_row = await cursor.fetchone()

        if not item_row:
            return {"status": "error", "message": "商品不在购物车中"}

        # 更新数量
        if request.quantity is not None:
            if request.quantity <= 0:
                # 删除商品
                await db.execute(
                    "DELETE FROM cart_items WHERE id = ?",
                    (item_id,)
                )
            else:
                await db.execute(
                    "UPDATE cart_items SET quantity = ? WHERE id = ?",
                    (request.quantity, item_id)
                )

        # 更新客制化
        if request.customization is not None:
            menu_item = get_menu_by_sku(item_row["item_sku"])
            if menu_item:
                customization_json = json.dumps(request.customization.model_dump())
                new_final_price = self._calculate_item_price(menu_item.base_price, request.customization)
                await db.execute(
                    "UPDATE cart_items SET customization = ?, final_price = ? WHERE id = ?",
                    (customization_json, new_final_price, item_id)
                )

        await db.commit()

        # 重新计算总计
        await self._recalculate_cart_totals_async(session_id)

        # 获取更新后的购物车
        cart = await self.get_cart_async(session_id)

        return {
            "status": "updated",
            "cart": cart.model_dump()
        }

    def update_cart_item(self, session_id: str, item_id: str, request: UpdateCartItemRequest) -> dict:
        """更新购物车商品（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.update_cart_item_async(session_id, item_id, request))

    async def remove_cart_item_async(self, session_id: str, item_id: str) -> dict:
        """删除购物车商品（异步版本）"""
        db = await get_db()

        # 检查商品是否存在
        cursor = await db.execute(
            "SELECT 1 FROM cart_items WHERE session_id = ? AND id = ?",
            (session_id, item_id)
        )
        if not await cursor.fetchone():
            return {"status": "error", "message": "商品不在购物车中"}

        # 删除商品
        await db.execute(
            "DELETE FROM cart_items WHERE id = ?",
            (item_id,)
        )
        await db.commit()

        # 重新计算总计
        await self._recalculate_cart_totals_async(session_id)

        # 获取更新后的购物车
        cart = await self.get_cart_async(session_id)

        return {
            "status": "removed",
            "cart": cart.model_dump()
        }

    def remove_cart_item(self, session_id: str, item_id: str) -> dict:
        """删除购物车商品（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.remove_cart_item_async(session_id, item_id))

    async def clear_cart_async(self, session_id: str) -> dict:
        """清空购物车（异步版本）"""
        db = await get_db()

        # 删除所有商品
        await db.execute(
            "DELETE FROM cart_items WHERE session_id = ?",
            (session_id,)
        )

        # 重置总计
        await db.execute(
            "UPDATE carts SET total_price = 0.0, total_items = 0, updated_at = ? WHERE session_id = ?",
            (time.time(), session_id)
        )
        await db.commit()

        # 获取更新后的购物车
        cart = await self.get_cart_async(session_id)

        return {
            "status": "cleared",
            "cart": cart.model_dump()
        }

    def clear_cart(self, session_id: str) -> dict:
        """清空购物车（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.clear_cart_async(session_id))

    async def checkout_async(self, request: CheckoutRequest) -> dict:
        """结算购物车生成订单（异步版本）"""
        db = await get_db()

        # 获取购物车
        cart = await self.get_cart_async(request.session_id)

        if not cart.items:
            return {"status": "error", "message": "购物车为空"}

        # 创建订单
        now = time.time()
        order_id = self._generate_order_id()
        user_id = request.user_id or cart.user_id

        await db.execute(
            """
            INSERT INTO completed_orders (order_id, user_id, session_id, total_price, total_items, status, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                order_id,
                user_id,
                request.session_id,
                cart.total_price,
                cart.total_items,
                OrderStatus.CONFIRMED.value,
                now
            )
        )

        # 插入订单商品
        for item in cart.items:
            customization_json = json.dumps(item.customization) if item.customization else None
            tags_json = json.dumps(item.tags) if item.tags else None

            await db.execute(
                """
                INSERT INTO completed_order_items (order_id, item_sku, item_name, category, quantity, customization, unit_price, final_price, image_url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    item.item_sku,
                    item.item_name,
                    item.category,
                    item.quantity,
                    customization_json,
                    item.unit_price,
                    item.final_price,
                    item.image_url,
                    tags_json
                )
            )

        await db.commit()

        # 清空购物车
        await self.clear_cart_async(request.session_id)

        # 构建订单响应
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "session_id": request.session_id,
            "items": [item.model_dump() for item in cart.items],
            "total_price": cart.total_price,
            "total_items": cart.total_items,
            "status": OrderStatus.CONFIRMED.value,
            "created_at": now,
            "completed_at": None
        }

        # 同步到行为服务
        await self._sync_order_to_behavior_async(order)

        return {
            "status": "success",
            "order_id": order_id,
            "order": order,
            "message": f"订单 {order_id} 已创建"
        }

    def checkout(self, request: CheckoutRequest) -> dict:
        """结算购物车生成订单（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"status": "pending"}
        except RuntimeError:
            return asyncio.run(self.checkout_async(request))

    async def _sync_order_to_behavior_async(self, order: dict):
        """同步订单到行为服务（异步版本）"""
        try:
            from app.experiment_service import behavior_service, OrderRecord

            for item in order["items"]:
                customization = item.get("customization")
                order_record = OrderRecord(
                    user_id=order["user_id"] or f"guest_{order['session_id'][:8]}",
                    item_sku=item["item_sku"],
                    item_name=item["item_name"],
                    category=item["category"],
                    tags=item.get("tags", []),
                    base_price=item["unit_price"],
                    final_price=item["final_price"] * item["quantity"],
                    customization=customization,
                    session_id=order["session_id"],
                    timestamp=order["created_at"]
                )
                await behavior_service.record_order_async(order_record)
        except Exception as e:
            print(f"同步订单到行为服务失败: {e}")

    def _sync_order_to_behavior(self, order: dict):
        """同步订单到行为服务（同步版本）"""
        try:
            asyncio.get_running_loop()
            pass
        except RuntimeError:
            asyncio.run(self._sync_order_to_behavior_async(order))

    async def get_user_orders_async(self, user_id: str, limit: int = 20) -> list[dict]:
        """获取用户订单历史（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            """
            SELECT * FROM completed_orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        order_rows = await cursor.fetchall()

        orders = []
        for order_row in order_rows:
            # 获取订单商品
            cursor = await db.execute(
                "SELECT * FROM completed_order_items WHERE order_id = ?",
                (order_row["order_id"],)
            )
            item_rows = await cursor.fetchall()

            items = []
            for item_row in item_rows:
                item = {
                    "item_sku": item_row["item_sku"],
                    "item_name": item_row["item_name"],
                    "category": item_row["category"],
                    "quantity": item_row["quantity"],
                    "customization": json.loads(item_row["customization"]) if item_row["customization"] else None,
                    "unit_price": item_row["unit_price"],
                    "final_price": item_row["final_price"],
                    "image_url": item_row["image_url"],
                    "tags": json.loads(item_row["tags"]) if item_row["tags"] else []
                }
                items.append(item)

            order = {
                "order_id": order_row["order_id"],
                "user_id": order_row["user_id"],
                "session_id": order_row["session_id"],
                "items": items,
                "total_price": order_row["total_price"],
                "total_items": order_row["total_items"],
                "status": order_row["status"],
                "created_at": order_row["created_at"],
                "completed_at": order_row["completed_at"]
            }
            orders.append(order)

        return orders

    def get_user_orders(self, user_id: str, limit: int = 20) -> list[dict]:
        """获取用户订单历史（同步版本）"""
        try:
            asyncio.get_running_loop()
            return []
        except RuntimeError:
            return asyncio.run(self.get_user_orders_async(user_id, limit))

    async def get_order_async(self, order_id: str) -> Optional[dict]:
        """获取单个订单（异步版本）"""
        db = await get_db()

        cursor = await db.execute(
            "SELECT * FROM completed_orders WHERE order_id = ?",
            (order_id,)
        )
        order_row = await cursor.fetchone()

        if not order_row:
            return None

        # 获取订单商品
        cursor = await db.execute(
            "SELECT * FROM completed_order_items WHERE order_id = ?",
            (order_id,)
        )
        item_rows = await cursor.fetchall()

        items = []
        for item_row in item_rows:
            item = {
                "item_sku": item_row["item_sku"],
                "item_name": item_row["item_name"],
                "category": item_row["category"],
                "quantity": item_row["quantity"],
                "customization": json.loads(item_row["customization"]) if item_row["customization"] else None,
                "unit_price": item_row["unit_price"],
                "final_price": item_row["final_price"],
                "image_url": item_row["image_url"],
                "tags": json.loads(item_row["tags"]) if item_row["tags"] else []
            }
            items.append(item)

        return {
            "order_id": order_row["order_id"],
            "user_id": order_row["user_id"],
            "session_id": order_row["session_id"],
            "items": items,
            "total_price": order_row["total_price"],
            "total_items": order_row["total_items"],
            "status": order_row["status"],
            "created_at": order_row["created_at"],
            "completed_at": order_row["completed_at"]
        }

    def get_order(self, order_id: str) -> Optional[dict]:
        """获取单个订单（同步版本）"""
        try:
            asyncio.get_running_loop()
            return None
        except RuntimeError:
            return asyncio.run(self.get_order_async(order_id))

    async def get_order_stats_async(self) -> dict:
        """获取订单统计（异步版本）"""
        db = await get_db()

        cursor = await db.execute("SELECT COUNT(*) as count FROM completed_orders")
        total_orders = (await cursor.fetchone())["count"]

        cursor = await db.execute("SELECT SUM(total_price) as total FROM completed_orders")
        row = await cursor.fetchone()
        total_revenue = row["total"] if row["total"] else 0.0

        cursor = await db.execute("SELECT SUM(total_items) as total FROM completed_orders")
        row = await cursor.fetchone()
        total_items = row["total"] if row["total"] else 0

        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) as count FROM completed_orders WHERE user_id IS NOT NULL")
        unique_users = (await cursor.fetchone())["count"]

        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "total_items_sold": total_items,
            "unique_users": unique_users
        }

    def get_order_stats(self) -> dict:
        """获取订单统计（同步版本）"""
        try:
            asyncio.get_running_loop()
            return {"total_orders": 0, "total_revenue": 0.0, "total_items_sold": 0, "unique_users": 0}
        except RuntimeError:
            return asyncio.run(self.get_order_stats_async())


# 单例实例
cart_service = CartService()
