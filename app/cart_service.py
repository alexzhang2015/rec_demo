"""
购物车服务

功能:
1. 购物车管理 - 添加/删除/更新商品
2. 价格计算 - 含客制化的价格计算
3. 订单生成 - 购物车转订单
4. 数据持久化 - JSON文件存储
"""
import json
import time
import random
from pathlib import Path
from typing import Optional

from app.models import (
    Cart, CartItem, CompletedOrder, OrderStatus,
    Customization, CupSize, MilkType,
    AddToCartRequest, UpdateCartItemRequest, CheckoutRequest
)
from app.data import get_menu_by_sku

# 数据存储路径
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CART_FILE = DATA_DIR / "carts.json"
ORDER_FILE = DATA_DIR / "completed_orders.json"


class CartService:
    """购物车服务"""

    def __init__(self):
        self.carts = self._load_carts()
        self.orders = self._load_orders()

    def _load_carts(self) -> dict:
        """加载购物车数据"""
        if CART_FILE.exists():
            try:
                with open(CART_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _load_orders(self) -> dict:
        """加载订单数据"""
        if ORDER_FILE.exists():
            try:
                with open(ORDER_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"orders": [], "user_index": {}}

    def _save_carts(self):
        """保存购物车数据"""
        with open(CART_FILE, "w") as f:
            json.dump(self.carts, f, ensure_ascii=False, indent=2)

    def _save_orders(self):
        """保存订单数据"""
        with open(ORDER_FILE, "w") as f:
            json.dump(self.orders, f, ensure_ascii=False, indent=2)

    def _calculate_item_price(self, base_price: float, customization: Optional[Customization]) -> float:
        """计算含客制化的商品单价"""
        price = base_price

        if customization:
            # 杯型加价
            if customization.cup_size == CupSize.VENTI:
                price += 4
            elif customization.cup_size == CupSize.TALL:
                price -= 3

            # 额外选项加价
            if customization.extra_shot:
                price += 4

            # 特殊奶类加价
            if customization.milk_type in [MilkType.OAT, MilkType.COCONUT]:
                price += 3

            # 糖浆加价
            if customization.syrup:
                price += 3

        return price

    def _generate_cart_item_id(self) -> str:
        """生成购物车项ID"""
        return f"cart_item_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

    def _generate_order_id(self) -> str:
        """生成订单ID"""
        return f"ORD{int(time.time())}{random.randint(100, 999)}"

    def _recalculate_cart_totals(self, cart: dict) -> dict:
        """重新计算购物车总计"""
        total_price = 0.0
        total_items = 0

        for item in cart["items"]:
            item_total = item["final_price"] * item["quantity"]
            total_price += item_total
            total_items += item["quantity"]

        cart["total_price"] = round(total_price, 2)
        cart["total_items"] = total_items
        cart["updated_at"] = time.time()

        return cart

    def get_cart(self, session_id: str) -> Cart:
        """获取购物车"""
        if session_id not in self.carts:
            # 创建新购物车
            now = time.time()
            self.carts[session_id] = {
                "session_id": session_id,
                "user_id": None,
                "items": [],
                "total_price": 0.0,
                "total_items": 0,
                "created_at": now,
                "updated_at": now
            }
            self._save_carts()

        cart_data = self.carts[session_id]
        return Cart(**cart_data)

    def add_to_cart(self, request: AddToCartRequest) -> dict:
        """添加商品到购物车"""
        # 获取商品信息
        menu_item = get_menu_by_sku(request.item_sku)
        if not menu_item:
            return {"status": "error", "message": "商品不存在"}

        # 获取或创建购物车
        cart = self.get_cart(request.session_id)
        cart_data = self.carts[request.session_id]

        # 更新用户ID
        if request.user_id:
            cart_data["user_id"] = request.user_id

        # 计算价格
        customization = request.customization
        final_price = self._calculate_item_price(menu_item.base_price, customization)

        # 检查是否已有相同商品和客制化
        existing_item = None
        customization_dict = customization.model_dump() if customization else None

        for item in cart_data["items"]:
            item_customization = item.get("customization")
            if item["item_sku"] == request.item_sku:
                if item_customization == customization_dict:
                    existing_item = item
                    break

        if existing_item:
            # 增加数量
            existing_item["quantity"] += request.quantity
        else:
            # 添加新项
            new_item = {
                "id": self._generate_cart_item_id(),
                "item_sku": menu_item.sku,
                "item_name": menu_item.name,
                "category": menu_item.category.value,
                "quantity": request.quantity,
                "customization": customization_dict,
                "unit_price": menu_item.base_price,
                "final_price": final_price,
                "image_url": menu_item.image_url,
                "tags": menu_item.tags
            }
            cart_data["items"].append(new_item)

        # 重新计算总计
        self._recalculate_cart_totals(cart_data)
        self._save_carts()

        return {
            "status": "added",
            "cart": Cart(**cart_data).model_dump(),
            "message": f"已添加 {menu_item.name} x{request.quantity}"
        }

    def update_cart_item(self, session_id: str, item_id: str, request: UpdateCartItemRequest) -> dict:
        """更新购物车商品"""
        if session_id not in self.carts:
            return {"status": "error", "message": "购物车不存在"}

        cart_data = self.carts[session_id]

        # 查找商品
        item_found = None
        for item in cart_data["items"]:
            if item["id"] == item_id:
                item_found = item
                break

        if not item_found:
            return {"status": "error", "message": "商品不在购物车中"}

        # 更新数量
        if request.quantity is not None:
            if request.quantity <= 0:
                # 删除商品
                cart_data["items"] = [i for i in cart_data["items"] if i["id"] != item_id]
            else:
                item_found["quantity"] = request.quantity

        # 更新客制化
        if request.customization is not None:
            menu_item = get_menu_by_sku(item_found["item_sku"])
            if menu_item:
                item_found["customization"] = request.customization.model_dump()
                item_found["final_price"] = self._calculate_item_price(
                    menu_item.base_price, request.customization
                )

        # 重新计算总计
        self._recalculate_cart_totals(cart_data)
        self._save_carts()

        return {
            "status": "updated",
            "cart": Cart(**cart_data).model_dump()
        }

    def remove_cart_item(self, session_id: str, item_id: str) -> dict:
        """删除购物车商品"""
        if session_id not in self.carts:
            return {"status": "error", "message": "购物车不存在"}

        cart_data = self.carts[session_id]

        # 查找并删除商品
        original_count = len(cart_data["items"])
        cart_data["items"] = [i for i in cart_data["items"] if i["id"] != item_id]

        if len(cart_data["items"]) == original_count:
            return {"status": "error", "message": "商品不在购物车中"}

        # 重新计算总计
        self._recalculate_cart_totals(cart_data)
        self._save_carts()

        return {
            "status": "removed",
            "cart": Cart(**cart_data).model_dump()
        }

    def clear_cart(self, session_id: str) -> dict:
        """清空购物车"""
        if session_id not in self.carts:
            return {"status": "error", "message": "购物车不存在"}

        cart_data = self.carts[session_id]
        cart_data["items"] = []
        self._recalculate_cart_totals(cart_data)
        self._save_carts()

        return {
            "status": "cleared",
            "cart": Cart(**cart_data).model_dump()
        }

    def checkout(self, request: CheckoutRequest) -> dict:
        """结算购物车生成订单"""
        if request.session_id not in self.carts:
            return {"status": "error", "message": "购物车不存在"}

        cart_data = self.carts[request.session_id]

        if not cart_data["items"]:
            return {"status": "error", "message": "购物车为空"}

        # 创建订单
        now = time.time()
        order_id = self._generate_order_id()

        order = {
            "order_id": order_id,
            "user_id": request.user_id or cart_data.get("user_id"),
            "session_id": request.session_id,
            "items": cart_data["items"].copy(),
            "total_price": cart_data["total_price"],
            "total_items": cart_data["total_items"],
            "status": OrderStatus.CONFIRMED.value,
            "created_at": now,
            "completed_at": None
        }

        # 保存订单
        self.orders["orders"].append(order)

        # 更新用户订单索引
        user_id = order["user_id"]
        if user_id:
            if user_id not in self.orders["user_index"]:
                self.orders["user_index"][user_id] = []
            self.orders["user_index"][user_id].append(len(self.orders["orders"]) - 1)

        self._save_orders()

        # 清空购物车
        cart_data["items"] = []
        self._recalculate_cart_totals(cart_data)
        self._save_carts()

        # 同步到行为服务（记录订单历史）
        self._sync_order_to_behavior(order)

        return {
            "status": "success",
            "order_id": order_id,
            "order": order,
            "message": f"订单 {order_id} 已创建"
        }

    def _sync_order_to_behavior(self, order: dict):
        """同步订单到行为服务"""
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
                behavior_service.record_order(order_record)
        except Exception as e:
            print(f"同步订单到行为服务失败: {e}")

    def get_user_orders(self, user_id: str, limit: int = 20) -> list[dict]:
        """获取用户订单历史"""
        indices = self.orders["user_index"].get(user_id, [])
        orders = []

        for idx in indices[-limit:]:
            if idx < len(self.orders["orders"]):
                orders.append(self.orders["orders"][idx])

        return orders

    def get_order(self, order_id: str) -> Optional[dict]:
        """获取单个订单"""
        for order in self.orders["orders"]:
            if order["order_id"] == order_id:
                return order
        return None

    def get_order_stats(self) -> dict:
        """获取订单统计"""
        total_orders = len(self.orders["orders"])
        total_revenue = sum(o["total_price"] for o in self.orders["orders"])
        total_items = sum(o["total_items"] for o in self.orders["orders"])

        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "total_items_sold": total_items,
            "unique_users": len(self.orders["user_index"])
        }


# 单例实例
cart_service = CartService()
