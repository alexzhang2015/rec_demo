"""
MOP 场景化上下文服务

功能:
1. 门店管理 - 门店信息、库存状态
2. 天气服务 - 天气状态获取（模拟）
3. 场景服务 - 预定义场景组合
4. 上下文服务 - 统一上下文管理
"""
import random
import time
import hashlib
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


# ============ 数据模型 ============

class StoreType(str, Enum):
    """门店类型"""
    MALL = "mall"          # 购物中心
    OFFICE = "office"      # 写字楼
    STATION = "station"    # 车站/交通枢纽
    UNIVERSITY = "university"  # 高校
    COMMUNITY = "community"    # 社区


class InventoryLevel(str, Enum):
    """库存水平"""
    HIGH = "high"      # 充足
    MEDIUM = "medium"  # 适中
    LOW = "low"        # 紧俏
    OUT = "out"        # 售罄


class BusyLevel(str, Enum):
    """繁忙程度"""
    LOW = "low"        # 空闲
    MEDIUM = "medium"  # 适中
    HIGH = "high"      # 繁忙
    VERY_HIGH = "very_high"  # 非常繁忙


class WeatherCondition(str, Enum):
    """天气状况"""
    SUNNY = "sunny"        # 晴朗
    CLOUDY = "cloudy"      # 多云
    RAINY = "rainy"        # 雨天
    HOT = "hot"            # 炎热
    COLD = "cold"          # 寒冷
    HUMID = "humid"        # 潮湿


# ============ 门店数据 ============

STORES = [
    {
        "store_id": "SH001",
        "name": "星巴克 (静安嘉里中心)",
        "city": "上海",
        "district": "静安区",
        "address": "南京西路1515号静安嘉里中心北区B1",
        "store_type": StoreType.MALL,
        "busy_hours": [8, 9, 12, 13, 18, 19],
        "features": ["reserve", "delivery", "drive_thru"],
        "latitude": 31.224,
        "longitude": 121.445,
        "opening_hours": "07:00-22:00"
    },
    {
        "store_id": "SH002",
        "name": "星巴克 (陆家嘴环球金融中心)",
        "city": "上海",
        "district": "浦东新区",
        "address": "世纪大道100号环球金融中心B1",
        "store_type": StoreType.OFFICE,
        "busy_hours": [8, 9, 10, 12, 18, 19],
        "features": ["reserve", "mobile_order"],
        "latitude": 31.236,
        "longitude": 121.507,
        "opening_hours": "07:00-21:00"
    },
    {
        "store_id": "SH003",
        "name": "星巴克 (虹桥火车站)",
        "city": "上海",
        "district": "闵行区",
        "address": "虹桥火车站出发层",
        "store_type": StoreType.STATION,
        "busy_hours": [7, 8, 9, 17, 18, 19, 20],
        "features": ["mobile_order", "express"],
        "latitude": 31.195,
        "longitude": 121.325,
        "opening_hours": "06:00-22:00"
    },
    {
        "store_id": "BJ001",
        "name": "星巴克 (国贸三期)",
        "city": "北京",
        "district": "朝阳区",
        "address": "建国门外大街1号国贸三期B1",
        "store_type": StoreType.OFFICE,
        "busy_hours": [8, 9, 12, 13, 18, 19],
        "features": ["reserve", "delivery"],
        "latitude": 39.909,
        "longitude": 116.460,
        "opening_hours": "07:00-21:00"
    },
    {
        "store_id": "BJ002",
        "name": "星巴克 (清华科技园)",
        "city": "北京",
        "district": "海淀区",
        "address": "清华科技园科技大厦A座1层",
        "store_type": StoreType.UNIVERSITY,
        "busy_hours": [10, 11, 14, 15, 16],
        "features": ["study_space", "mobile_order"],
        "latitude": 40.005,
        "longitude": 116.325,
        "opening_hours": "08:00-22:00"
    },
    {
        "store_id": "HZ001",
        "name": "星巴克 (湖滨银泰)",
        "city": "杭州",
        "district": "上城区",
        "address": "延安路98号湖滨银泰in77 B区",
        "store_type": StoreType.MALL,
        "busy_hours": [10, 11, 14, 15, 19, 20],
        "features": ["reserve", "terrace"],
        "latitude": 30.254,
        "longitude": 120.167,
        "opening_hours": "09:00-22:00"
    },
    {
        "store_id": "HZ002",
        "name": "星巴克 (阿里巴巴西溪园区)",
        "city": "杭州",
        "district": "余杭区",
        "address": "文一西路969号阿里巴巴西溪园区1号楼",
        "store_type": StoreType.OFFICE,
        "busy_hours": [9, 10, 14, 15, 18],
        "features": ["mobile_order", "meeting_room"],
        "latitude": 30.288,
        "longitude": 120.026,
        "opening_hours": "08:00-20:00"
    },
    {
        "store_id": "SH004",
        "name": "星巴克 (复旦大学)",
        "city": "上海",
        "district": "杨浦区",
        "address": "国定路400号复旦大学光华楼",
        "store_type": StoreType.UNIVERSITY,
        "busy_hours": [10, 11, 14, 15, 16, 20, 21],
        "features": ["study_space", "wifi"],
        "latitude": 31.299,
        "longitude": 121.503,
        "opening_hours": "08:00-22:00"
    },
    # ============ 深圳门店 ============
    {
        "store_id": "SZ001",
        "name": "星巴克 (深圳湾万象城)",
        "city": "深圳",
        "district": "南山区",
        "address": "深圳湾万象城L1层",
        "store_type": StoreType.MALL,
        "busy_hours": [10, 11, 14, 15, 19, 20, 21],
        "features": ["reserve", "delivery", "terrace"],
        "latitude": 22.517,
        "longitude": 113.935,
        "opening_hours": "10:00-22:00"
    },
    {
        "store_id": "SZ002",
        "name": "星巴克 (腾讯滨海大厦)",
        "city": "深圳",
        "district": "南山区",
        "address": "滨海大道3333号腾讯滨海大厦北塔1层",
        "store_type": StoreType.OFFICE,
        "busy_hours": [9, 10, 12, 14, 15, 18, 19],
        "features": ["mobile_order", "meeting_room"],
        "latitude": 22.533,
        "longitude": 113.943,
        "opening_hours": "08:00-21:00"
    },
    {
        "store_id": "SZ003",
        "name": "星巴克 (华强北茂业)",
        "city": "深圳",
        "district": "福田区",
        "address": "华强北路2006号茂业百货1层",
        "store_type": StoreType.MALL,
        "busy_hours": [11, 12, 14, 15, 19, 20],
        "features": ["delivery"],
        "latitude": 22.546,
        "longitude": 114.089,
        "opening_hours": "10:00-22:00"
    },
    {
        "store_id": "SZ004",
        "name": "星巴克 (深圳北站)",
        "city": "深圳",
        "district": "龙华区",
        "address": "深圳北站东广场出发层",
        "store_type": StoreType.STATION,
        "busy_hours": [7, 8, 9, 17, 18, 19, 20],
        "features": ["mobile_order", "express"],
        "latitude": 22.609,
        "longitude": 114.029,
        "opening_hours": "06:30-22:00"
    },
    {
        "store_id": "SZ005",
        "name": "星巴克 (南山科技园)",
        "city": "深圳",
        "district": "南山区",
        "address": "科苑南路3099号科技园中区1栋",
        "store_type": StoreType.OFFICE,
        "busy_hours": [9, 10, 12, 13, 18, 19],
        "features": ["mobile_order", "wifi"],
        "latitude": 22.540,
        "longitude": 113.958,
        "opening_hours": "08:00-20:00"
    },
    # ============ 广州门店 ============
    {
        "store_id": "GZ001",
        "name": "星巴克 (天河城)",
        "city": "广州",
        "district": "天河区",
        "address": "天河路208号天河城B1层",
        "store_type": StoreType.MALL,
        "busy_hours": [10, 11, 14, 15, 19, 20],
        "features": ["reserve", "delivery"],
        "latitude": 23.131,
        "longitude": 113.330,
        "opening_hours": "10:00-22:00"
    },
    {
        "store_id": "GZ002",
        "name": "星巴克 (珠江新城)",
        "city": "广州",
        "district": "天河区",
        "address": "珠江新城华夏路10号富力中心1层",
        "store_type": StoreType.OFFICE,
        "busy_hours": [8, 9, 12, 13, 18, 19],
        "features": ["mobile_order"],
        "latitude": 23.122,
        "longitude": 113.322,
        "opening_hours": "07:30-21:00"
    }
]


# ============ 天气配置 ============

WEATHER_CONDITIONS = {
    "hot": {
        "condition": WeatherCondition.HOT,
        "temperature": 32,
        "humidity": 65,
        "description": "晴朗炎热",
        "icon": "☀️",
        "boost_tags": ["冰爽", "清爽", "冰"],
        "demote_tags": ["热", "温暖"],
        "boost_temperatures": ["ICED", "BLENDED"],
        "demote_temperatures": ["HOT", "EXTRA_HOT"]
    },
    "rainy": {
        "condition": WeatherCondition.RAINY,
        "temperature": 22,
        "humidity": 85,
        "description": "阴雨绵绵",
        "icon": "🌧️",
        "boost_tags": ["热", "温暖", "治愈"],
        "demote_tags": ["冰爽"],
        "boost_temperatures": ["HOT", "WARM"],
        "demote_temperatures": ["ICED"]
    },
    "cold": {
        "condition": WeatherCondition.COLD,
        "temperature": 5,
        "humidity": 50,
        "description": "寒冷干燥",
        "icon": "❄️",
        "boost_tags": ["热", "温暖", "暖心"],
        "demote_tags": ["冰爽", "冰", "清爽"],
        "boost_temperatures": ["HOT", "EXTRA_HOT"],
        "demote_temperatures": ["ICED", "BLENDED"]
    },
    "sunny": {
        "condition": WeatherCondition.SUNNY,
        "temperature": 25,
        "humidity": 55,
        "description": "晴朗舒适",
        "icon": "🌤️",
        "boost_tags": [],
        "demote_tags": [],
        "boost_temperatures": [],
        "demote_temperatures": []
    },
    "cloudy": {
        "condition": WeatherCondition.CLOUDY,
        "temperature": 20,
        "humidity": 60,
        "description": "多云微凉",
        "icon": "☁️",
        "boost_tags": ["经典"],
        "demote_tags": [],
        "boost_temperatures": [],
        "demote_temperatures": []
    },
    "humid": {
        "condition": WeatherCondition.HUMID,
        "temperature": 28,
        "humidity": 80,
        "description": "闷热潮湿",
        "icon": "🌫️",
        "boost_tags": ["冰爽", "清爽", "提神"],
        "demote_tags": ["甜蜜"],
        "boost_temperatures": ["ICED"],
        "demote_temperatures": ["HOT"]
    }
}


# ============ 场景配置 ============

CONTEXT_SCENARIOS = [
    {
        "scenario_id": "office_morning_rush",
        "name": "上班早高峰",
        "icon": "🏢",
        "description": "工作日早晨，需要提神醒脑开启一天",
        "context": {
            "time_of_day": "morning",
            "day_type": "weekday",
            "store_type": "office"
        },
        "boost_tags": ["提神", "经典", "便携", "咖啡因"],
        "boost_categories": ["咖啡", "食品"],
        "demote_tags": ["甜蜜", "网红"],
        "recommended_time": "07:30-09:30"
    },
    {
        "scenario_id": "office_afternoon",
        "name": "下午茶时光",
        "icon": "☕",
        "description": "午后犯困，来杯提神的下午茶",
        "context": {
            "time_of_day": "afternoon",
            "day_type": "weekday"
        },
        "boost_tags": ["提神", "下午茶", "轻食"],
        "boost_categories": ["咖啡", "茶饮"],
        "demote_tags": [],
        "recommended_time": "14:00-16:00"
    },
    {
        "scenario_id": "weekend_leisure",
        "name": "周末休闲",
        "icon": "🛍️",
        "description": "周末逛街，享受悠闲时光",
        "context": {
            "time_of_day": "afternoon",
            "day_type": "weekend"
        },
        "boost_tags": ["网红", "新品", "颜值", "甜蜜"],
        "boost_categories": ["星冰乐", "茶饮"],
        "demote_tags": [],
        "recommended_time": "10:00-18:00"
    },
    {
        "scenario_id": "student_study",
        "name": "学习充电",
        "icon": "📚",
        "description": "在咖啡店学习，需要持久专注",
        "context": {
            "store_type": "university",
            "time_of_day": "afternoon"
        },
        "boost_tags": ["提神", "经典", "大杯"],
        "boost_categories": ["咖啡"],
        "demote_tags": ["甜蜜"],
        "recommended_time": "09:00-21:00"
    },
    {
        "scenario_id": "travel_rush",
        "name": "出行赶路",
        "icon": "🚄",
        "description": "赶火车/飞机，需要快速取餐",
        "context": {
            "store_type": "station"
        },
        "boost_tags": ["便携", "经典", "快速"],
        "boost_categories": ["咖啡", "食品"],
        "demote_tags": ["需等待"],
        "recommended_time": "06:00-22:00"
    },
    {
        "scenario_id": "date_night",
        "name": "约会时光",
        "icon": "💕",
        "description": "和朋友或恋人共度美好时光",
        "context": {
            "time_of_day": "evening",
            "day_type": "weekend"
        },
        "boost_tags": ["颜值", "网红", "分享", "甜蜜"],
        "boost_categories": ["星冰乐", "茶饮", "食品"],
        "demote_tags": ["苦", "浓郁"],
        "recommended_time": "18:00-21:00"
    },
    {
        "scenario_id": "healthy_morning",
        "name": "健康早餐",
        "icon": "🥗",
        "description": "注重健康的早晨选择",
        "context": {
            "time_of_day": "morning"
        },
        "boost_tags": ["低卡", "健康", "无糖", "燕麦奶", "植物基"],
        "boost_categories": ["咖啡", "茶饮"],
        "demote_tags": ["高糖", "奶油"],
        "recommended_time": "07:00-10:00"
    },
    {
        "scenario_id": "summer_cool",
        "name": "夏日清凉",
        "icon": "🧊",
        "description": "炎炎夏日，需要清凉解暑",
        "context": {
            "season": "summer",
            "weather": "hot"
        },
        "boost_tags": ["冰爽", "清爽", "果香"],
        "boost_categories": ["星冰乐", "清爽系列"],
        "demote_tags": ["热", "温暖"],
        "recommended_time": "11:00-17:00"
    },
    {
        "scenario_id": "winter_warm",
        "name": "冬日暖心",
        "icon": "🔥",
        "description": "寒冷冬天，来杯暖心饮品",
        "context": {
            "season": "winter",
            "weather": "cold"
        },
        "boost_tags": ["热", "温暖", "暖心", "经典"],
        "boost_categories": ["咖啡", "茶饮"],
        "demote_tags": ["冰", "冰爽"],
        "recommended_time": "07:00-20:00"
    },
    {
        "scenario_id": "late_night",
        "name": "深夜加班",
        "icon": "🌙",
        "description": "深夜工作，需要低咖啡因陪伴",
        "context": {
            "time_of_day": "night"
        },
        "boost_tags": ["无咖啡因", "舒缓", "茶香"],
        "boost_categories": ["茶饮"],
        "demote_tags": ["咖啡因", "提神"],
        "recommended_time": "21:00-24:00"
    }
]


# ============ 门店服务 ============

class StoreService:
    """门店服务"""

    def __init__(self):
        self.stores = {store["store_id"]: store for store in STORES}
        self._inventory_cache: dict[str, dict] = {}

    def get_all_stores(self) -> list[dict]:
        """获取所有门店"""
        return STORES

    def get_store(self, store_id: str) -> Optional[dict]:
        """获取门店详情"""
        return self.stores.get(store_id)

    def get_stores_by_city(self, city: str) -> list[dict]:
        """按城市获取门店"""
        return [s for s in STORES if s["city"] == city]

    def get_stores_by_type(self, store_type: StoreType) -> list[dict]:
        """按类型获取门店"""
        return [s for s in STORES if s["store_type"] == store_type]

    def get_nearby_stores(self, lat: float, lon: float, limit: int = 5) -> list[dict]:
        """获取附近门店（模拟距离计算）"""
        stores_with_distance = []
        for store in STORES:
            # 简化的距离计算（实际应使用 haversine 公式）
            dlat = abs(store["latitude"] - lat)
            dlon = abs(store["longitude"] - lon)
            distance = ((dlat ** 2 + dlon ** 2) ** 0.5) * 111  # 粗略转换为公里
            stores_with_distance.append({
                **store,
                "distance_km": round(distance, 1)
            })

        stores_with_distance.sort(key=lambda x: x["distance_km"])
        return stores_with_distance[:limit]

    def get_store_busy_level(self, store_id: str) -> dict:
        """获取门店繁忙程度"""
        store = self.stores.get(store_id)
        if not store:
            return {"level": BusyLevel.MEDIUM, "wait_minutes": 5}

        current_hour = datetime.now().hour
        is_busy_hour = current_hour in store.get("busy_hours", [])

        if is_busy_hour:
            # 高峰期随机波动
            rand = random.random()
            if rand > 0.7:
                return {"level": BusyLevel.VERY_HIGH, "wait_minutes": random.randint(12, 18)}
            else:
                return {"level": BusyLevel.HIGH, "wait_minutes": random.randint(8, 12)}
        else:
            rand = random.random()
            if rand > 0.6:
                return {"level": BusyLevel.MEDIUM, "wait_minutes": random.randint(4, 7)}
            else:
                return {"level": BusyLevel.LOW, "wait_minutes": random.randint(2, 4)}

    def get_store_inventory(self, store_id: str) -> dict[str, InventoryLevel]:
        """获取门店库存（模拟）"""
        # 使用缓存，每5分钟更新一次
        cache_key = f"{store_id}_{int(time.time() // 300)}"

        if cache_key not in self._inventory_cache:
            # 模拟库存数据
            from app.data import MENU_ITEMS

            inventory = {}
            for item in MENU_ITEMS:
                rand = random.random()
                if rand > 0.95:
                    inventory[item.sku] = InventoryLevel.OUT
                elif rand > 0.85:
                    inventory[item.sku] = InventoryLevel.LOW
                elif rand > 0.6:
                    inventory[item.sku] = InventoryLevel.MEDIUM
                else:
                    inventory[item.sku] = InventoryLevel.HIGH

            self._inventory_cache[cache_key] = inventory

        return self._inventory_cache.get(cache_key, {})

    def get_item_inventory(self, store_id: str, item_sku: str) -> InventoryLevel:
        """获取单个商品库存"""
        inventory = self.get_store_inventory(store_id)
        return inventory.get(item_sku, InventoryLevel.MEDIUM)


# ============ 城市气候配置 ============

# 不同城市的气候基准温度调整（相对于默认值）
CITY_CLIMATE = {
    # 华南地区 - 冬季温暖，夏季炎热潮湿
    "深圳": {"winter_offset": 12, "summer_offset": 2, "region": "south", "humidity_offset": 10},
    "广州": {"winter_offset": 10, "summer_offset": 2, "region": "south", "humidity_offset": 15},
    # 华东地区 - 四季分明
    "上海": {"winter_offset": 3, "summer_offset": 0, "region": "east", "humidity_offset": 5},
    "杭州": {"winter_offset": 2, "summer_offset": 0, "region": "east", "humidity_offset": 5},
    # 华北地区 - 冬季寒冷
    "北京": {"winter_offset": -3, "summer_offset": -2, "region": "north", "humidity_offset": -10},
}

# 各城市当前真实天气的近似值（1月中旬）
CITY_REALTIME_WEATHER = {
    "深圳": {"temp_range": (15, 22), "condition": "sunny", "description": "晴朗温和"},
    "广州": {"temp_range": (13, 20), "condition": "cloudy", "description": "多云温和"},
    "上海": {"temp_range": (3, 10), "condition": "cloudy", "description": "阴冷"},
    "杭州": {"temp_range": (2, 9), "condition": "cloudy", "description": "阴冷"},
    "北京": {"temp_range": (-8, 2), "condition": "cold", "description": "寒冷干燥"},
}


# ============ 天气服务 ============

class WeatherService:
    """天气服务"""

    def __init__(self):
        self._weather_cache: dict[str, dict] = {}

    def get_weather(self, city: str) -> dict:
        """获取城市天气（基于城市气候特征模拟）"""
        # 使用缓存，每10分钟更新
        cache_key = f"{city}_{int(time.time() // 600)}"

        if cache_key not in self._weather_cache:
            now = datetime.now()
            month = now.month
            hour = now.hour

            # 获取城市气候配置
            city_climate = CITY_CLIMATE.get(city, {"winter_offset": 0, "summer_offset": 0, "region": "east", "humidity_offset": 0})
            realtime = CITY_REALTIME_WEATHER.get(city)

            # 如果有该城市的实时天气近似值，优先使用
            if realtime:
                temp_min, temp_max = realtime["temp_range"]
                # 根据时间计算当前温度
                if 6 <= hour <= 14:
                    # 早到午后温度上升
                    temp_ratio = (hour - 6) / 8
                    temperature = temp_min + (temp_max - temp_min) * temp_ratio
                else:
                    # 下午到夜间温度下降
                    if hour > 14:
                        temp_ratio = 1 - (hour - 14) / 10
                    else:
                        temp_ratio = 0.3  # 深夜
                    temperature = temp_min + (temp_max - temp_min) * temp_ratio

                temperature = round(temperature + random.uniform(-1, 1))
                weather_type = realtime["condition"]
                description = realtime["description"]
            else:
                # 回退到基于季节的模拟
                # 季节性天气倾向（针对华南调整）
                region = city_climate.get("region", "east")

                if month in [6, 7, 8]:  # 夏季
                    if region == "south":
                        weights = {"hot": 0.4, "humid": 0.4, "rainy": 0.2}
                    else:
                        weights = {"hot": 0.5, "humid": 0.2, "sunny": 0.2, "rainy": 0.1}
                elif month in [12, 1, 2]:  # 冬季
                    if region == "south":
                        # 华南冬季温和
                        weights = {"sunny": 0.5, "cloudy": 0.4, "rainy": 0.1}
                    elif region == "north":
                        weights = {"cold": 0.7, "cloudy": 0.2, "sunny": 0.1}
                    else:
                        weights = {"cold": 0.4, "cloudy": 0.4, "sunny": 0.2}
                elif month in [3, 4, 5]:  # 春季
                    if region == "south":
                        weights = {"humid": 0.4, "rainy": 0.3, "cloudy": 0.2, "sunny": 0.1}
                    else:
                        weights = {"sunny": 0.3, "cloudy": 0.3, "rainy": 0.3, "humid": 0.1}
                else:  # 秋季
                    weights = {"sunny": 0.5, "cloudy": 0.3, "cold": 0.2}

                weather_type = random.choices(
                    list(weights.keys()),
                    weights=list(weights.values())
                )[0]

                weather_config = WEATHER_CONDITIONS.get(weather_type, WEATHER_CONDITIONS["sunny"])
                base_temp = weather_config["temperature"]

                # 应用城市气候调整
                if month in [12, 1, 2]:
                    temp_offset = city_climate.get("winter_offset", 0)
                elif month in [6, 7, 8]:
                    temp_offset = city_climate.get("summer_offset", 0)
                else:
                    temp_offset = city_climate.get("winter_offset", 0) // 2

                temperature = base_temp + temp_offset + random.randint(-2, 2)
                description = weather_config["description"]

            # 根据温度确定天气类型（用于推荐逻辑）
            if temperature >= 30:
                effective_weather_type = "hot"
            elif temperature <= 10:
                effective_weather_type = "cold"
            elif weather_type == "rainy":
                effective_weather_type = "rainy"
            elif weather_type == "humid" or (city_climate.get("humidity_offset", 0) > 5 and temperature > 25):
                effective_weather_type = "humid"
            else:
                effective_weather_type = "sunny" if temperature > 20 else "cloudy"

            weather_config = WEATHER_CONDITIONS.get(effective_weather_type, WEATHER_CONDITIONS["sunny"])

            # 湿度调整
            base_humidity = weather_config["humidity"]
            humidity = base_humidity + city_climate.get("humidity_offset", 0) + random.randint(-5, 5)
            humidity = max(20, min(95, humidity))

            # 确定图标
            if temperature >= 30:
                icon = "☀️"
            elif temperature <= 5:
                icon = "❄️"
            elif weather_type == "rainy":
                icon = "🌧️"
            elif weather_type == "cloudy":
                icon = "☁️"
            elif weather_type == "humid":
                icon = "🌫️"
            else:
                icon = "🌤️"

            self._weather_cache[cache_key] = {
                "city": city,
                "condition": weather_config["condition"].value,
                "temperature": temperature,
                "humidity": humidity,
                "description": description,
                "icon": icon,
                "weather_type": effective_weather_type,
                "boost_tags": weather_config["boost_tags"],
                "demote_tags": weather_config["demote_tags"],
                "boost_temperatures": weather_config["boost_temperatures"],
                "demote_temperatures": weather_config["demote_temperatures"],
                "updated_at": time.time(),
                "is_realtime_approximation": realtime is not None
            }

        return self._weather_cache[cache_key]

    def get_simulated_weather(self, weather_type: str) -> dict:
        """获取模拟天气（用于演示）"""
        weather_config = WEATHER_CONDITIONS.get(weather_type, WEATHER_CONDITIONS["sunny"])
        return {
            "condition": weather_config["condition"].value,
            "temperature": weather_config["temperature"],
            "humidity": weather_config["humidity"],
            "description": weather_config["description"],
            "icon": weather_config["icon"],
            "weather_type": weather_type,
            "boost_tags": weather_config["boost_tags"],
            "demote_tags": weather_config["demote_tags"],
            "boost_temperatures": weather_config["boost_temperatures"],
            "demote_temperatures": weather_config["demote_temperatures"],
            "simulated": True
        }


# ============ 场景服务 ============

class ScenarioService:
    """场景服务"""

    def __init__(self):
        self.scenarios = {s["scenario_id"]: s for s in CONTEXT_SCENARIOS}

    def get_all_scenarios(self) -> list[dict]:
        """获取所有场景"""
        return CONTEXT_SCENARIOS

    def get_scenario(self, scenario_id: str) -> Optional[dict]:
        """获取场景详情"""
        return self.scenarios.get(scenario_id)

    def get_matching_scenarios(self, context: dict) -> list[dict]:
        """获取匹配当前上下文的场景"""
        matching = []

        for scenario in CONTEXT_SCENARIOS:
            scenario_context = scenario.get("context", {})
            match_score = 0
            total_fields = len(scenario_context)

            if total_fields == 0:
                continue

            for key, value in scenario_context.items():
                if context.get(key) == value:
                    match_score += 1

            if match_score > 0:
                matching.append({
                    **scenario,
                    "match_score": match_score / total_fields
                })

        matching.sort(key=lambda x: x["match_score"], reverse=True)
        return matching[:5]

    def get_recommended_scenario(self, context: dict) -> Optional[dict]:
        """获取最匹配的推荐场景"""
        matching = self.get_matching_scenarios(context)
        return matching[0] if matching else None


# ============ 上下文服务 ============

class ContextService:
    """统一上下文管理服务"""

    def __init__(self):
        self.store_service = StoreService()
        self.weather_service = WeatherService()
        self.scenario_service = ScenarioService()

    def get_current_context(
        self,
        store_id: Optional[str] = None,
        city: Optional[str] = None,
        weather_override: Optional[str] = None,
        scenario_override: Optional[str] = None
    ) -> dict:
        """获取当前完整上下文"""
        now = datetime.now()
        hour = now.hour

        # 时间上下文
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

        # 季节
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

        context = {
            "timestamp": time.time(),
            "datetime": now.isoformat(),
            "time_of_day": time_of_day,
            "hour": hour,
            "season": season,
            "day_type": day_type,
            "month": month,
            "weekday": now.weekday()
        }

        # 门店上下文
        if store_id:
            store = self.store_service.get_store(store_id)
            if store:
                context["store"] = {
                    "store_id": store["store_id"],
                    "name": store["name"],
                    "city": store["city"],
                    "district": store["district"],
                    "store_type": store["store_type"].value if isinstance(store["store_type"], StoreType) else store["store_type"],
                    "features": store.get("features", [])
                }
                context["store_type"] = store["store_type"].value if isinstance(store["store_type"], StoreType) else store["store_type"]

                # 门店繁忙程度
                busy_info = self.store_service.get_store_busy_level(store_id)
                context["store"]["busy_level"] = busy_info["level"].value if isinstance(busy_info["level"], BusyLevel) else busy_info["level"]
                context["store"]["wait_minutes"] = busy_info["wait_minutes"]

                city = store["city"]

        # 天气上下文
        if weather_override:
            context["weather"] = self.weather_service.get_simulated_weather(weather_override)
        elif city:
            context["weather"] = self.weather_service.get_weather(city)
        else:
            # 默认使用上海天气
            context["weather"] = self.weather_service.get_weather("上海")

        # 场景上下文
        if scenario_override:
            scenario = self.scenario_service.get_scenario(scenario_override)
            if scenario:
                context["scenario"] = scenario
                context["active_scenario_id"] = scenario_override
        else:
            # 自动匹配场景
            recommended = self.scenario_service.get_recommended_scenario({
                "time_of_day": time_of_day,
                "day_type": day_type,
                "season": season,
                "store_type": context.get("store_type"),
                "weather": context.get("weather", {}).get("weather_type")
            })
            if recommended:
                context["scenario"] = recommended
                context["active_scenario_id"] = recommended["scenario_id"]

        return context

    def simulate_context(
        self,
        time_of_day: Optional[str] = None,
        weather: Optional[str] = None,
        store_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        day_type: Optional[str] = None,
        season: Optional[str] = None
    ) -> dict:
        """模拟上下文（用于演示）"""
        # 获取基础上下文
        context = self.get_current_context(
            store_id=store_id,
            weather_override=weather,
            scenario_override=scenario_id
        )

        # 覆盖模拟值
        if time_of_day:
            context["time_of_day"] = time_of_day
        if day_type:
            context["day_type"] = day_type
        if season:
            context["season"] = season

        context["simulated"] = True

        return context

    def calculate_context_boost(
        self,
        context: dict,
        item_tags: list[str],
        item_category: str,
        item_temperatures: list[str]
    ) -> dict:
        """计算上下文对商品的加权影响"""
        factors = {}

        # 1. 时段因子
        time_factor = 1.0
        time_reason = ""
        time_of_day = context.get("time_of_day")

        if time_of_day == "morning":
            if item_category == "咖啡":
                time_factor = 1.15
                time_reason = "早晨咖啡需求高峰"
            elif "早餐" in item_tags:
                time_factor = 1.2
                time_reason = "早餐时段加权"
        elif time_of_day == "afternoon":
            if item_category in ["茶饮", "星冰乐"]:
                time_factor = 1.1
                time_reason = "下午茶时段偏好"
        elif time_of_day == "evening":
            if "无咖啡因" in item_tags:
                time_factor = 1.15
                time_reason = "晚间低咖啡因偏好"
            elif item_category == "咖啡":
                time_factor = 0.9
                time_reason = "晚间咖啡降权"
        elif time_of_day == "night":
            if item_category == "咖啡":
                time_factor = 0.8
                time_reason = "深夜咖啡降权"

        factors["time_factor"] = {
            "value": round(time_factor, 2),
            "reason": time_reason or "标准时段权重"
        }

        # 2. 天气因子
        weather_factor = 1.0
        weather_reason = ""
        weather_info = context.get("weather", {})

        if weather_info:
            temp = weather_info.get("temperature", 25)
            weather_type = weather_info.get("weather_type", "sunny")
            boost_tags = weather_info.get("boost_tags", [])
            demote_tags = weather_info.get("demote_tags", [])
            boost_temps = weather_info.get("boost_temperatures", [])
            demote_temps = weather_info.get("demote_temperatures", [])

            # 标签匹配
            for tag in item_tags:
                if tag in boost_tags:
                    weather_factor += 0.08
                    weather_reason = f"{weather_info.get('description', '')}天气偏好"
                if tag in demote_tags:
                    weather_factor -= 0.08

            # 温度匹配
            item_temps_upper = [t.upper() for t in item_temperatures]
            boost_temps_upper = [t.upper() for t in boost_temps]
            demote_temps_upper = [t.upper() for t in demote_temps]

            has_boost_temp = any(t in boost_temps_upper for t in item_temps_upper)
            has_demote_temp = any(t in demote_temps_upper for t in item_temps_upper)

            for item_temp in item_temperatures:
                if item_temp.upper() in boost_temps_upper:
                    weather_factor += 0.1
                    weather_reason = weather_reason or f"天气适配温度偏好"
                if item_temp.upper() in demote_temps_upper:
                    weather_factor -= 0.1

            # 🆕 对只有冰饮选项的商品在冷天额外降权
            # 如果商品只有被降权的温度选项，没有被加权的温度选项，说明是纯冰饮/纯热饮商品
            if has_demote_temp and not has_boost_temp:
                # 商品完全不支持天气偏好的温度，额外降权
                weather_factor -= 0.15
                if weather_type == "cold":
                    weather_reason = "冷天不推荐纯冰饮"
                elif weather_type == "hot":
                    weather_reason = "热天不推荐纯热饮"

            weather_factor = max(0.6, min(1.5, weather_factor))

        factors["weather_factor"] = {
            "value": round(weather_factor, 2),
            "reason": weather_reason or "标准天气权重"
        }

        # 3. 门店因子
        store_factor = 1.0
        store_reason = ""
        store_info = context.get("store", {})

        if store_info:
            store_type = store_info.get("store_type")

            # 门店类型匹配
            if store_type == "office":
                if item_category == "咖啡" and "提神" in item_tags:
                    store_factor = 1.1
                    store_reason = "写字楼店提神饮品偏好"
            elif store_type == "university":
                if "大杯" in item_tags or item_category == "咖啡":
                    store_factor = 1.1
                    store_reason = "高校店学习饮品偏好"
            elif store_type == "station":
                if "便携" in item_tags or "经典" in item_tags:
                    store_factor = 1.1
                    store_reason = "车站店快捷饮品偏好"
            elif store_type == "mall":
                if "网红" in item_tags or "颜值" in item_tags:
                    store_factor = 1.1
                    store_reason = "购物中心网红饮品偏好"

        factors["store_factor"] = {
            "value": round(store_factor, 2),
            "reason": store_reason or "标准门店权重"
        }

        # 4. 场景因子
        scenario_factor = 1.0
        scenario_reason = ""
        scenario_info = context.get("scenario", {})

        if scenario_info:
            boost_tags = scenario_info.get("boost_tags", [])
            demote_tags = scenario_info.get("demote_tags", [])
            boost_categories = scenario_info.get("boost_categories", [])

            # 标签匹配
            for tag in item_tags:
                if tag in boost_tags:
                    scenario_factor += 0.05
                if tag in demote_tags:
                    scenario_factor -= 0.05

            # 类别匹配
            if item_category in boost_categories:
                scenario_factor += 0.1
                scenario_reason = f"「{scenario_info.get('name', '')}」场景推荐"

            scenario_factor = max(0.7, min(1.5, scenario_factor))

        factors["scenario_factor"] = {
            "value": round(scenario_factor, 2),
            "reason": scenario_reason or "标准场景权重"
        }

        # 综合因子
        total_factor = time_factor * weather_factor * store_factor * scenario_factor
        total_factor = max(0.5, min(2.0, total_factor))

        return {
            "total_factor": round(total_factor, 3),
            "factors": factors
        }


# ============ 单例实例 ============

store_service = StoreService()
weather_service = WeatherService()
scenario_service = ScenarioService()
context_service = ContextService()
