"""菜单数据"""
from app.models import (
    MenuItem, Category, Temperature, CupSize,
    SugarLevel, MilkType, CustomizationConstraints
)

# 模拟菜单数据
MENU_ITEMS: list[MenuItem] = [
    # 咖啡类
    MenuItem(
        sku="COF001",
        name="经典美式",
        english_name="Caffè Americano",
        category=Category.COFFEE,
        base_price=28,
        description="浓缩咖啡与水的完美结合，醇厚而顺滑",
        image_url="/static/images/americano.jpg",
        calories=15,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["经典", "低卡", "提神"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF, SugarLevel.FULL],
            available_milk_types=None,  # 美式通常不加奶
            supports_extra_shot=True,
            supports_whipped_cream=False,
            available_syrups=["vanilla", "caramel", "hazelnut"],
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE
        )
    ),
    MenuItem(
        sku="COF002",
        name="拿铁",
        english_name="Caffè Latte",
        category=Category.COFFEE,
        base_price=32,
        description="浓缩咖啡与丝滑蒸奶的经典组合",
        image_url="/static/images/latte.jpg",
        calories=190,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["经典", "奶香", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.SOY, MilkType.COCONUT],
            supports_extra_shot=True,
            supports_whipped_cream=False,
            available_syrups=["vanilla", "caramel", "hazelnut"],
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF003",
        name="焦糖玛奇朵",
        english_name="Caramel Macchiato",
        category=Category.COFFEE,
        base_price=36,
        description="香浓焦糖与浓缩咖啡的甜蜜邂逅",
        image_url="/static/images/caramel_macchiato.jpg",
        calories=250,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["甜蜜", "人气", "网红"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],  # 甜饮不支持无糖
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.SOY],
            supports_extra_shot=True,
            supports_whipped_cream=True,
            available_syrups=["caramel"],  # 焦糖玛奇朵固定焦糖
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF004",
        name="馥芮白",
        english_name="Flat White",
        category=Category.COFFEE,
        base_price=34,
        description="双份浓缩与绵密奶泡的澳式风味",
        image_url="/static/images/flat_white.jpg",
        calories=170,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE],
        tags=["浓郁", "澳洲风味"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            supports_extra_shot=True,
            supports_whipped_cream=False,
            available_syrups=None,  # 馥芮白不加糖浆
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF005",
        name="冷萃咖啡",
        english_name="Cold Brew",
        category=Category.COFFEE,
        base_price=30,
        description="低温慢萃20小时，口感顺滑无酸涩",
        image_url="/static/images/cold_brew.jpg",
        calories=5,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["冷萃", "低卡", "顺滑"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF],
            available_milk_types=[MilkType.NONE, MilkType.WHOLE, MilkType.OAT],  # 可选加奶
            supports_extra_shot=True,
            supports_whipped_cream=False,
            available_syrups=["vanilla"],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.NONE
        )
    ),
    MenuItem(
        sku="COF006",
        name="燕麦拿铁",
        english_name="Oat Milk Latte",
        category=Category.COFFEE,
        base_price=38,
        description="燕麦奶带来的植物清香与咖啡融合",
        image_url="/static/images/oat_latte.jpg",
        calories=160,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["植物基", "健康", "网红"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF, SugarLevel.FULL],
            available_milk_types=[MilkType.OAT],  # 燕麦拿铁固定燕麦奶
            supports_extra_shot=True,
            supports_whipped_cream=False,
            available_syrups=["vanilla", "caramel"],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.LIGHT,
            default_milk_type=MilkType.OAT
        )
    ),
    # 茶饮类
    MenuItem(
        sku="TEA001",
        name="抹茶拿铁",
        english_name="Matcha Latte",
        category=Category.TEA,
        base_price=34,
        description="日式抹茶与牛奶的清新组合",
        image_url="/static/images/matcha_latte.jpg",
        calories=240,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["抹茶控", "日式", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.SOY],
            supports_extra_shot=False,  # 茶饮不加浓缩
            supports_whipped_cream=True,
            available_syrups=None,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.HALF,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="TEA002",
        name="红茶拿铁",
        english_name="Black Tea Latte",
        category=Category.TEA,
        base_price=30,
        description="醇香红茶与丝滑牛奶的经典搭配",
        image_url="/static/images/black_tea_latte.jpg",
        calories=180,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["茶香", "经典"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.SOY],
            supports_extra_shot=False,
            supports_whipped_cream=False,
            available_syrups=["vanilla"],
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="TEA003",
        name="桃桃乌龙",
        english_name="Peach Oolong Tea",
        category=Category.TEA,
        base_price=32,
        description="清甜蜜桃与乌龙茶的夏日限定",
        image_url="/static/images/peach_oolong.jpg",
        calories=120,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["果香", "清爽", "夏日"],
        is_seasonal=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],  # 果茶不支持无糖
            available_milk_types=None,  # 果茶不加奶
            supports_extra_shot=False,
            supports_whipped_cream=False,
            available_syrups=None,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="TEA004",
        name="伯爵红茶",
        english_name="Earl Grey Tea",
        category=Category.TEA,
        base_price=26,
        description="经典伯爵红茶，佛手柑芬芳",
        image_url="/static/images/earl_grey.jpg",
        calories=0,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["经典", "低卡", "英式"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF],
            available_milk_types=[MilkType.NONE, MilkType.WHOLE, MilkType.OAT],  # 可选加奶
            supports_extra_shot=False,
            supports_whipped_cream=False,
            available_syrups=None,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.NONE
        )
    ),
    # 星冰乐
    MenuItem(
        sku="FRA001",
        name="摩卡星冰乐",
        english_name="Mocha Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=38,
        description="浓郁巧克力与咖啡的冰爽享受",
        image_url="/static/images/mocha_frappuccino.jpg",
        calories=370,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["巧克力", "冰爽", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],  # 星冰乐不支持无糖
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            supports_extra_shot=True,
            supports_whipped_cream=True,
            available_syrups=["mocha"],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="FRA002",
        name="焦糖星冰乐",
        english_name="Caramel Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=38,
        description="香甜焦糖与咖啡冰沙的完美融合",
        image_url="/static/images/caramel_frappuccino.jpg",
        calories=380,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["焦糖", "甜蜜", "冰爽"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            supports_extra_shot=True,
            supports_whipped_cream=True,
            available_syrups=["caramel"],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="FRA003",
        name="芒果西番莲星冰乐",
        english_name="Mango Passion Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=36,
        description="热带芒果与西番莲的清爽风味",
        image_url="/static/images/mango_frappuccino.jpg",
        calories=280,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["水果", "清爽", "无咖啡因"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=None,  # 水果星冰乐无奶
            supports_extra_shot=False,  # 无咖啡因
            supports_whipped_cream=True,
            available_syrups=None,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    # 清爽系列
    MenuItem(
        sku="REF001",
        name="草莓柠檬气泡水",
        english_name="Strawberry Lemonade Refresher",
        category=Category.REFRESHERS,
        base_price=28,
        description="清新草莓与柠檬的气泡享受",
        image_url="/static/images/strawberry_refresher.jpg",
        calories=90,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["气泡", "果香", "夏日"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=None,  # 气泡水无奶
            supports_extra_shot=False,
            supports_whipped_cream=False,
            available_syrups=None,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="REF002",
        name="粉红饮",
        english_name="Pink Drink",
        category=Category.REFRESHERS,
        base_price=32,
        description="草莓阿萨伊与椰奶的梦幻组合",
        image_url="/static/images/pink_drink.jpg",
        calories=140,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["网红", "颜值", "椰奶"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.COCONUT],  # 粉红饮固定椰奶
            supports_extra_shot=False,
            supports_whipped_cream=False,
            available_syrups=None,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.COCONUT
        )
    ),
    # 食品（无客制化选项）
    MenuItem(
        sku="FOO001",
        name="芝士蛋糕",
        english_name="Cheese Cake",
        category=Category.FOOD,
        base_price=32,
        description="细腻绵密的纽约风味芝士蛋糕",
        image_url="/static/images/cheese_cake.jpg",
        calories=350,
        available_temperatures=[],
        available_sizes=[],
        tags=["甜点", "人气"],
        customization_constraints=None  # 食品无客制化
    ),
    MenuItem(
        sku="FOO002",
        name="可颂",
        english_name="Croissant",
        category=Category.FOOD,
        base_price=18,
        description="法式黄油可颂，外酥里嫩",
        image_url="/static/images/croissant.jpg",
        calories=280,
        available_temperatures=[],
        available_sizes=[],
        tags=["早餐", "经典"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO003",
        name="香肠卷",
        english_name="Sausage Roll",
        category=Category.FOOD,
        base_price=22,
        description="酥脆面皮包裹多汁香肠",
        image_url="/static/images/sausage_roll.jpg",
        calories=320,
        available_temperatures=[],
        available_sizes=[],
        tags=["咸点", "早餐"],
        customization_constraints=None
    ),

    # ============ 新增商品 ============

    # 咖啡类新增 (6个)
    MenuItem(
        sku="COF007",
        name="浓缩咖啡",
        english_name="Espresso",
        category=Category.COFFEE,
        base_price=22,
        description="纯正意式浓缩，咖啡的灵魂",
        image_url="/static/images/espresso.jpg",
        calories=5,
        available_temperatures=[Temperature.HOT],
        available_sizes=[CupSize.TALL],
        tags=["经典", "浓郁", "提神", "低卡"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT],
            available_milk_types=None,
            supports_extra_shot=True,
            supports_whipped_cream=False,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE
        )
    ),
    MenuItem(
        sku="COF008",
        name="卡布奇诺",
        english_name="Cappuccino",
        category=Category.COFFEE,
        base_price=32,
        description="浓缩咖啡配绵密奶泡，经典意式风味",
        image_url="/static/images/cappuccino.jpg",
        calories=120,
        available_temperatures=[Temperature.HOT],
        available_sizes=[CupSize.TALL, CupSize.GRANDE],
        tags=["经典", "奶泡", "意式"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            supports_extra_shot=True,
            supports_whipped_cream=False,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF009",
        name="摩卡",
        english_name="Caffè Mocha",
        category=Category.COFFEE,
        base_price=36,
        description="浓缩咖啡、巧克力与蒸奶的完美融合",
        image_url="/static/images/mocha.jpg",
        calories=290,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["巧克力", "甜蜜", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            supports_extra_shot=True,
            supports_whipped_cream=True,
            available_syrups=["mocha"],
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF010",
        name="香草拿铁",
        english_name="Vanilla Latte",
        category=Category.COFFEE,
        base_price=34,
        description="香草糖浆为拿铁增添甜蜜香气",
        image_url="/static/images/vanilla_latte.jpg",
        calories=220,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["香草", "甜蜜", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.SOY],
            supports_extra_shot=True,
            supports_whipped_cream=False,
            available_syrups=["vanilla"],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF011",
        name="榛果拿铁",
        english_name="Hazelnut Latte",
        category=Category.COFFEE,
        base_price=34,
        description="榛果糖浆带来坚果香气的拿铁",
        image_url="/static/images/hazelnut_latte.jpg",
        calories=230,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["榛果", "坚果香", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            supports_extra_shot=True,
            supports_whipped_cream=False,
            available_syrups=["hazelnut"],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF012",
        name="生椰拿铁",
        english_name="Coconut Latte",
        category=Category.COFFEE,
        base_price=38,
        description="生椰浆与浓缩咖啡的热带风情",
        image_url="/static/images/coconut_latte.jpg",
        calories=180,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["生椰", "植物基", "网红", "清爽"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF],
            available_milk_types=[MilkType.COCONUT],
            supports_extra_shot=True,
            supports_whipped_cream=False,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.LIGHT,
            default_milk_type=MilkType.COCONUT
        )
    ),

    # 茶饮类新增 (4个)
    MenuItem(
        sku="TEA005",
        name="柚子蜂蜜茶",
        english_name="Honey Citrus Tea",
        category=Category.TEA,
        base_price=28,
        description="柚子与蜂蜜的温暖治愈组合",
        image_url="/static/images/honey_citrus_tea.jpg",
        calories=80,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["蜂蜜", "柚子", "治愈", "养生"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=None,
            supports_extra_shot=False,
            supports_whipped_cream=False,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="TEA006",
        name="芝芝抹茶",
        english_name="Cheese Matcha",
        category=Category.TEA,
        base_price=36,
        description="香浓芝士奶盖与抹茶的绝妙碰撞",
        image_url="/static/images/cheese_matcha.jpg",
        calories=320,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["芝士", "抹茶控", "网红", "颜值"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.OAT],
            supports_extra_shot=False,
            supports_whipped_cream=False,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="TEA007",
        name="蜜桃红茶",
        english_name="Peach Black Tea",
        category=Category.TEA,
        base_price=30,
        description="蜜桃果香与红茶的清甜搭配",
        image_url="/static/images/peach_black_tea.jpg",
        calories=100,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["果香", "清爽", "夏日"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=None,
            supports_extra_shot=False,
            supports_whipped_cream=False,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="TEA008",
        name="茉莉花茶",
        english_name="Jasmine Tea",
        category=Category.TEA,
        base_price=24,
        description="清新茉莉花香，回味悠长",
        image_url="/static/images/jasmine_tea.jpg",
        calories=0,
        available_temperatures=[Temperature.HOT, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["经典", "低卡", "清香", "无咖啡因"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.LIGHT, SugarLevel.HALF],
            available_milk_types=None,
            supports_extra_shot=False,
            supports_whipped_cream=False,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE
        )
    ),

    # 星冰乐新增 (4个)
    MenuItem(
        sku="FRA004",
        name="香草星冰乐",
        english_name="Vanilla Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=36,
        description="香草风味的经典冰沙饮品",
        image_url="/static/images/vanilla_frappuccino.jpg",
        calories=340,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["香草", "冰爽", "经典"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            supports_extra_shot=True,
            supports_whipped_cream=True,
            available_syrups=["vanilla"],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="FRA005",
        name="抹茶星冰乐",
        english_name="Matcha Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=38,
        description="日式抹茶风味的冰沙饮品",
        image_url="/static/images/matcha_frappuccino.jpg",
        calories=350,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["抹茶控", "日式", "冰爽"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            supports_extra_shot=False,
            supports_whipped_cream=True,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="FRA006",
        name="草莓星冰乐",
        english_name="Strawberry Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=36,
        description="草莓风味的粉红色冰沙",
        image_url="/static/images/strawberry_frappuccino.jpg",
        calories=300,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["草莓", "颜值", "水果", "无咖啡因"],
        is_seasonal=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM],
            supports_extra_shot=False,
            supports_whipped_cream=True,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="FRA007",
        name="芒果星冰乐",
        english_name="Mango Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=36,
        description="热带芒果风味的清爽冰沙",
        image_url="/static/images/mango_frappuccino.jpg",
        calories=280,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["芒果", "热带", "水果", "无咖啡因", "夏日"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=None,
            supports_extra_shot=False,
            supports_whipped_cream=True,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),

    # 清爽系列新增 (3个)
    MenuItem(
        sku="REF003",
        name="柠檬气泡冰",
        english_name="Lemon Refresher",
        category=Category.REFRESHERS,
        base_price=26,
        description="清新柠檬与气泡的清爽组合",
        image_url="/static/images/lemon_refresher.jpg",
        calories=70,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["气泡", "柠檬", "清爽", "低卡", "夏日"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=None,
            supports_extra_shot=False,
            supports_whipped_cream=False,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="REF004",
        name="青柠薄荷",
        english_name="Lime Mint Refresher",
        category=Category.REFRESHERS,
        base_price=28,
        description="青柠与薄荷的清凉邂逅",
        image_url="/static/images/lime_mint_refresher.jpg",
        calories=60,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["薄荷", "清凉", "清爽", "低卡", "夏日"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=None,
            supports_extra_shot=False,
            supports_whipped_cream=False,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="REF005",
        name="西柚气泡饮",
        english_name="Grapefruit Refresher",
        category=Category.REFRESHERS,
        base_price=30,
        description="西柚与气泡的微苦清爽",
        image_url="/static/images/grapefruit_refresher.jpg",
        calories=80,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["西柚", "气泡", "清爽", "微苦"],
        is_seasonal=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.HALF, SugarLevel.LESS, SugarLevel.FULL],
            available_milk_types=None,
            supports_extra_shot=False,
            supports_whipped_cream=False,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),

    # 食品新增 (5个)
    MenuItem(
        sku="FOO004",
        name="巧克力马芬",
        english_name="Chocolate Muffin",
        category=Category.FOOD,
        base_price=22,
        description="浓郁巧克力风味的松软马芬",
        image_url="/static/images/chocolate_muffin.jpg",
        calories=380,
        available_temperatures=[],
        available_sizes=[],
        tags=["甜点", "巧克力", "人气"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO005",
        name="蓝莓马芬",
        english_name="Blueberry Muffin",
        category=Category.FOOD,
        base_price=22,
        description="酸甜蓝莓点缀的经典马芬",
        image_url="/static/images/blueberry_muffin.jpg",
        calories=360,
        available_temperatures=[],
        available_sizes=[],
        tags=["甜点", "蓝莓", "经典"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO006",
        name="肉桂卷",
        english_name="Cinnamon Roll",
        category=Category.FOOD,
        base_price=28,
        description="香甜肉桂与柔软面包的完美结合",
        image_url="/static/images/cinnamon_roll.jpg",
        calories=420,
        available_temperatures=[],
        available_sizes=[],
        tags=["甜点", "肉桂", "人气", "早餐"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO007",
        name="蛋挞",
        english_name="Egg Tart",
        category=Category.FOOD,
        base_price=15,
        description="酥脆外壳包裹嫩滑蛋奶馅",
        image_url="/static/images/egg_tart.jpg",
        calories=200,
        available_temperatures=[],
        available_sizes=[],
        tags=["甜点", "经典", "人气"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO008",
        name="火腿芝士三明治",
        english_name="Ham & Cheese Sandwich",
        category=Category.FOOD,
        base_price=32,
        description="火腿与芝士的经典搭配",
        image_url="/static/images/ham_cheese_sandwich.jpg",
        calories=380,
        available_temperatures=[],
        available_sizes=[],
        tags=["咸点", "早餐", "人气"],
        customization_constraints=None
    ),
]


def get_menu_by_sku(sku: str) -> MenuItem | None:
    """根据SKU获取菜单项"""
    for item in MENU_ITEMS:
        if item.sku == sku:
            return item
    return None


def get_menu_by_category(category: Category) -> list[MenuItem]:
    """根据分类获取菜单"""
    return [item for item in MENU_ITEMS if item.category == category]


def get_all_categories() -> list[dict]:
    """获取所有分类"""
    return [{"value": c.name, "label": c.value} for c in Category]
