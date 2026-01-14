"""数据模型定义"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Category(str, Enum):
    """饮品分类"""
    COFFEE = "咖啡"
    TEA = "茶饮"
    FRAPPUCCINO = "星冰乐"
    REFRESHERS = "清爽系列"
    FOOD = "食品"


class CupSize(str, Enum):
    """杯型"""
    TALL = "中杯"
    GRANDE = "大杯"
    VENTI = "超大杯"


class Temperature(str, Enum):
    """温度"""
    HOT = "热"
    ICED = "冰"
    WARM = "温"


class SugarLevel(str, Enum):
    """糖度"""
    FULL = "全糖"
    LESS = "少糖"
    HALF = "半糖"
    LIGHT = "微糖"
    NONE = "无糖"


class MilkType(str, Enum):
    """奶类"""
    WHOLE = "全脂牛奶"
    SKIM = "脱脂牛奶"
    OAT = "燕麦奶"
    SOY = "豆奶"
    COCONUT = "椰奶"
    NONE = "不加奶"


class Customization(BaseModel):
    """客制化选项"""
    cup_size: CupSize = CupSize.GRANDE
    temperature: Temperature = Temperature.ICED
    sugar_level: SugarLevel = SugarLevel.FULL
    milk_type: MilkType = MilkType.WHOLE
    extra_shot: bool = False  # 加浓缩
    whipped_cream: bool = False  # 奶油
    syrup: Optional[str] = None  # 糖浆风味


class CustomizationConstraints(BaseModel):
    """商品客制化约束 - 定义商品支持的客制化选项"""
    # 可用选项（None 表示该选项不适用于此商品）
    available_sugar_levels: Optional[list[SugarLevel]] = None
    available_milk_types: Optional[list[MilkType]] = None

    # 功能支持
    supports_extra_shot: bool = False  # 是否支持加浓缩
    supports_whipped_cream: bool = False  # 是否支持奶油顶
    available_syrups: Optional[list[str]] = None  # 可用糖浆列表

    # 默认/推荐配置
    default_temperature: Optional[Temperature] = None
    default_sugar_level: Optional[SugarLevel] = None
    default_milk_type: Optional[MilkType] = None


class MenuItem(BaseModel):
    """菜单项"""
    sku: str
    name: str
    english_name: str
    category: Category
    base_price: float
    description: str
    image_url: str
    is_new: bool = False
    is_seasonal: bool = False
    calories: int
    available_temperatures: list[Temperature]
    available_sizes: list[CupSize]
    tags: list[str] = []
    customization_constraints: Optional[CustomizationConstraints] = None  # 客制化约束


class OrderItem(BaseModel):
    """订单项"""
    menu_item: MenuItem
    customization: Customization
    quantity: int = 1

    @property
    def total_price(self) -> float:
        price = self.menu_item.base_price
        # 杯型加价
        if self.customization.cup_size == CupSize.VENTI:
            price += 4
        elif self.customization.cup_size == CupSize.TALL:
            price -= 3
        # 额外选项加价
        if self.customization.extra_shot:
            price += 4
        if self.customization.milk_type in [MilkType.OAT, MilkType.COCONUT]:
            price += 3
        return price * self.quantity


class UserPreference(BaseModel):
    """用户偏好"""
    user_id: str
    favorite_categories: list[Category] = []
    preferred_temperature: Optional[Temperature] = None
    preferred_sugar: Optional[SugarLevel] = None
    preferred_milk: Optional[MilkType] = None
    order_history: list[str] = []  # SKU列表
    tags_preference: list[str] = []


# ============ 购物车与订单模型 ============

class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "待确认"
    CONFIRMED = "已确认"
    PREPARING = "制作中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


class CartItem(BaseModel):
    """购物车商品项"""
    id: str  # 购物车项唯一ID
    item_sku: str
    item_name: str
    category: str
    quantity: int = 1
    customization: Optional[Customization] = None
    unit_price: float  # 基础单价
    final_price: float  # 含客制化后的单价
    image_url: Optional[str] = None
    tags: list[str] = []


class Cart(BaseModel):
    """购物车"""
    session_id: str
    user_id: Optional[str] = None
    items: list[CartItem] = []
    total_price: float = 0.0
    total_items: int = 0
    created_at: float
    updated_at: float


class CompletedOrder(BaseModel):
    """已完成的订单"""
    order_id: str
    user_id: Optional[str] = None
    session_id: str
    items: list[CartItem]
    total_price: float
    total_items: int
    status: OrderStatus = OrderStatus.CONFIRMED
    created_at: float
    completed_at: Optional[float] = None


# ============ API请求模型 ============

class AddToCartRequest(BaseModel):
    """添加到购物车请求"""
    session_id: str
    user_id: Optional[str] = None
    item_sku: str
    quantity: int = 1
    customization: Optional[Customization] = None


class UpdateCartItemRequest(BaseModel):
    """更新购物车商品请求"""
    quantity: Optional[int] = None
    customization: Optional[Customization] = None


class CheckoutRequest(BaseModel):
    """结算请求"""
    session_id: str
    user_id: Optional[str] = None
