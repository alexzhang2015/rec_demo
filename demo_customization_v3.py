#!/usr/bin/env python3
"""客制化推荐准确性演示 - 修复版"""
import httpx
import json
from datetime import datetime, timedelta
import time

BASE_URL = "http://localhost:8000"
USER_ID = "cust_demo_" + str(int(time.time()))

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

print_section("客制化推荐准确性演示")
print(f"测试用户ID: {USER_ID}")

# Step 1: 创建订单
print_section("Step 1: 创建带客制化偏好的订单历史")

orders = []
for i in range(8):
    orders.append({
        "user_id": USER_ID,
        "item_sku": ["COF001", "COF002", "COF003", "COF004", "TEA001", "TEA002"][i % 6],
        "quantity": 1,
        "order_time": (datetime.now() - timedelta(days=i*2)).isoformat(),
        "customization": {
            "temperature": "ICED",
            "cup_size": "GRANDE",
            "sugar_level": "NONE" if i % 4 != 3 else "LIGHT",
            "milk_type": "OAT"
        }
    })

resp = httpx.post(f"{BASE_URL}/api/orders/batch", json={"orders": orders}, timeout=30)
print(f"✅ 创建了 {len(orders)} 笔订单")
print(f"   偏好设定: 100% 冰饮, 100% 燕麦奶, 75% 无糖, 100% 大杯")

# Step 2: 验证偏好
print_section("Step 2: 验证偏好提取")
time.sleep(1)

resp = httpx.get(f"{BASE_URL}/api/behavior/user/{USER_ID}", timeout=30)
data = resp.json()
cp = data.get("customization_preference", {})

if cp:
    # 温度偏好
    if cp.get("temperature"):
        print("\n温度偏好:")
        for t, v in sorted(cp["temperature"].items(), key=lambda x: -x[1]):
            bar = "█" * int(v * 20)
            check = "✅ 符合预期" if t == "ICED" and v >= 0.9 else ""
            print(f"  {t:10} {bar} {v*100:5.1f}% {check}")
    
    # 奶类偏好
    if cp.get("milk_type"):
        print("\n奶类偏好:")
        for m, v in sorted(cp["milk_type"].items(), key=lambda x: -x[1]):
            bar = "█" * int(v * 20)
            check = "✅ 符合预期" if m == "OAT" and v >= 0.9 else ""
            print(f"  {m:10} {bar} {v*100:5.1f}% {check}")
    
    # 糖度偏好
    if cp.get("sugar_level"):
        print("\n糖度偏好:")
        for s, v in sorted(cp["sugar_level"].items(), key=lambda x: -x[1]):
            bar = "█" * int(v * 20)
            check = "✅ 符合预期" if s == "NONE" and v >= 0.6 else ""
            print(f"  {s:10} {bar} {v*100:5.1f}% {check}")
else:
    print("❌ 未找到客制化偏好数据")

# 检查商品客制化约束支持
print_section("Step 3: 检查商品客制化约束与用户偏好匹配")

menu_resp = httpx.get(f"{BASE_URL}/api/menu", timeout=30)
items = menu_resp.json().get("items", [])

# 中英文映射（与后端保持一致）
def matches_any(pref: str, values: list, mapping: dict) -> bool:
    """检查偏好是否匹配可用选项（支持中英文）"""
    if not values:
        return False
    pref_variants = mapping.get(pref.upper(), [pref])
    for variant in pref_variants:
        for val in values:
            if variant == val or variant.upper() == str(val).upper():
                return True
    return False

TEMP_MAP = {"HOT": ["热", "HOT"], "ICED": ["冰", "ICED"], "BLENDED": ["冰沙", "BLENDED"]}
MILK_MAP = {"OAT": ["燕麦奶", "OAT"], "WHOLE": ["全脂牛奶", "全脂奶", "WHOLE"],
            "SOY": ["豆奶", "SOY"], "ALMOND": ["杏仁奶", "ALMOND"]}
SUGAR_MAP = {"NONE": ["无糖", "NONE"], "LIGHT": ["微糖", "少糖", "LIGHT"],
             "HALF": ["半糖", "HALF"], "STANDARD": ["全糖", "标准糖", "STANDARD"]}

print(f"\n用户偏好: ICED + OAT + NONE\n")
print(f"{'商品':<12} {'支持冰饮':<10} {'支持燕麦奶':<12} {'支持无糖':<10}")
print("-" * 50)

for item in items[:8]:
    constr = item.get("customization_constraints") or {}
    temps = item.get("available_temperatures", [])
    milks = constr.get("available_milk_types") or []
    sugars = constr.get("available_sugar_levels") or []

    supports_iced = matches_any("ICED", temps, TEMP_MAP) if temps else "?"
    supports_oat = matches_any("OAT", milks, MILK_MAP) if milks else "?"
    supports_none = matches_any("NONE", sugars, SUGAR_MAP) if sugars else "?"

    print(f"{item['name']:<12} {'✓' if supports_iced else '✗':<10} {'✓' if supports_oat else '✗':<12} {'✓' if supports_none else '✗':<10}")

# Step 4: 获取推荐并检查权重
print_section("Step 4: 验证推荐中的客制化权重")

rec_resp = httpx.post(f"{BASE_URL}/api/embedding/recommend/v2", json={
    "persona_type": "咖啡重度用户",
    "user_id": USER_ID,
    "top_k": 5,
    "enable_behavior": True,
    "enable_customization": True
}, timeout=60)

if rec_resp.status_code == 200:
    rec_data = rec_resp.json()
    recs = rec_data.get("recommendations", [])
    
    print(f"\n{'排名':<4} {'商品':<12} {'最终分':<8} {'客制化权重':<12} {'详情'}")
    print("-" * 70)
    
    for i, rec in enumerate(recs):
        item = rec["item"]
        bd = rec.get("score_breakdown", {})
        cust = bd.get("customization_multiplier", 1.0)
        cust_detail = bd.get("customization_boost_detail", {})
        
        detail_str = ""
        if cust_detail:
            factors = cust_detail.get("factors", {})
            if factors:
                detail_str = " ".join([f"{k}:{v:.2f}" for k, v in factors.items() if v != 1.0])
        
        icon = "⬆️" if cust > 1.0 else "⬇️" if cust < 1.0 else "➡️"
        print(f"{i+1:<4} {item['name']:<12} {rec['match_score']*100:>5.1f}% ×{cust:.2f} {icon:<3} {detail_str}")
else:
    print(f"❌ API错误: {rec_resp.status_code}")

# Step 5: 对比
print_section("Step 5: 新老用户对比")

NEW_USER = "brand_new_" + str(int(time.time()))

old_resp = httpx.post(f"{BASE_URL}/api/embedding/recommend/v2", json={
    "persona_type": "健康达人", "user_id": USER_ID, "top_k": 3,
    "enable_behavior": True, "enable_customization": True
}, timeout=60)

new_resp = httpx.post(f"{BASE_URL}/api/embedding/recommend/v2", json={
    "persona_type": "健康达人", "user_id": NEW_USER, "top_k": 3,
    "enable_behavior": True, "enable_customization": True
}, timeout=60)

if old_resp.status_code == 200 and new_resp.status_code == 200:
    old_recs = old_resp.json().get("recommendations", [])
    new_recs = new_resp.json().get("recommendations", [])
    
    old_cust = sum(r.get("score_breakdown", {}).get("customization_multiplier", 1.0) for r in old_recs) / max(len(old_recs), 1)
    new_cust = sum(r.get("score_breakdown", {}).get("customization_multiplier", 1.0) for r in new_recs) / max(len(new_recs), 1)
    
    print(f"\n老用户 (有订单历史):")
    for r in old_recs:
        c = r.get("score_breakdown", {}).get("customization_multiplier", 1.0)
        print(f"  {r['item']['name']:<12} 客制化权重: ×{c:.2f}")
    print(f"  平均: ×{old_cust:.2f}")
    
    print(f"\n新用户 (无订单历史):")
    for r in new_recs:
        c = r.get("score_breakdown", {}).get("customization_multiplier", 1.0)
        print(f"  {r['item']['name']:<12} 客制化权重: ×{c:.2f}")
    print(f"  平均: ×{new_cust:.2f}")
    
    diff = (old_cust - new_cust) * 100
    print(f"\n📊 差异: {diff:+.1f}%")
    
    if old_cust > new_cust:
        print("✅ 有客制化偏好的用户获得更高权重")
    elif old_cust < new_cust:
        print("⚠️ 有客制化偏好的用户获得更低权重（需检查匹配逻辑）")
    else:
        print("➡️ 无显著差异")

print("\n" + "="*60 + "\n")
