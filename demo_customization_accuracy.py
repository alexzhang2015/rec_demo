#!/usr/bin/env python3
"""
客制化推荐准确性演示脚本
展示如何验证客制化推荐的准确性
"""

import httpx
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000"
USER_ID = "accuracy_demo_user"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_subsection(title):
    print(f"\n--- {title} ---")

# ============================================================
# Step 1: 创建明确客制化偏好的订单历史
# ============================================================
def create_orders_with_preferences():
    print_section("Step 1: 创建带明确客制化偏好的订单历史")
    
    # 定义用户偏好: 冰饮、燕麦奶、无糖/少糖
    orders = []
    
    # 咖啡订单 - 全部冰饮、燕麦奶、无糖
    coffee_items = ["COF001", "COF002", "COF003", "COF004", "COF005", "COF006"]
    for i, sku in enumerate(coffee_items[:4]):
        orders.append({
            "user_id": USER_ID,
            "item_sku": sku,
            "quantity": random.randint(1, 2),
            "order_time": (datetime.now() - timedelta(days=random.randint(1, 20))).isoformat(),
            "customization": {
                "temperature": "ICED",      # 全部冰饮
                "cup_size": "GRANDE",       # 全部大杯
                "sugar_level": "NONE" if i % 3 != 2 else "LIGHT",  # 主要无糖
                "milk_type": "OAT"          # 全部燕麦奶
            }
        })
    
    # 茶饮订单 - 冰饮、无糖
    tea_items = ["TEA001", "TEA002", "TEA003"]
    for sku in tea_items[:2]:
        orders.append({
            "user_id": USER_ID,
            "item_sku": sku,
            "quantity": 1,
            "order_time": (datetime.now() - timedelta(days=random.randint(5, 15))).isoformat(),
            "customization": {
                "temperature": "ICED",
                "cup_size": "GRANDE",
                "sugar_level": "NONE"
            }
        })
    
    # 批量提交订单
    resp = httpx.post(f"{BASE_URL}/api/orders/batch", json={"orders": orders}, timeout=30)
    result = resp.json()
    
    print(f"✅ 创建了 {len(orders)} 笔订单")
    print(f"   客制化偏好设定:")
    print(f"   - 温度: 100% 冰饮 (ICED)")
    print(f"   - 奶类: 100% 燕麦奶 (OAT)")
    print(f"   - 糖度: ~83% 无糖 (NONE), ~17% 少糖 (LIGHT)")
    print(f"   - 杯型: 100% 大杯 (GRANDE)")
    
    return orders

# ============================================================
# Step 2: 验证客制化偏好被正确提取
# ============================================================
def verify_preference_extraction():
    print_section("Step 2: 验证客制化偏好提取准确性")
    
    resp = httpx.get(f"{BASE_URL}/api/behavior/user/{USER_ID}", timeout=30)
    data = resp.json()
    
    if "customization_preference" in data:
        cp = data["customization_preference"]
        
        print_subsection("温度偏好")
        if cp.get("temperature_preference"):
            for temp, ratio in sorted(cp["temperature_preference"].items(), key=lambda x: -x[1]):
                bar = "█" * int(ratio * 20)
                status = "✅ 符合预期" if temp == "ICED" and ratio > 0.9 else ""
                print(f"   {temp:10} {bar} {ratio*100:5.1f}% {status}")
        
        print_subsection("奶类偏好")
        if cp.get("milk_preference"):
            for milk, ratio in sorted(cp["milk_preference"].items(), key=lambda x: -x[1]):
                bar = "█" * int(ratio * 20)
                status = "✅ 符合预期" if milk == "OAT" and ratio > 0.9 else ""
                print(f"   {milk:10} {bar} {ratio*100:5.1f}% {status}")
        
        print_subsection("糖度偏好")
        if cp.get("sugar_preference"):
            for sugar, ratio in sorted(cp["sugar_preference"].items(), key=lambda x: -x[1]):
                bar = "█" * int(ratio * 20)
                status = "✅ 符合预期" if sugar == "NONE" and ratio > 0.7 else ""
                print(f"   {sugar:10} {bar} {ratio*100:5.1f}% {status}")
        
        print_subsection("客制化关键词")
        if data.get("customization_keywords"):
            for kw in data["customization_keywords"]:
                print(f"   🏷️  {kw}")
        
        return cp
    else:
        print("❌ 未找到客制化偏好数据")
        return None

# ============================================================
# Step 3: 验证推荐中的客制化权重
# ============================================================
def verify_customization_weights():
    print_section("Step 3: 验证推荐中的客制化权重")
    
    # 获取菜单，了解哪些商品支持燕麦奶
    menu_resp = httpx.get(f"{BASE_URL}/api/menu", timeout=30)
    menu_items = menu_resp.json().get("items", [])
    
    # 找出支持燕麦奶的商品
    oat_supported = set()
    for item in menu_items:
        constraints = item.get("customization_constraints", {})
        if constraints and "OAT" in constraints.get("available_milk_types", []):
            oat_supported.add(item["sku"])
    
    print(f"📋 支持燕麦奶的商品: {len(oat_supported)} 个")
    
    # 获取推荐
    rec_resp = httpx.post(f"{BASE_URL}/api/embedding/recommend/v2", json={
        "persona_type": "咖啡重度用户",
        "user_id": USER_ID,
        "top_k": 6,
        "enable_behavior": True,
        "enable_customization": True
    }, timeout=60)
    rec_data = rec_resp.json()
    
    print_subsection("推荐结果与客制化权重")
    print(f"{'排名':<4} {'商品':<12} {'最终分':<8} {'客制化权重':<12} {'支持燕麦奶':<10} {'准确性'}")
    print("-" * 70)
    
    accurate_count = 0
    for i, rec in enumerate(rec_data.get("recommendations", [])[:6]):
        item = rec["item"]
        breakdown = rec.get("score_breakdown", {})
        cust_mult = breakdown.get("customization_multiplier", 1.0)
        supports_oat = item["sku"] in oat_supported
        
        # 检查准确性：支持燕麦奶的商品应该有较高的客制化权重
        if supports_oat and cust_mult >= 1.0:
            accuracy = "✅"
            accurate_count += 1
        elif not supports_oat and cust_mult < 1.0:
            accuracy = "✅"
            accurate_count += 1
        else:
            accuracy = "⚠️"
        
        oat_icon = "✓" if supports_oat else "✗"
        print(f"{i+1:<4} {item['name']:<12} {rec['match_score']*100:>6.1f}% {cust_mult:>10.2f}× {oat_icon:<10} {accuracy}")
    
    print(f"\n📊 客制化权重准确率: {accurate_count}/6 = {accurate_count/6*100:.0f}%")
    
    return rec_data

# ============================================================
# Step 4: 验证推荐的客制化组合建议
# ============================================================
def verify_suggested_customization(rec_data):
    print_section("Step 4: 验证推荐的客制化组合建议")
    
    print("预期: 基于用户历史，应推荐 冰饮 + 大杯 + 无糖 + 燕麦奶\n")
    
    accurate_count = 0
    total_with_suggestion = 0
    
    for i, rec in enumerate(rec_data.get("recommendations", [])[:3]):
        item = rec["item"]
        suggested = rec.get("suggested_customization", {})
        
        print(f"🥤 {i+1}. {item['name']}")
        
        if suggested and suggested.get("suggested_customization"):
            total_with_suggestion += 1
            sc = suggested["suggested_customization"]
            confidence = suggested.get("confidence", 0)
            reason = suggested.get("reason", "")
            
            # 检查各项是否符合预期
            checks = []
            if sc.get("temperature") == "ICED":
                checks.append(("温度", "ICED ☑️", True))
            elif sc.get("temperature"):
                checks.append(("温度", f"{sc['temperature']} ✗", False))
            
            if sc.get("cup_size") == "GRANDE":
                checks.append(("杯型", "GRANDE ☑️", True))
            elif sc.get("cup_size"):
                checks.append(("杯型", f"{sc['cup_size']} ⚠️", False))
            
            if sc.get("sugar_level") in ["NONE", "LIGHT"]:
                checks.append(("糖度", f"{sc['sugar_level']} ☑️", True))
            elif sc.get("sugar_level"):
                checks.append(("糖度", f"{sc['sugar_level']} ✗", False))
            
            if sc.get("milk_type") == "OAT":
                checks.append(("奶类", "OAT ☑️", True))
            elif sc.get("milk_type"):
                checks.append(("奶类", f"{sc['milk_type']} ⚠️", False))
            
            correct = sum(1 for _, _, ok in checks if ok)
            if correct >= 3:
                accurate_count += 1
            
            print(f"   置信度: {confidence*100:.0f}%")
            for label, value, _ in checks:
                print(f"   {label}: {value}")
            print(f"   理由: {reason}")
            print(f"   匹配度: {correct}/{len(checks)}")
        else:
            print("   (无客制化建议)")
        print()
    
    if total_with_suggestion > 0:
        print(f"📊 客制化建议准确率: {accurate_count}/{total_with_suggestion} = {accurate_count/total_with_suggestion*100:.0f}%")

# ============================================================
# Step 5: 对比有/无客制化偏好的用户
# ============================================================
def compare_with_new_user():
    print_section("Step 5: 对比有/无客制化偏好的用户")
    
    NEW_USER = "brand_new_user_no_history"
    
    # 获取老用户推荐
    old_resp = httpx.post(f"{BASE_URL}/api/embedding/recommend/v2", json={
        "persona_type": "健康达人",
        "user_id": USER_ID,
        "top_k": 3,
        "enable_behavior": True,
        "enable_customization": True
    }, timeout=60)
    
    # 获取新用户推荐
    new_resp = httpx.post(f"{BASE_URL}/api/embedding/recommend/v2", json={
        "persona_type": "健康达人",
        "user_id": NEW_USER,
        "top_k": 3,
        "enable_behavior": True,
        "enable_customization": True
    }, timeout=60)
    
    old_recs = old_resp.json().get("recommendations", [])
    new_recs = new_resp.json().get("recommendations", [])
    
    print_subsection("老用户 (有客制化历史)")
    print(f"{'商品':<12} {'最终分':<8} {'客制化权重':<12} {'推荐组合'}")
    print("-" * 60)
    for rec in old_recs:
        item = rec["item"]
        breakdown = rec.get("score_breakdown", {})
        cust_mult = breakdown.get("customization_multiplier", 1.0)
        suggested = rec.get("suggested_customization", {}).get("suggested_customization", {})
        combo = []
        if suggested.get("temperature"): combo.append(suggested["temperature"])
        if suggested.get("milk_type"): combo.append(suggested["milk_type"])
        if suggested.get("sugar_level"): combo.append(suggested["sugar_level"])
        combo_str = " + ".join(combo) if combo else "-"
        print(f"{item['name']:<12} {rec['match_score']*100:>6.1f}% {cust_mult:>10.2f}× {combo_str}")
    
    print_subsection("新用户 (无客制化历史)")
    print(f"{'商品':<12} {'最终分':<8} {'客制化权重':<12} {'推荐组合'}")
    print("-" * 60)
    for rec in new_recs:
        item = rec["item"]
        breakdown = rec.get("score_breakdown", {})
        cust_mult = breakdown.get("customization_multiplier", 1.0)
        suggested = rec.get("suggested_customization", {}).get("suggested_customization", {})
        combo = []
        if suggested.get("temperature"): combo.append(suggested["temperature"])
        if suggested.get("milk_type"): combo.append(suggested["milk_type"])
        if suggested.get("sugar_level"): combo.append(suggested["sugar_level"])
        combo_str = " + ".join(combo) if combo else "-"
        print(f"{item['name']:<12} {rec['match_score']*100:>6.1f}% {cust_mult:>10.2f}× {combo_str}")
    
    # 计算差异
    old_avg_cust = sum(r.get("score_breakdown", {}).get("customization_multiplier", 1.0) for r in old_recs) / len(old_recs)
    new_avg_cust = sum(r.get("score_breakdown", {}).get("customization_multiplier", 1.0) for r in new_recs) / len(new_recs)
    
    print_subsection("对比结论")
    print(f"老用户平均客制化权重: {old_avg_cust:.2f}×")
    print(f"新用户平均客制化权重: {new_avg_cust:.2f}×")
    print(f"差异: {(old_avg_cust - new_avg_cust)*100:+.1f}%")
    
    if old_avg_cust != new_avg_cust:
        print("\n✅ 客制化推荐正在发挥作用 - 有历史偏好的用户获得了差异化的权重")
    else:
        print("\n⚠️ 客制化权重未体现差异")

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("     客制化推荐准确性演示")
    print("="*60)
    
    create_orders_with_preferences()
    verify_preference_extraction()
    rec_data = verify_customization_weights()
    verify_suggested_customization(rec_data)
    compare_with_new_user()
    
    print("\n" + "="*60)
    print("     演示完成")
    print("="*60 + "\n")
