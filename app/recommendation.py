"""推荐算法服务"""
import random
from collections import Counter
from app.models import MenuItem, Category, UserPreference
from app.data import MENU_ITEMS, get_menu_by_sku


class RecommendationEngine:
    """推荐引擎"""

    def __init__(self):
        self.menu_items = MENU_ITEMS

    def get_recommendations(
        self,
        user_pref: UserPreference | None = None,
        limit: int = 6
    ) -> list[dict]:
        """
        获取个性化推荐

        策略:
        1. 基于用户历史订单的协同过滤
        2. 基于用户偏好标签的内容推荐
        3. 新品和季节限定加权
        4. 多样性保证
        """
        scored_items = []

        for item in self.menu_items:
            score = self._calculate_score(item, user_pref)
            scored_items.append({
                "item": item,
                "score": score,
                "reason": self._get_recommendation_reason(item, user_pref)
            })

        # 按分数排序
        scored_items.sort(key=lambda x: x["score"], reverse=True)

        # 确保多样性 - 每个分类至少有一个
        result = self._ensure_diversity(scored_items, limit)

        return result

    def _calculate_score(
        self,
        item: MenuItem,
        user_pref: UserPreference | None
    ) -> float:
        """计算推荐分数"""
        score = 50.0  # 基础分

        # 新品加分
        if item.is_new:
            score += 15

        # 季节限定加分
        if item.is_seasonal:
            score += 10

        # 人气标签加分
        if "人气" in item.tags:
            score += 10
        if "网红" in item.tags:
            score += 8

        if user_pref:
            # 基于分类偏好
            if item.category in user_pref.favorite_categories:
                score += 20

            # 基于标签偏好
            matching_tags = set(item.tags) & set(user_pref.tags_preference)
            score += len(matching_tags) * 5

            # 基于历史订单 - 购买过的同类商品加分
            if user_pref.order_history:
                history_categories = []
                for sku in user_pref.order_history:
                    hist_item = get_menu_by_sku(sku)
                    if hist_item:
                        history_categories.append(hist_item.category)

                category_counter = Counter(history_categories)
                if item.category in category_counter:
                    score += min(category_counter[item.category] * 3, 15)

        # 添加随机性，避免推荐过于固定
        score += random.uniform(0, 10)

        return score

    def _get_recommendation_reason(
        self,
        item: MenuItem,
        user_pref: UserPreference | None
    ) -> str:
        """获取推荐理由"""
        reasons = []

        if item.is_new:
            reasons.append("新品上市")

        if item.is_seasonal:
            reasons.append("季节限定")

        if "人气" in item.tags:
            reasons.append("人气爆款")

        if "网红" in item.tags:
            reasons.append("网红推荐")

        if user_pref:
            if item.category in user_pref.favorite_categories:
                reasons.append("根据你的喜好")

            matching_tags = set(item.tags) & set(user_pref.tags_preference)
            if matching_tags:
                reasons.append(f"你可能喜欢{list(matching_tags)[0]}")

        if not reasons:
            default_reasons = ["店长推荐", "好评如潮", "经典必点", "口碑之选"]
            reasons.append(random.choice(default_reasons))

        return reasons[0]

    def _ensure_diversity(
        self,
        scored_items: list[dict],
        limit: int
    ) -> list[dict]:
        """确保推荐结果的多样性"""
        result = []
        category_count = {}
        max_per_category = 2  # 每个分类最多2个

        for scored in scored_items:
            item = scored["item"]
            cat = item.category

            if cat not in category_count:
                category_count[cat] = 0

            if category_count[cat] < max_per_category:
                result.append(scored)
                category_count[cat] += 1

            if len(result) >= limit:
                break

        return result

    def get_similar_items(self, sku: str, limit: int = 4) -> list[MenuItem]:
        """获取相似商品"""
        target = get_menu_by_sku(sku)
        if not target:
            return []

        similar = []
        for item in self.menu_items:
            if item.sku == sku:
                continue

            # 计算相似度
            similarity = 0

            # 同分类
            if item.category == target.category:
                similarity += 50

            # 共同标签
            common_tags = set(item.tags) & set(target.tags)
            similarity += len(common_tags) * 10

            # 价格相近
            price_diff = abs(item.base_price - target.base_price)
            if price_diff <= 5:
                similarity += 10

            similar.append((item, similarity))

        similar.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in similar[:limit]]

    def get_category_recommendations(
        self,
        category: Category,
        limit: int = 4
    ) -> list[MenuItem]:
        """获取分类推荐"""
        items = [i for i in self.menu_items if i.category == category]

        # 新品优先，然后按人气
        items.sort(key=lambda x: (x.is_new, "人气" in x.tags), reverse=True)

        return items[:limit]


# 单例
recommendation_engine = RecommendationEngine()
