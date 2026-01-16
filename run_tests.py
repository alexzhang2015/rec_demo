#!/usr/bin/env python3
"""全面测试 SQLite 迁移"""
import asyncio
import os
import sys
import sqlite3
import json

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

async def test_database_init():
    """测试数据库初始化"""
    print_header("测试 1: 数据库初始化")

    db_path = 'app/data/recommendation.db'

    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ 删除旧数据库")

    from app.db import init_db, close_db
    await init_db()

    # 验证表
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    expected_tables = [
        'cart_items', 'carts', 'completed_order_items', 'completed_orders',
        'experiment_variants', 'experiments', 'feedback_stats', 'migration_status',
        'order_stats', 'orders', 'sqlite_sequence', 'user_behavior',
        'user_feedback', 'user_presets'
    ]

    print(f"创建的表: {len(tables)}个")

    missing = set(expected_tables) - set(tables)
    if missing:
        print(f"❌ 缺少表: {missing}")
        return False

    print("✅ 数据库初始化测试通过")
    return True

async def test_ab_test_service():
    """测试 ABTestService"""
    print_header("测试 2: ABTestService")

    from app.experiment_service import ABTestService
    service = ABTestService()

    # 测试获取所有实验
    experiments = await service.get_all_experiments_async()
    print(f"实验数量: {len(experiments)}")

    if len(experiments) < 1:
        print("❌ 没有找到实验")
        return False

    # 测试获取变体
    variant = await service.get_variant_async("test_user_123", "rec_algorithm")
    print(f"用户变体: {variant}")

    if not variant or 'variant' not in variant:
        print("❌ 无法获取变体")
        return False

    print("✅ ABTestService 测试通过")
    return True

async def test_feedback_service():
    """测试 FeedbackService"""
    print_header("测试 3: FeedbackService")

    from app.experiment_service import FeedbackService, UserFeedback
    service = FeedbackService()

    # 测试记录反馈
    feedback = UserFeedback(
        user_id="test_user",
        session_id="test_session",
        item_sku="TEA001",
        feedback_type="like"
    )
    result = await service.record_feedback_async(feedback)
    print(f"记录反馈: {result['status']}")

    if result['status'] != 'recorded':
        print("❌ 记录反馈失败")
        return False

    # 测试获取统计
    stats = await service.get_item_stats_async("TEA001")
    print(f"商品统计: likes={stats['likes']}, dislikes={stats['dislikes']}")

    if stats['likes'] < 1:
        print("❌ 统计数据不正确")
        return False

    # 测试 dislike
    feedback2 = UserFeedback(
        user_id="test_user2",
        session_id="test_session2",
        item_sku="TEA001",
        feedback_type="dislike"
    )
    await service.record_feedback_async(feedback2)

    stats = await service.get_item_stats_async("TEA001")
    print(f"更新后统计: likes={stats['likes']}, dislikes={stats['dislikes']}")

    print("✅ FeedbackService 测试通过")
    return True

async def test_behavior_service():
    """测试 BehaviorService"""
    print_header("测试 4: BehaviorService")

    from app.experiment_service import BehaviorService, OrderRecord
    service = BehaviorService()

    # 测试记录订单
    order = OrderRecord(
        user_id="test_user",
        session_id="test_session",
        item_sku="COF001",
        item_name="经典美式",
        category="咖啡",
        base_price=28.0,
        final_price=28.0
    )
    result = await service.record_order_async(order)
    print(f"记录订单: {result['status']}, order_id={result['order_id']}")

    if result['status'] != 'recorded':
        print("❌ 记录订单失败")
        return False

    # 测试获取用户订单
    orders = await service.get_user_orders_async("test_user")
    print(f"用户订单数: {len(orders)}")

    if len(orders) < 1:
        print("❌ 获取订单失败")
        return False

    # 测试用户画像
    profile = await service.get_user_profile_async("test_user")
    print(f"用户画像: is_new={profile['is_new_user']}, orders={profile['order_count']}")

    # 测试推荐加权
    boost = await service.get_order_based_recommendation_boost_async(
        "test_user", "COF001", "咖啡", ["经典", "低卡"]
    )
    print(f"推荐加权: {boost}")

    print("✅ BehaviorService 测试通过")
    return True

async def test_preset_service():
    """测试 PresetService"""
    print_header("测试 5: PresetService")

    from app.experiment_service import PresetService
    service = PresetService()

    # 测试创建预设
    preset_data = {
        "user_id": "test_user",
        "name": "我的冰美式",
        "default_temperature": "冰",
        "default_cup_size": "大杯",
        "default_sugar_level": "无糖"
    }
    result = await service.create_preset_async(preset_data)
    preset = result['preset']
    print(f"创建预设: {preset['name']}, id={preset['preset_id']}")

    if not preset['preset_id']:
        print("❌ 创建预设失败")
        return False

    preset_id = preset['preset_id']

    # 测试获取预设
    presets = await service.get_user_presets_async("test_user")
    print(f"用户预设数: {len(presets)}")

    if len(presets) < 1:
        print("❌ 获取预设失败")
        return False

    # 测试更新预设
    update_data = {
        "name": "我的热拿铁",
        "default_temperature": "热"
    }
    updated_result = await service.update_preset_async(preset_id, update_data)
    print(f"更新预设: {updated_result['preset']['name']}")

    # 测试删除预设
    deleted = await service.delete_preset_async(preset_id)
    print(f"删除预设: {deleted['status']}")

    print("✅ PresetService 测试通过")
    return True

async def test_cart_service():
    """测试 CartService"""
    print_header("测试 6: CartService")

    from app.cart_service import CartService
    from app.models import AddToCartRequest
    service = CartService()

    session_id = "test_cart_session"

    # 测试添加商品
    request = AddToCartRequest(
        session_id=session_id,
        item_sku="COF001",
        quantity=2
    )
    result = await service.add_to_cart_async(request)
    print(f"添加购物车: {result['status']}, items={len(result['cart']['items'])}")

    if result['status'] != 'added':
        print("❌ 添加购物车失败")
        return False

    # 测试获取购物车
    cart = await service.get_cart_async(session_id)
    print(f"购物车: items={len(cart.items)}, total={cart.total_price}")

    # 测试更新数量
    from app.models import UpdateCartItemRequest
    item_id = cart.items[0].id
    update_request = UpdateCartItemRequest(quantity=3)
    updated = await service.update_cart_item_async(session_id, item_id, update_request)
    print(f"更新数量: total_items={updated['cart']['total_items']}")

    # 测试结账
    from app.models import CheckoutRequest
    checkout_request = CheckoutRequest(session_id=session_id, user_id="test_user")
    order = await service.checkout_async(checkout_request)
    print(f"结账: order_id={order['order_id']}, status={order['status']}")

    if order['status'] not in ('CONFIRMED', 'success'):
        print("❌ 结账失败")
        return False

    # 验证购物车清空
    cart = await service.get_cart_async(session_id)
    print(f"结账后购物车: items={len(cart.items)}")

    # 测试获取订单统计
    stats = await service.get_order_stats_async()
    print(f"订单统计: total_orders={stats['total_orders']}, revenue={stats['total_revenue']}")

    print("✅ CartService 测试通过")
    return True

async def test_api_endpoints():
    """测试 API 端点"""
    print_header("测试 7: API 端点")

    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        # 测试菜单
        r = client.get("/api/menu")
        print(f"GET /api/menu: {r.status_code}")
        if r.status_code != 200:
            print("❌ 菜单 API 失败")
            return False

        # 测试实验
        r = client.get("/api/experiments")
        print(f"GET /api/experiments: {r.status_code}, count={len(r.json().get('experiments', []))}")
        if r.status_code != 200:
            print("❌ 实验 API 失败")
            return False

        # 测试购物车添加
        r = client.post("/api/cart/add", json={
            "session_id": "api_test",
            "item_sku": "TEA002",
            "quantity": 1
        })
        print(f"POST /api/cart/add: {r.status_code}")
        if r.status_code != 200:
            print("❌ 购物车添加 API 失败")
            return False

        # 测试购物车获取
        r = client.get("/api/cart/api_test")
        print(f"GET /api/cart/api_test: {r.status_code}")
        if r.status_code != 200:
            print("❌ 购物车获取 API 失败")
            return False

        # 测试反馈
        r = client.post("/api/feedback", json={
            "user_id": "api_user",
            "session_id": "api_session",
            "item_sku": "COF002",
            "feedback_type": "click"
        })
        print(f"POST /api/feedback: {r.status_code}")
        if r.status_code != 200:
            print("❌ 反馈 API 失败")
            return False

    print("✅ API 端点测试通过")
    return True

async def test_v2_recommendation():
    """测试 V2 推荐 API"""
    print_header("测试 8: V2 推荐 API")

    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        r = client.post("/api/embedding/recommend/v2", json={
            "persona_type": "健康达人",
            "user_id": "rec_test_user",
            "enable_ab_test": True
        })
        print(f"POST /api/embedding/recommend/v2: {r.status_code}")

        if r.status_code != 200:
            print("❌ V2 推荐 API 失败")
            return False

        data = r.json()
        recs = data.get("recommendations", [])
        print(f"推荐数量: {len(recs)}")

        if len(recs) > 0:
            print(f"第一个推荐: {recs[0].get('reason', 'N/A')[:50]}...")

    print("✅ V2 推荐 API 测试通过")
    return True

async def verify_sqlite_data():
    """验证 SQLite 数据"""
    print_header("验证: SQLite 数据持久化")

    conn = sqlite3.connect('app/data/recommendation.db')
    cursor = conn.cursor()

    checks = [
        ("experiments", "SELECT COUNT(*) FROM experiments"),
        ("experiment_variants", "SELECT COUNT(*) FROM experiment_variants"),
        ("user_feedback", "SELECT COUNT(*) FROM user_feedback"),
        ("feedback_stats", "SELECT COUNT(*) FROM feedback_stats"),
        ("orders", "SELECT COUNT(*) FROM orders"),
        ("carts", "SELECT COUNT(*) FROM carts"),
        ("completed_orders", "SELECT COUNT(*) FROM completed_orders"),
    ]

    for name, query in checks:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"  {name}: {count} 条记录")

    conn.close()
    print("✅ SQLite 数据验证完成")
    return True

async def main():
    print("\n" + "="*60)
    print("  SQLite 迁移全面测试")
    print("="*60)

    results = []

    # 运行所有测试
    tests = [
        ("数据库初始化", test_database_init),
        ("ABTestService", test_ab_test_service),
        ("FeedbackService", test_feedback_service),
        ("BehaviorService", test_behavior_service),
        ("PresetService", test_preset_service),
        ("CartService", test_cart_service),
        ("API 端点", test_api_endpoints),
        ("V2 推荐", test_v2_recommendation),
        ("数据验证", verify_sqlite_data),
    ]

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 汇总
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！SQLite 迁移验证成功！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
