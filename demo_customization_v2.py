#!/usr/bin/env python3
"""客制化推荐准确性演示 - 简化版"""
import httpx
import json
from datetime import datetime, timedelta
import random
import time

BASE_URL = "http://localhost:8000"
USER_ID = "cust_demo_" + str(int(time.time()))

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

print_section("客制化推荐准确性演示")
print(f"测试用户ID: {USER_ID}")

# ============================================================
# Step 1: 创建有明确客制化偏好的订单
# ============================================================
print_section("Step 1: 创建带客制化偏好的订单历史")

orders = []
for i in range(8):
    orders.append({
        "user_id": USER_ID,
        "item_sku": ["COF001", "COF002", "COF003", "COF004", "TEA001", "TEA002"][i % 6],
        "quantity": 1,
        "order_time": (datetime.now() - timedelta(days=i*2)).isoformat(),
        "customization": {
            "temperature": "ICED",           # 全部冰饮
            "cup_size": "GRANDE",            # 全部大杯
            "sugar_level": "NONE" if i % 4 != 3 else "LIGHT",  # 75%无糖
            "milk_type": "OAT"               # 全部燕麦奶
        }
    })

try:
    resp = httpx.post(f"{BASE_URL}/api/orders/batch", json={"orders": orders}, timeout=30)
    print(f"✅ 创建了 {len(orders)} 笔订单")
    print(f"   偏好设定: 100% 冰饮, 100% 燕麦奶, 75% 无糖, 100% 大杯")
except Exception as e:
    print(f"❌ 创建订单失败: {e}")

# ============================================================
# Step 2: 获取用户行为数据
# ============================================================
print_section("Step 2: 验证偏好提取")

try:
    time.sleep(1)
    resp = httpx.get(f"{BASE_URL}/api/behavior/user/{USER_ID}", timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        cp = data.get("customization_preference", {})
        
        if cp.get("temperature_preference"):
            print("\n温度偏好:")
            for t, v in sorted(cp["temperature_preference"].items(), key=lambda x: -x[1]):
                bar = "█" * int(v * 20)
                check = "✅" if t == "ICED" and v >= 0.9 else ""
                print(f"  {t:10} {bar} {v*100:5.1f}% {check}")
        
        if cp.get("milk_preference"):
            print("\n奶类偏好:")
            for m, v in sorted(cp["milk_preference"].items(), key=lambda x: -x[1]):
                bar = "█" * int(v * 20)
                check = "✅" if m == "OAT" and v >= 0.9 else ""
                print(f"  {m:10} {bar} {v*100:5.1f}% {check}")
        
        if cp.get("sugar_preference"):
            print("\n糖度偏好:")
            for s, v in sorted(cp["sugar_preference"].items(), key=lambda x: -x[1]):
                bar = "█" * int(v * 20)
                check = "✅" if s == "NONE" and v >= 0.6 else ""
                print(f"  {s:10} {bar} {v*100:5.1f}% {check}")
        
        kws = data.get("customization_keywords", [])
        if kws:
            print("\n客制化关键词:")
            for kw in kws:
                print(f"  🏷️  {kw}")
    else:
        print(f"⚠️ API返回状态码: {resp.status_code}")
        print(resp.text[:200])
except Exception as e:
    print(f"❌ 获取行为数据失败: {e}")

# ============================================================
# Step 3: 验证推荐中的客制化权重
# ============================================================
print_section("Step 3: 验证推荐中的客制化权重")

try:
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
        
        print(f"\n{'排名':<4} {'商品':<12} {'最终分':<8} {'客制化权重':<12}")
        print("-" * 50)
        
        for i, rec in enumerate(recs):
            item = rec["item"]
            bd = rec.get("score_breakdown", {})
            cust = bd.get("customization_multiplier", 1.0)
            cust_str = f"×{cust:.2f}" + (" ⬆️" if cust > 1.0 else " ⬇️" if cust < 1.0 else "")
            print(f"{i+1:<4} {item['name']:<12} {rec['match_score']*100:>5.1f}% {cust_str:<12}")
    else:
        print(f"❌ 推荐API错误: {rec_resp.status_code}")
except Exception as e:
    print(f"❌ 获取推荐失败: {e}")

# ============================================================
# Step 4: 验证推荐客制化建议
# ============================================================
print_section("Step 4: 验证推荐的客制化建议")

try:
    if rec_resp.status_code == 200:
        recs = rec_data.get("recommendations", [])[:3]
        
        print("预期: 基于历史偏好，应推荐 ICED + GRANDE + NONE/LIGHT + OAT\n")
        
        for i, rec in enumerate(recs):
            item = rec["item"]
            sg = rec.get("suggested_customization", {})
            
            print(f"🥤 {i+1}. {item['name']}")
            
            if sg and sg.get("suggested_customization"):
                sc = sg["suggested_customization"]
                conf = sg.get("confidence", 0)
                
                checks = []
                if sc.get("temperature") == "ICED":
                    checks.append("温度: ICED ✓")
                elif sc.get("temperature"):
                    checks.append(f"温度: {sc['temperature']} ✗")
                    
                if sc.get("milk_type") == "OAT":
                    checks.append("奶类: OAT ✓")
                elif sc.get("milk_type"):
                    checks.append(f"奶类: {sc['milk_type']} ✗")
                    
                if sc.get("sugar_level") in ["NONE", "LIGHT"]:
                    checks.append(f"糖度: {sc['sugar_level']} ✓")
                elif sc.get("sugar_level"):
                    checks.append(f"糖度: {sc['sugar_level']} ✗")
                
                print(f"   置信度: {conf*100:.0f}%")
                for c in checks:
                    print(f"   {c}")
                if sg.get("reason"):
                    print(f"   理由: {sg['reason']}")
            else:
                print("   (无客制化建议)")
            print()
except Exception as e:
    print(f"❌ 验证客制化建议失败: {e}")

# ============================================================
# Step 5: 对比新老用户
# ============================================================
print_section("Step 5: 新老用户对比")

NEW_USER = "brand_new_" + str(int(time.time()))

try:
    # 老用户推荐
    old_resp = httpx.post(f"{BASE_URL}/api/embedding/recommend/v2", json={
        "persona_type": "健康达人",
        "user_id": USER_ID,
        "top_k": 3,
        "enable_behavior": True,
        "enable_customization": True
    }, timeout=60)
    
    # 新用户推荐
    new_resp = httpx.post(f"{BASE_URL}/api/embedding/recommend/v2", json={
        "persona_type": "健康达人",
        "user_id": NEW_USER,
        "top_k": 3,
        "enable_behavior": True,
        "enable_customization": True
    }, timeout=60)
    
    if old_resp.status_code == 200 and new_resp.status_code == 200:
        old_recs = old_resp.json().get("recommendations", [])
        new_recs = new_resp.json().get("recommendations", [])
        
        old_cust = sum(r.get("score_breakdown", {}).get("customization_multiplier", 1.0) for r in old_recs) / max(len(old_recs), 1)
        new_cust = sum(r.get("score_breakdown", {}).get("customization_multiplier", 1.0) for r in new_recs) / max(len(new_recs), 1)
        
        print(f"\n老用户 ({USER_ID[:15]}...):")
        for r in old_recs:
            cust = r.get("score_breakdown", {}).get("customization_multiplier", 1.0)
            print(f"  {r['item']['name']:<12} 客制化权重: ×{cust:.2f}")
        print(f"  平均客制化权重: ×{old_cust:.2f}")
        
        print(f"\n新用户 ({NEW_USER[:15]}...):")
        for r in new_recs:
            cust = r.get("score_breakdown", {}).get("customization_multiplier", 1.0)
            print(f"  {r['item']['name']:<12} 客制化权重: ×{cust:.2f}")
        print(f"  平均客制化权重: ×{new_cust:.2f}")
        
        diff = (old_cust - new_cust) * 100
        print(f"\n📊 差异: {diff:+.1f}%")
        
        if abs(diff) > 1:
            print("✅ 客制化推荐发挥作用 - 有偏好历史的用户获得差异化权重")
        else:
            print("⚠️ 新老用户客制化权重无显著差异")
except Exception as e:
    print(f"❌ 对比失败: {e}")

print("\n" + "="*60)
print("  演示完成")
print("="*60 + "\n")
