"""菜单数据 - 基于星巴克真实商品信息"""
from app.models import (
    MenuItem, Category, Temperature, CupSize,
    SugarLevel, MilkType, CustomizationConstraints,
    EspressoRoast, EspressoType, SugarFreeFlavor, Drizzle
)

# 通用温度选项
COFFEE_HOT_TEMPS = [Temperature.EXTRA_HOT, Temperature.HOT, Temperature.WARM]
COFFEE_ICED_TEMPS = [Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE, Temperature.FULL_ICE]
COFFEE_ALL_TEMPS = COFFEE_HOT_TEMPS + COFFEE_ICED_TEMPS

# 通用浓缩选项
ALL_ESPRESSO_ROASTS = [EspressoRoast.CLASSIC_DARK, EspressoRoast.BLONDE, EspressoRoast.DECAF_DARK]
ALL_ESPRESSO_TYPES = [EspressoType.SIGNATURE, EspressoType.RISTRETTO, EspressoType.LONG_SHOT]

# 通用无糖风味
ALL_SUGAR_FREE_FLAVORS = [
    SugarFreeFlavor.VANILLA, SugarFreeFlavor.HAZELNUT,
    SugarFreeFlavor.SEA_SALT_CARAMEL, SugarFreeFlavor.TAHITIAN_VANILLA,
    SugarFreeFlavor.BERRY, SugarFreeFlavor.PANDAN
]

# 模拟菜单数据
MENU_ITEMS: list[MenuItem] = [
    # ============ 咖啡类 ============
    MenuItem(
        sku="COF001",
        name="美式咖啡",
        english_name="Caffè Americano",
        category=Category.COFFEE,
        base_price=30,
        description="简单即是美味，萃取经典浓缩咖啡，以水调和，香气浓郁漫溢。毫升数仅供参考，饮品量以实际为准。",
        image_url="/static/images/americano.jpg",
        calories=15,
        available_temperatures=[Temperature.HOT, Temperature.WARM, Temperature.ICED,
                               Temperature.LESS_ICE, Temperature.NO_ICE, Temperature.FULL_ICE],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["经典", "低卡", "提神", "0糖风味可选"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.NONE],
            available_milk_types=[MilkType.WHOLE, MilkType.ALMOND, MilkType.OAT, MilkType.SKIM],
            available_temperatures=COFFEE_ALL_TEMPS,
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            available_espresso_types=ALL_ESPRESSO_TYPES,
            supports_espresso_adjustment=True,
            default_espresso_shots=3,
            available_sugar_free_flavors=ALL_SUGAR_FREE_FLAVORS,
            supports_whipped_cream=True,
            supports_room_adjustment=True,
            supports_extra_cream=True,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE,
            default_espresso_roast=EspressoRoast.CLASSIC_DARK,
            default_espresso_type=EspressoType.SIGNATURE,
            member_discount=21
        )
    ),
    MenuItem(
        sku="COF002",
        name="馥芮白",
        english_name="Flat White",
        category=Category.COFFEE,
        base_price=38,
        description="选用星巴克精萃浓缩咖啡制成，融合蒸煮牛奶，风味更浓郁和甘甜。毫升数仅供参考，饮品量以实际为准。",
        image_url="/static/images/flat_white.jpg",
        calories=170,
        available_temperatures=[Temperature.EXTRA_HOT, Temperature.HOT, Temperature.WARM,
                               Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["浓郁", "经典", "澳洲风味", "0糖风味可选"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.NONE],
            available_milk_types=[MilkType.WHOLE, MilkType.ALMOND, MilkType.OAT, MilkType.SKIM],
            available_temperatures=[Temperature.EXTRA_HOT, Temperature.HOT, Temperature.WARM,
                                   Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            available_espresso_types=ALL_ESPRESSO_TYPES,
            supports_espresso_adjustment=True,
            default_espresso_shots=2,
            available_sugar_free_flavors=ALL_SUGAR_FREE_FLAVORS,
            available_drizzles=[Drizzle.MOCHA, Drizzle.CARAMEL],
            supports_whipped_cream=True,
            supports_extra_cream=True,
            supports_mocha_sauce=True,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.WHOLE,
            default_espresso_roast=EspressoRoast.CLASSIC_DARK,
            default_espresso_type=EspressoType.RISTRETTO
        )
    ),
    MenuItem(
        sku="COF003",
        name="拿铁",
        english_name="Caffè Latte",
        category=Category.COFFEE,
        base_price=35,
        description="浓缩咖啡与蒸煮牛奶完美融合，口感丝滑细腻。",
        image_url="/static/images/latte.jpg",
        calories=190,
        available_temperatures=COFFEE_ALL_TEMPS,
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["经典", "奶香", "人气", "0糖风味可选"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.NONE],
            available_milk_types=[MilkType.WHOLE, MilkType.ALMOND, MilkType.OAT, MilkType.SKIM],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            available_espresso_types=ALL_ESPRESSO_TYPES,
            supports_espresso_adjustment=True,
            available_sugar_free_flavors=ALL_SUGAR_FREE_FLAVORS,
            available_drizzles=[Drizzle.MOCHA, Drizzle.CARAMEL],
            supports_whipped_cream=True,
            supports_extra_cream=True,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF004",
        name="焦糖玛奇朵",
        english_name="Caramel Macchiato",
        category=Category.COFFEE,
        base_price=39,
        description="香浓焦糖与浓缩咖啡的甜蜜邂逅，顶部淋焦糖酱。",
        image_url="/static/images/caramel_macchiato.jpg",
        calories=250,
        available_temperatures=COFFEE_ALL_TEMPS,
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["甜蜜", "人气", "网红", "焦糖"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.NONE, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.ALMOND, MilkType.OAT, MilkType.SKIM],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            available_espresso_types=ALL_ESPRESSO_TYPES,
            supports_espresso_adjustment=True,
            available_drizzles=[Drizzle.CARAMEL],
            supports_whipped_cream=True,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="COF005",
        name="冷萃咖啡",
        english_name="Cold Brew",
        category=Category.COFFEE,
        base_price=32,
        description="低温慢萃20小时，口感顺滑无酸涩，咖啡香气更醇厚。",
        image_url="/static/images/cold_brew.jpg",
        calories=5,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE, Temperature.FULL_ICE],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["冷萃", "低卡", "顺滑", "提神"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.ZERO_CAL],
            available_milk_types=[MilkType.NONE, MilkType.WHOLE, MilkType.OAT, MilkType.ALMOND],
            available_sugar_free_flavors=ALL_SUGAR_FREE_FLAVORS,
            supports_whipped_cream=True,
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
        base_price=39,
        description="燕麦奶带来的植物清香与咖啡融合，健康植物基选择。",
        image_url="/static/images/oat_latte.jpg",
        calories=160,
        available_temperatures=COFFEE_ALL_TEMPS,
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["植物基", "健康", "网红", "燕麦"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.ZERO_CAL, SugarLevel.FULL],
            available_milk_types=[MilkType.OAT],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
            available_sugar_free_flavors=ALL_SUGAR_FREE_FLAVORS,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.OAT
        )
    ),
    MenuItem(
        sku="COF007",
        name="浓缩咖啡",
        english_name="Espresso",
        category=Category.COFFEE,
        base_price=24,
        description="纯正意式浓缩，咖啡的灵魂所在。",
        image_url="/static/images/espresso.jpg",
        calories=5,
        available_temperatures=[Temperature.HOT],
        available_sizes=[CupSize.TALL],
        tags=["经典", "浓郁", "提神", "低卡", "意式"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            available_espresso_types=ALL_ESPRESSO_TYPES,
            supports_espresso_adjustment=True,
            default_espresso_shots=2,
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE,
            default_espresso_roast=EspressoRoast.CLASSIC_DARK
        )
    ),
    MenuItem(
        sku="COF008",
        name="卡布奇诺",
        english_name="Cappuccino",
        category=Category.COFFEE,
        base_price=35,
        description="浓缩咖啡配绵密奶泡，经典意式风味。",
        image_url="/static/images/cappuccino.jpg",
        calories=120,
        available_temperatures=[Temperature.EXTRA_HOT, Temperature.HOT, Temperature.WARM],
        available_sizes=[CupSize.TALL, CupSize.GRANDE],
        tags=["经典", "奶泡", "意式"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.ZERO_CAL, SugarLevel.FULL],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.ALMOND],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
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
        base_price=38,
        description="浓缩咖啡、巧克力酱与蒸煮牛奶的完美融合，顶部奶油。",
        image_url="/static/images/mocha.jpg",
        calories=290,
        available_temperatures=COFFEE_ALL_TEMPS,
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["巧克力", "甜蜜", "人气", "奶油"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.ALMOND],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
            available_drizzles=[Drizzle.MOCHA],
            supports_whipped_cream=True,
            supports_mocha_sauce=True,
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
        base_price=37,
        description="香草糖浆为拿铁增添甜蜜香气。",
        image_url="/static/images/vanilla_latte.jpg",
        calories=220,
        available_temperatures=COFFEE_ALL_TEMPS,
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["香草", "甜蜜", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.ALMOND],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
            available_sugar_free_flavors=[SugarFreeFlavor.VANILLA, SugarFreeFlavor.TAHITIAN_VANILLA],
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
        base_price=37,
        description="榛果糖浆带来坚果香气的拿铁。",
        image_url="/static/images/hazelnut_latte.jpg",
        calories=230,
        available_temperatures=COFFEE_ALL_TEMPS,
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["榛果", "坚果香", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.ALMOND],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
            available_sugar_free_flavors=[SugarFreeFlavor.HAZELNUT],
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
        base_price=40,
        description="生椰浆与浓缩咖啡的热带风情，清爽不腻。",
        image_url="/static/images/coconut_latte.jpg",
        calories=180,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["生椰", "植物基", "网红", "清爽", "夏日"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.ZERO_CAL],
            available_milk_types=[MilkType.COCONUT],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.COCONUT
        )
    ),

    # ============ 茶饮类 ============
    MenuItem(
        sku="TEA001",
        name="抹茶拿铁",
        english_name="Matcha Latte",
        category=Category.TEA,
        base_price=36,
        description="日式抹茶与牛奶的清新组合，抹茶控必选。",
        image_url="/static/images/matcha_latte.jpg",
        calories=240,
        available_temperatures=COFFEE_ALL_TEMPS,
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["抹茶控", "日式", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.NONE, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.ALMOND],
            supports_whipped_cream=True,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),
    MenuItem(
        sku="TEA002",
        name="红茶拿铁",
        english_name="Black Tea Latte",
        category=Category.TEA,
        base_price=32,
        description="醇香红茶与丝滑牛奶的经典搭配。",
        image_url="/static/images/black_tea_latte.jpg",
        calories=180,
        available_temperatures=COFFEE_ALL_TEMPS,
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["茶香", "经典", "奶茶"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.NONE, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT, MilkType.ALMOND],
            available_sugar_free_flavors=[SugarFreeFlavor.VANILLA],
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
        base_price=34,
        description="清甜蜜桃与乌龙茶的夏日限定，清爽解渴。",
        image_url="/static/images/peach_oolong.jpg",
        calories=120,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["果香", "清爽", "夏日", "限定"],
        is_seasonal=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.LESS],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="TEA004",
        name="伯爵红茶",
        english_name="Earl Grey Tea",
        category=Category.TEA,
        base_price=28,
        description="经典伯爵红茶，佛手柑芬芳，回味悠长。",
        image_url="/static/images/earl_grey.jpg",
        calories=0,
        available_temperatures=[Temperature.HOT, Temperature.WARM, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["经典", "低卡", "英式", "无咖啡因"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.ZERO_CAL],
            available_milk_types=[MilkType.NONE, MilkType.WHOLE, MilkType.OAT],
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE,
            default_milk_type=MilkType.NONE
        )
    ),
    MenuItem(
        sku="TEA005",
        name="柚子蜂蜜茶",
        english_name="Honey Citrus Tea",
        category=Category.TEA,
        base_price=30,
        description="柚子与蜂蜜的温暖治愈组合，润喉养生。",
        image_url="/static/images/honey_citrus_tea.jpg",
        calories=80,
        available_temperatures=[Temperature.HOT, Temperature.WARM, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["蜂蜜", "柚子", "治愈", "养生"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="TEA006",
        name="芝芝抹茶",
        english_name="Cheese Matcha",
        category=Category.TEA,
        base_price=38,
        description="香浓芝士奶盖与抹茶的绝妙碰撞，颜值与美味并存。",
        image_url="/static/images/cheese_matcha.jpg",
        calories=320,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["芝士", "抹茶控", "网红", "颜值", "奶盖"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.OAT],
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
        base_price=32,
        description="蜜桃果香与红茶的清甜搭配，夏日清爽之选。",
        image_url="/static/images/peach_black_tea.jpg",
        calories=100,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["果香", "清爽", "夏日"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.ZERO_CAL, SugarLevel.LESS],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="TEA008",
        name="茉莉花茶",
        english_name="Jasmine Tea",
        category=Category.TEA,
        base_price=26,
        description="清新茉莉花香，回味悠长，经典中式茶饮。",
        image_url="/static/images/jasmine_tea.jpg",
        calories=0,
        available_temperatures=[Temperature.HOT, Temperature.WARM, Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["经典", "低卡", "清香", "无咖啡因", "中式"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.NONE, SugarLevel.ZERO_CAL],
            default_temperature=Temperature.HOT,
            default_sugar_level=SugarLevel.NONE
        )
    ),

    # ============ 星冰乐 ============
    MenuItem(
        sku="FRA001",
        name="摩卡星冰乐",
        english_name="Mocha Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=40,
        description="浓郁巧克力与咖啡的冰爽享受，顶部奶油与摩卡酱。",
        image_url="/static/images/mocha_frappuccino.jpg",
        calories=370,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["巧克力", "冰爽", "人气", "奶油"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
            available_drizzles=[Drizzle.MOCHA],
            supports_whipped_cream=True,
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
        base_price=40,
        description="香甜焦糖与咖啡冰沙的完美融合，淋焦糖酱。",
        image_url="/static/images/caramel_frappuccino.jpg",
        calories=380,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["焦糖", "甜蜜", "冰爽", "人气"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
            available_drizzles=[Drizzle.CARAMEL],
            supports_whipped_cream=True,
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
        base_price=38,
        description="热带芒果与西番莲的清爽风味，无咖啡因。",
        image_url="/static/images/mango_frappuccino.jpg",
        calories=280,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["水果", "清爽", "无咖啡因", "热带"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            supports_whipped_cream=True,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="FRA004",
        name="香草星冰乐",
        english_name="Vanilla Frappuccino",
        category=Category.FRAPPUCCINO,
        base_price=38,
        description="香草风味的经典冰沙饮品，香甜顺滑。",
        image_url="/static/images/vanilla_frappuccino.jpg",
        calories=340,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["香草", "冰爽", "经典"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
            available_espresso_roasts=ALL_ESPRESSO_ROASTS,
            supports_espresso_adjustment=True,
            available_sugar_free_flavors=[SugarFreeFlavor.VANILLA],
            supports_whipped_cream=True,
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
        base_price=40,
        description="日式抹茶风味的冰沙饮品，抹茶控最爱。",
        image_url="/static/images/matcha_frappuccino.jpg",
        calories=350,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["抹茶控", "日式", "冰爽"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM, MilkType.OAT],
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
        base_price=38,
        description="草莓风味的粉红色冰沙，颜值超高。",
        image_url="/static/images/strawberry_frappuccino.jpg",
        calories=300,
        available_temperatures=[Temperature.ICED],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["草莓", "颜值", "水果", "无咖啡因", "粉红"],
        is_seasonal=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            available_milk_types=[MilkType.WHOLE, MilkType.SKIM],
            supports_whipped_cream=True,
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.WHOLE
        )
    ),

    # ============ 清爽系列 ============
    MenuItem(
        sku="REF001",
        name="草莓柠檬气泡水",
        english_name="Strawberry Lemonade Refresher",
        category=Category.REFRESHERS,
        base_price=30,
        description="清新草莓与柠檬的气泡享受，清爽解渴。",
        image_url="/static/images/strawberry_refresher.jpg",
        calories=90,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["气泡", "果香", "夏日", "清爽"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="REF002",
        name="粉红饮",
        english_name="Pink Drink",
        category=Category.REFRESHERS,
        base_price=34,
        description="草莓阿萨伊与椰奶的梦幻组合，ins风网红饮品。",
        image_url="/static/images/pink_drink.jpg",
        calories=140,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["网红", "颜值", "椰奶", "粉红", "ins风"],
        is_new=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            available_milk_types=[MilkType.COCONUT],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL,
            default_milk_type=MilkType.COCONUT
        )
    ),
    MenuItem(
        sku="REF003",
        name="柠檬气泡冰",
        english_name="Lemon Refresher",
        category=Category.REFRESHERS,
        base_price=28,
        description="清新柠檬与气泡的清爽组合，低卡解渴。",
        image_url="/static/images/lemon_refresher.jpg",
        calories=70,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
        available_sizes=[CupSize.TALL, CupSize.GRANDE, CupSize.VENTI],
        tags=["气泡", "柠檬", "清爽", "低卡", "夏日"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS, SugarLevel.NONE],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="REF004",
        name="青柠薄荷",
        english_name="Lime Mint Refresher",
        category=Category.REFRESHERS,
        base_price=30,
        description="青柠与薄荷的清凉邂逅，提神醒脑。",
        image_url="/static/images/lime_mint_refresher.jpg",
        calories=60,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["薄荷", "清凉", "清爽", "低卡", "夏日"],
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),
    MenuItem(
        sku="REF005",
        name="西柚气泡饮",
        english_name="Grapefruit Refresher",
        category=Category.REFRESHERS,
        base_price=32,
        description="西柚与气泡的微苦清爽，成熟风味。",
        image_url="/static/images/grapefruit_refresher.jpg",
        calories=80,
        available_temperatures=[Temperature.ICED, Temperature.LESS_ICE, Temperature.NO_ICE],
        available_sizes=[CupSize.GRANDE, CupSize.VENTI],
        tags=["西柚", "气泡", "清爽", "微苦", "成熟"],
        is_seasonal=True,
        customization_constraints=CustomizationConstraints(
            available_sugar_levels=[SugarLevel.FULL, SugarLevel.LESS],
            default_temperature=Temperature.ICED,
            default_sugar_level=SugarLevel.FULL
        )
    ),

    # ============ 食品 ============
    MenuItem(
        sku="FOO001",
        name="芝士蛋糕",
        english_name="New York Cheese Cake",
        category=Category.FOOD,
        base_price=35,
        description="细腻绵密的纽约风味芝士蛋糕，浓郁奶香。",
        image_url="/static/images/cheese_cake.jpg",
        calories=350,
        available_temperatures=[],
        available_sizes=[],
        tags=["甜点", "人气", "芝士"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO002",
        name="可颂",
        english_name="Butter Croissant",
        category=Category.FOOD,
        base_price=20,
        description="法式黄油可颂，外酥里嫩，层次分明。",
        image_url="/static/images/croissant.jpg",
        calories=280,
        available_temperatures=[],
        available_sizes=[],
        tags=["早餐", "经典", "法式"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO003",
        name="香肠卷",
        english_name="Sausage Roll",
        category=Category.FOOD,
        base_price=24,
        description="酥脆面皮包裹多汁香肠，咸香可口。",
        image_url="/static/images/sausage_roll.jpg",
        calories=320,
        available_temperatures=[],
        available_sizes=[],
        tags=["咸点", "早餐", "人气"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO004",
        name="巧克力马芬",
        english_name="Chocolate Muffin",
        category=Category.FOOD,
        base_price=24,
        description="浓郁巧克力风味的松软马芬，巧克力控必选。",
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
        base_price=24,
        description="酸甜蓝莓点缀的经典马芬，果香四溢。",
        image_url="/static/images/blueberry_muffin.jpg",
        calories=360,
        available_temperatures=[],
        available_sizes=[],
        tags=["甜点", "蓝莓", "经典", "水果"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO006",
        name="肉桂卷",
        english_name="Cinnamon Roll",
        category=Category.FOOD,
        base_price=30,
        description="香甜肉桂与柔软面包的完美结合，淋糖霜。",
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
        base_price=18,
        description="酥脆外壳包裹嫩滑蛋奶馅，经典港式风味。",
        image_url="/static/images/egg_tart.jpg",
        calories=200,
        available_temperatures=[],
        available_sizes=[],
        tags=["甜点", "经典", "人气", "港式"],
        customization_constraints=None
    ),
    MenuItem(
        sku="FOO008",
        name="火腿芝士三明治",
        english_name="Ham & Cheese Sandwich",
        category=Category.FOOD,
        base_price=35,
        description="火腿与芝士的经典搭配，早餐首选。",
        image_url="/static/images/ham_cheese_sandwich.jpg",
        calories=380,
        available_temperatures=[],
        available_sizes=[],
        tags=["咸点", "早餐", "人气", "芝士"],
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
