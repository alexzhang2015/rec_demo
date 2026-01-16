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
    EXTRA_HOT = "特别热"
    HOT = "热"
    WARM = "微热"
    ICED = "冰"
    LESS_ICE = "少冰"
    NO_ICE = "去冰"
    FULL_ICE = "全冰"


class SugarLevel(str, Enum):
    """糖度/甜度选择"""
    FULL = "经典糖"        # 标准甜度
    ZERO_CAL = "0热量代糖"  # 0热量代糖
    NONE = "不另外加糖"     # 不另外加糖
    LESS = "少甜"          # Less Sweetness
    STANDARD = "标准甜"    # Regular Sweetness


class MilkType(str, Enum):
    """奶类 - 添加或更换牛奶"""
    WHOLE = "全脂牛奶"
    SKIM = "脱脂牛奶"
    OAT = "燕麦奶"
    ALMOND = "巴旦木奶"
    SOY = "豆奶"
    COCONUT = "椰奶"
    NONE = "不加奶"


class EspressoRoast(str, Enum):
    """浓缩咖啡烘焙类型"""
    CLASSIC_DARK = "经典浓缩(深烘)"
    BLONDE = "金烘浓缩(浅烘)"
    DECAF_DARK = "低因浓缩(深烘)"


class EspressoType(str, Enum):
    """浓缩咖啡萃取类型"""
    SIGNATURE = "原萃浓缩"   # 浓郁醇香，焦糖般甜感
    RISTRETTO = "精萃浓缩"   # 精炼萃取，倍感甜郁
    LONG_SHOT = "满萃浓缩"   # 深度萃取，焦香饱满


class RoomLevel(str, Enum):
    """留位（奶量空间）"""
    STANDARD = "标准"
    MORE = "多"
    EXTRA = "更多"


class SugarFreeFlavor(str, Enum):
    """无糖风味糖浆"""
    VANILLA = "香草风味"
    HAZELNUT = "榛果风味"
    SEA_SALT_CARAMEL = "海盐焦糖风味"
    TAHITIAN_VANILLA = "大溪地香草风味"
    BERRY = "莓莓风味"
    PANDAN = "糯香斑斓风味"


class Drizzle(str, Enum):
    """淋酱/其它"""
    MOCHA = "摩卡淋酱"
    CARAMEL = "焦糖风味酱"


class WhippedCreamLevel(str, Enum):
    """奶油顶"""
    NONE = "不加奶油"
    LIGHT = "加少量搅打稀奶油"
    STANDARD = "加标准搅打稀奶油"


class Customization(BaseModel):
    """客制化选项"""
    # 基础选项
    cup_size: CupSize = CupSize.GRANDE
    temperature: Temperature = Temperature.ICED
    sugar_level: SugarLevel = SugarLevel.FULL
    milk_type: MilkType = MilkType.WHOLE

    # 浓缩咖啡选项
    espresso_roast: Optional[EspressoRoast] = None  # 烘焙类型
    espresso_type: Optional[EspressoType] = None    # 萃取类型
    espresso_shots: int = 2                          # 浓缩份数

    # 风味与添加
    sugar_free_flavor: Optional[SugarFreeFlavor] = None  # 无糖风味
    whipped_cream: WhippedCreamLevel = WhippedCreamLevel.NONE  # 奶油顶
    drizzle: Optional[Drizzle] = None               # 淋酱
    room_level: RoomLevel = RoomLevel.STANDARD      # 留位

    # 饮品主体添加
    extra_cream: bool = False    # 稀奶油
    mocha_sauce: bool = False    # 摩卡酱


class CustomizationConstraints(BaseModel):
    """商品客制化约束 - 定义商品支持的客制化选项"""
    # 可用选项（None 表示该选项不适用于此商品）
    available_sugar_levels: Optional[list[SugarLevel]] = None
    available_milk_types: Optional[list[MilkType]] = None
    available_temperatures: Optional[list[Temperature]] = None

    # 浓缩咖啡选项
    available_espresso_roasts: Optional[list[EspressoRoast]] = None
    available_espresso_types: Optional[list[EspressoType]] = None
    supports_espresso_adjustment: bool = False  # 是否支持调整浓缩份数
    default_espresso_shots: int = 2

    # 风味与添加
    available_sugar_free_flavors: Optional[list[SugarFreeFlavor]] = None
    available_drizzles: Optional[list[Drizzle]] = None
    supports_whipped_cream: bool = False
    supports_room_adjustment: bool = False  # 是否支持调整留位
    supports_extra_cream: bool = False      # 是否支持添加稀奶油
    supports_mocha_sauce: bool = False      # 是否支持添加摩卡酱

    # 默认/推荐配置
    default_temperature: Optional[Temperature] = None
    default_sugar_level: Optional[SugarLevel] = None
    default_milk_type: Optional[MilkType] = None
    default_espresso_roast: Optional[EspressoRoast] = None
    default_espresso_type: Optional[EspressoType] = None

    # 会员优惠信息
    member_discount: Optional[float] = None  # 金星会员折扣价


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
