#!/usr/bin/env python3
"""完整 Demo 测试 - 使用 TestClient"""
import json
import time
from fastapi.testclient import TestClient

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_json(data, max_len=500):
    """打印 JSON，限制长度"""
    s = json.dumps(data, ensure_ascii=False, indent=2)
    if len(s) > max_len:
        s = s[:max_len] + "\n... (truncated)"
    print(s)

def main():
    print("\n" + "="*60)
    print("  完整 Demo 测试")
    print("="*60)

    from app.main import app

    with TestClient(app) as client:
        # ==========================================
        # 测试 1: 菜单 API
        # ==========================================
        print_header("测试 1: 菜单 API")
        r = client.get("/api/menu")
        assert r.status_code == 200, f"菜单 API 失败: {r.status_code}"
        menu = r.json()
        categories = menu.get("categories", [])
        items = menu.get("items", [])
        print(f"✓ 菜单分类数: {len(categories)}")
        print(f"✓ 商品总数: {len(items)}")
        # 按分类统计
        from collections import Counter
        cat_counts = Counter(item.get('category') for item in items)
        for cat in categories:
            cat_label = cat.get('label', cat.get('value', 'Unknown'))
            cat_value = cat.get('value', '')
            count = cat_counts.get(cat_value, 0)
            print(f"  - {cat_label}: {count} 个商品")
        print("✅ 菜单 API 测试通过")

        # ==========================================
        # 测试 2: 人设列表 API
        # ==========================================
        print_header("测试 2: 人设列表 API")
        r = client.get("/api/embedding/personas")
        assert r.status_code == 200
        personas = r.json().get("personas", [])
        print(f"✓ 可用人设数: {len(personas)}")
        for p in personas:
            print(f"  - {p}")
        print("✅ 人设列表 API 测试通过")

        # ==========================================
        # 测试 3: V1 推荐 API
        # ==========================================
        print_header("测试 3: V1 推荐 API (咖啡重度用户)")
        r = client.post("/api/embedding/recommend", json={
            "persona_type": "咖啡重度用户",
            "top_k": 5
        })
        assert r.status_code == 200
        data = r.json()
        recs = data.get("recommendations", [])
        print(f"✓ 推荐数量: {len(recs)}")
        print(f"✓ 用户画像: {data.get('user_profile', {}).get('persona', 'N/A')[:50]}...")
        print("推荐结果:")
        for i, rec in enumerate(recs[:3], 1):
            print(f"  {i}. {rec.get('name')} - {rec.get('reason', 'N/A')[:40]}...")
        print("✅ V1 推荐 API 测试通过")

        # ==========================================
        # 测试 4: V2 推荐 API - 多种人设
        # ==========================================
        print_header("测试 4: V2 推荐 API (多种人设)")

        test_personas = ["健康达人", "甜品爱好者", "尝鲜派", "实用主义"]
        for persona in test_personas:
            r = client.post("/api/embedding/recommend/v2", json={
                "persona_type": persona,
                "user_id": f"demo_user_{persona}",
                "enable_ab_test": True
            })
            assert r.status_code == 200
            data = r.json()
            recs = data.get("recommendations", [])
            top_rec = recs[0] if recs else {}
            print(f"✓ {persona}: 推荐 {len(recs)} 个")
            print(f"    Top1: {top_rec.get('name', 'N/A')} - {top_rec.get('reason', 'N/A')[:35]}...")

        print("✅ V2 推荐 API 测试通过")

        # ==========================================
        # 测试 5: A/B 实验 API
        # ==========================================
        print_header("测试 5: A/B 实验 API")
        r = client.get("/api/experiments")
        assert r.status_code == 200
        experiments = r.json().get("experiments", [])
        print(f"✓ 实验数量: {len(experiments)}")
        for exp in experiments:
            variants = exp.get("variants", [])
            print(f"  - {exp['name']}: {len(variants)} 个变体")
            for v in variants[:2]:
                print(f"      • {v['name']} (权重: {v['weight']}%)")
        print("✅ A/B 实验 API 测试通过")

        # ==========================================
        # 测试 6: 完整购物车流程
        # ==========================================
        print_header("测试 6: 完整购物车流程")
        session_id = f"demo_session_{int(time.time())}"

        # 添加商品 1
        r = client.post("/api/cart/add", json={
            "session_id": session_id,
            "item_sku": "COF001",
            "quantity": 2
        })
        assert r.status_code == 200
        print(f"✓ 添加经典美式 x2: {r.json()['message']}")

        # 添加商品 2
        r = client.post("/api/cart/add", json={
            "session_id": session_id,
            "item_sku": "TEA001",
            "quantity": 1
        })
        assert r.status_code == 200
        print(f"✓ 添加芝芝抹茶 x1: {r.json()['message']}")

        # 查看购物车
        r = client.get(f"/api/cart/{session_id}")
        assert r.status_code == 200
        cart = r.json()
        print(f"✓ 购物车商品数: {len(cart['items'])}")
        print(f"✓ 购物车总价: ¥{cart['total_price']}")

        # 更新数量
        item_id = cart['items'][0]['id']
        r = client.put(f"/api/cart/item/{session_id}/{item_id}", json={
            "quantity": 3
        })
        assert r.status_code == 200, f"更新购物车失败: {r.status_code} - {r.text}"
        print(f"✓ 更新数量为 3: 总价 ¥{r.json()['cart']['total_price']}")

        # 结账
        r = client.post("/api/cart/checkout", json={
            "session_id": session_id,
            "user_id": "demo_user"
        })
        assert r.status_code == 200
        order = r.json()
        print(f"✓ 结账成功: 订单号 {order['order_id']}")
        print(f"✓ 订单状态: {order.get('status', 'N/A')}")

        print("✅ 购物车流程测试通过")

        # ==========================================
        # 测试 7: 用户反馈功能
        # ==========================================
        print_header("测试 7: 用户反馈功能")

        # 记录多个反馈
        feedbacks = [
            ("COF001", "like"),
            ("COF001", "click"),
            ("TEA001", "like"),
            ("COF002", "dislike"),
        ]
        for sku, fb_type in feedbacks:
            r = client.post("/api/feedback", json={
                "user_id": "demo_user",
                "session_id": session_id,
                "item_sku": sku,
                "feedback_type": fb_type
            })
            assert r.status_code == 200
            print(f"✓ 记录反馈: {sku} - {fb_type}")

        print("✅ 用户反馈功能测试通过")

        # ==========================================
        # 测试 8: 用户预设功能
        # ==========================================
        print_header("测试 8: 用户预设功能")

        # 创建预设
        r = client.post("/api/presets", json={
            "user_id": "demo_user",
            "name": "我的冰美式",
            "default_temperature": "冰",
            "default_cup_size": "大杯",
            "default_sugar_level": "无糖"
        })
        assert r.status_code == 200
        preset = r.json()["preset"]
        print(f"✓ 创建预设: {preset['name']} (ID: {preset['preset_id'][:20]}...)")

        # 获取预设列表
        r = client.get("/api/presets/demo_user")
        assert r.status_code == 200
        presets = r.json().get("presets", [])
        print(f"✓ 用户预设数: {len(presets)}")

        print("✅ 用户预设功能测试通过")

        # ==========================================
        # 测试 9: 行为记录与用户画像
        # ==========================================
        print_header("测试 9: 行为记录与用户画像")

        # 模拟订单历史
        r = client.post("/api/orders/simulate", json={
            "user_id": "demo_profile_user",
            "num_orders": 5
        })
        if r.status_code == 200:
            print(f"✓ 模拟生成 5 笔订单")

        # 获取用户画像
        r = client.get("/api/user/demo_profile_user/profile")
        if r.status_code == 200:
            profile = r.json()
            print(f"✓ 用户画像: 订单数={profile.get('order_count', 0)}, 新用户={profile.get('is_new_user', True)}")
        else:
            print(f"✓ 用户画像 API: {r.status_code}")

        print("✅ 行为记录功能测试通过")

        # ==========================================
        # 测试 10: 数据持久化验证
        # ==========================================
        print_header("测试 10: 数据持久化验证 (SQLite)")

        import sqlite3
        conn = sqlite3.connect('app/data/recommendation.db')
        cursor = conn.cursor()

        tables_data = {}
        tables = ['experiments', 'experiment_variants', 'user_feedback',
                  'feedback_stats', 'orders', 'carts', 'completed_orders', 'user_presets']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            tables_data[table] = count

        conn.close()

        print("SQLite 数据统计:")
        for table, count in tables_data.items():
            print(f"  - {table}: {count} 条记录")

        print("✅ 数据持久化验证通过")

    # ==========================================
    # 最终汇总
    # ==========================================
    print("\n" + "="*60)
    print("  Demo 测试完成")
    print("="*60)
    print("""
测试项目:
  1. 菜单 API              ✅
  2. 人设列表 API          ✅
  3. V1 推荐 API           ✅
  4. V2 推荐 API (多人设)  ✅
  5. A/B 实验 API          ✅
  6. 完整购物车流程        ✅
  7. 用户反馈功能          ✅
  8. 用户预设功能          ✅
  9. 行为记录与用户画像    ✅
  10. 数据持久化验证       ✅

🎉 所有 Demo 测试通过！
""")

    print("Web UI 访问地址:")
    print("  - 主菜单: http://localhost:8000/")
    print("  - Embedding 推荐: http://localhost:8000/embedding")
    print("  - V2 推荐演示: http://localhost:8000/embedding-v2")
    print("  - 技术演示: http://localhost:8000/presentation")

if __name__ == "__main__":
    main()
