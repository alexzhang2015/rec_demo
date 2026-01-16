"""
Embedding增强推荐服务

核心流程:
1. LLM生成商品语义描述
2. OpenAI Embedding API生成向量
3. 向量相似度召回
4. 记录完整推理过程

使用OpenAI text-embedding-3-small模型替代TF-IDF
"""
import json
import os
import time
from pathlib import Path
from typing import Optional
import numpy as np

from app.models import MenuItem, Category, Temperature
from app.data import MENU_ITEMS
from app.llm_service import llm_service, get_embedding_service


# 缓存文件路径
CACHE_DIR = Path(__file__).parent / "cache"
ITEM_EMBEDDINGS_CACHE = CACHE_DIR / "item_embeddings.json"


class RealLLMService:
    """真实LLM服务 - 调用OpenAI/Claude API"""

    def __init__(self):
        self.llm = llm_service
        self.provider_info = self.llm.get_info()

        self.persona_templates = {
            "健康达人": {
                "description": "注重健康养生，偏好低糖低卡，关注营养成分",
                "base_keywords": ["低卡", "健康", "无糖", "植物基", "燕麦奶"],
                "avoid": ["高糖", "奶油", "甜蜜"]
            },
            "咖啡重度用户": {
                "description": "每日咖啡刚需，追求咖啡因含量和浓郁口感",
                "base_keywords": ["浓郁", "提神", "咖啡", "浓缩", "美式"],
                "avoid": ["无咖啡因", "茶饮"]
            },
            "甜品爱好者": {
                "description": "喜欢甜蜜口感，注重颜值和拍照分享",
                "base_keywords": ["甜蜜", "网红", "颜值", "奶油", "焦糖"],
                "avoid": ["苦", "无糖"]
            },
            "尝鲜派": {
                "description": "喜欢尝试新品，追求独特体验",
                "base_keywords": ["新品", "限定", "创新", "特色", "独家"],
                "avoid": []
            },
            "实用主义": {
                "description": "注重性价比，偏好经典款式",
                "base_keywords": ["经典", "实惠", "大杯", "人气"],
                "avoid": ["昂贵", "花哨"]
            },
            "养生白领": {
                "description": "办公室工作者，需要提神但也关注健康",
                "base_keywords": ["提神", "低糖", "燕麦奶", "工作", "下午茶"],
                "avoid": ["高糖", "冰"]
            }
        }

    def generate_item_description(self, item: MenuItem) -> dict:
        """使用LLM生成商品的语义描述"""
        start_time = time.time()

        prompt = f"""请为以下星巴克饮品生成详细的语义描述。

饮品信息：
- 名称：{item.name} ({item.english_name})
- 分类：{item.category.value}
- 价格：¥{item.base_price}
- 描述：{item.description}
- 卡路里：{item.calories}
- 标签：{', '.join(item.tags)}
- 可选温度：{', '.join([t.value for t in item.available_temperatures])}
- 是否新品：{'是' if item.is_new else '否'}

请输出JSON格式：
{{
    "semantic_description": "100字以内的详细描述，包含口味、适合人群、场景",
    "keywords": ["关键词1", "关键词2", ...]
}}"""

        result = self.llm.generate_json(prompt, "你是咖啡品鉴专家")
        elapsed_time = time.time() - start_time

        content = result["content"]
        if isinstance(content, dict) and "semantic_description" in content:
            return {
                "sku": item.sku,
                "name": item.name,
                "semantic_description": content.get("semantic_description", item.description),
                "keywords": content.get("keywords", item.tags),
                "processing_time_ms": round(elapsed_time * 1000, 2),
                "llm_model": result.get("model", "unknown"),
                "provider": result.get("provider", "unknown")
            }
        else:
            return self._fallback_item_description(item, elapsed_time)

    def _fallback_item_description(self, item: MenuItem, elapsed_time: float) -> dict:
        """降级描述生成"""
        taste_mapping = {
            "咖啡": ["醇厚", "香浓", "咖啡因", "提神"],
            "茶饮": ["清新", "茶香", "舒缓"],
            "星冰乐": ["冰爽", "顺滑", "甜蜜"],
            "清爽系列": ["清爽", "果香", "气泡"],
            "食品": ["香脆", "美味", "搭配"]
        }

        keywords = (
            taste_mapping.get(item.category.value, []) +
            item.tags +
            [item.category.value]
        )

        return {
            "sku": item.sku,
            "name": item.name,
            "semantic_description": item.description,
            "keywords": keywords,
            "processing_time_ms": round(elapsed_time * 1000, 2),
            "llm_model": "fallback",
            "provider": "local"
        }

    def generate_user_profile(
        self,
        persona_type: str,
        custom_tags: list[str] = None,
        customization_preference: dict = None
    ) -> dict:
        """使用LLM生成用户画像（支持融入客制化偏好）"""
        start_time = time.time()

        base_persona = self.persona_templates.get(
            persona_type,
            self.persona_templates["实用主义"]
        )

        all_keywords = base_persona["base_keywords"].copy()
        if custom_tags:
            all_keywords.extend(custom_tags)

        # 从客制化偏好提取关键词
        customization_keywords = []
        if customization_preference:
            # 温度偏好
            temp_pref = customization_preference.get("temperature", {})
            if temp_pref:
                top_temp = max(temp_pref.items(), key=lambda x: x[1])[0] if temp_pref else None
                if top_temp:
                    temp_map = {"HOT": "热饮", "ICED": "冰饮", "WARM": "温饮"}
                    temp_display = temp_map.get(top_temp.upper(), top_temp)
                    ratio = temp_pref.get(top_temp, 0)
                    if ratio > 0.5:
                        customization_keywords.append(f"偏好{temp_display}")

            # 奶类偏好
            milk_pref = customization_preference.get("milk_type", {})
            if milk_pref:
                top_milk = max(milk_pref.items(), key=lambda x: x[1])[0] if milk_pref else None
                if top_milk:
                    ratio = milk_pref.get(top_milk, 0)
                    if ratio > 0.4:
                        milk_map = {
                            "OAT": "燕麦奶爱好者", "SOY": "豆奶爱好者",
                            "COCONUT": "椰奶爱好者", "SKIM": "低脂偏好"
                        }
                        milk_display = milk_map.get(top_milk.upper())
                        if milk_display:
                            customization_keywords.append(milk_display)

            # 糖度偏好
            sugar_pref = customization_preference.get("sugar_level", {})
            if sugar_pref:
                top_sugar = max(sugar_pref.items(), key=lambda x: x[1])[0] if sugar_pref else None
                if top_sugar:
                    ratio = sugar_pref.get(top_sugar, 0)
                    if ratio > 0.4:
                        sugar_map = {
                            "NONE": "无糖控糖", "LIGHT": "微糖偏好",
                            "HALF": "半糖偏好", "LESS": "少糖偏好"
                        }
                        sugar_display = sugar_map.get(top_sugar.upper())
                        if sugar_display:
                            customization_keywords.append(sugar_display)

        # 合并客制化关键词
        all_keywords.extend(customization_keywords)

        # 构建客制化偏好描述
        customization_hint = ""
        if customization_keywords:
            customization_hint = f"\n客制化习惯：{', '.join(customization_keywords)}"

        prompt = f"""分析用户画像，生成饮品偏好描述。

用户类型：{persona_type}
基础描述：{base_persona["description"]}
偏好关键词：{', '.join(all_keywords)}{customization_hint}

输出JSON：
{{
    "enhanced_description": "30字描述",
    "search_query": "用于搜索匹配饮品的查询语句，50字以内"
}}"""

        result = self.llm.generate_json(prompt, "你是用户研究专家")
        elapsed_time = time.time() - start_time

        content = result["content"]
        if isinstance(content, dict) and "search_query" in content:
            return {
                "persona_type": persona_type,
                "description": content.get("enhanced_description", base_persona["description"]),
                "keywords": all_keywords,
                "customization_keywords": customization_keywords,
                "search_query": content.get("search_query", " ".join(all_keywords)),
                "avoid_keywords": base_persona["avoid"],
                "processing_time_ms": round(elapsed_time * 1000, 2),
                "llm_model": result.get("model", "unknown"),
                "provider": result.get("provider", "unknown")
            }
        else:
            return {
                "persona_type": persona_type,
                "description": base_persona["description"],
                "keywords": all_keywords,
                "customization_keywords": customization_keywords,
                "search_query": " ".join(all_keywords),
                "avoid_keywords": base_persona["avoid"],
                "processing_time_ms": round(elapsed_time * 1000, 2),
                "llm_model": "fallback",
                "provider": "local"
            }

    def generate_recommendation_reason(
        self,
        item: MenuItem,
        user_profile: dict,
        match_score: float,
        use_llm: bool = True,
        suggested_customization: dict = None
    ) -> dict:
        """生成推荐理由（可含客制化建议）"""
        start_time = time.time()

        if not use_llm:
            return self._quick_recommendation_reason(item, user_profile, match_score, start_time, suggested_customization)

        # 构建客制化描述
        customization_hint = ""
        if suggested_customization and suggested_customization.get("suggested_customization"):
            custom = suggested_customization["suggested_customization"]
            custom_parts = []
            if custom.get("temperature"):
                temp_map = {"HOT": "热", "ICED": "冰", "WARM": "温"}
                temp = custom["temperature"]
                custom_parts.append(temp_map.get(temp.upper(), temp))
            if custom.get("milk_type"):
                milk_map = {"OAT": "燕麦奶", "WHOLE": "全脂奶", "SKIM": "脱脂奶", "SOY": "豆奶", "COCONUT": "椰奶"}
                milk = custom["milk_type"]
                if milk.upper() not in ["NONE", "WHOLE"]:
                    custom_parts.append(milk_map.get(milk.upper(), milk))
            if custom.get("sugar_level"):
                sugar_map = {"NONE": "无糖", "LIGHT": "微糖", "HALF": "半糖", "LESS": "少糖"}
                sugar = custom["sugar_level"]
                if sugar.upper() != "FULL":
                    custom_parts.append(sugar_map.get(sugar.upper(), sugar))
            if custom_parts:
                customization_hint = f"\n推荐配置：{'+'.join(custom_parts)}（基于用户习惯）"

        prompt = f"""为用户生成饮品推荐理由。

用户：{user_profile.get('persona_type')}，偏好{', '.join(user_profile.get('keywords', [])[:3])}
饮品：{item.name}，{item.description}
匹配度：{match_score:.0%}{customization_hint}

输出JSON：{{"reason": "15-20字推荐理由（可含客制化建议）", "highlight": "核心卖点"}}"""

        result = self.llm.generate_json(prompt, "你是星巴克店员，语气亲切")
        elapsed_time = time.time() - start_time

        content = result["content"]
        if isinstance(content, dict) and "reason" in content:
            return {
                "reason": content.get("reason", "为您精选推荐"),
                "highlight": content.get("highlight", ""),
                "confidence": "high" if match_score > 0.6 else "medium",
                "processing_time_ms": round(elapsed_time * 1000, 2),
                "llm_model": result.get("model", "unknown"),
                "provider": result.get("provider", "unknown")
            }
        else:
            return self._quick_recommendation_reason(item, user_profile, match_score, start_time, suggested_customization)

    def _quick_recommendation_reason(self, item, user_profile, match_score, start_time, suggested_customization=None):
        """快速生成推荐理由"""
        reasons = []
        item_keywords = set(item.tags)
        user_keywords = set(user_profile.get("keywords", []))
        matched = item_keywords & user_keywords

        if matched:
            reasons.append(f"符合您对「{list(matched)[0]}」的偏好")
        if item.is_new:
            reasons.append("新品推荐")
        if item.is_seasonal:
            reasons.append("季节限定")
        if item.calories < 100:
            reasons.append(f"仅{item.calories}卡")

        # 添加客制化建议到理由
        if suggested_customization and suggested_customization.get("reason"):
            custom_reason = suggested_customization["reason"]
            if custom_reason and custom_reason != "综合您的历史偏好推荐":
                reasons.append(custom_reason.split("；")[0])  # 取第一个客制化原因

        if not reasons:
            reasons.append("热门推荐")

        return {
            "reason": "；".join(reasons[:2]),
            "highlight": list(matched)[0] if matched else "",
            "confidence": "high" if match_score > 0.6 else "medium",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "llm_model": "rule-based",
            "provider": "local"
        }


class OpenAIEmbeddingVectorService:
    """使用OpenAI Embedding API的向量服务"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.llm_service = RealLLMService()
        self.item_embeddings: dict[str, np.ndarray] = {}
        self.item_texts: dict[str, dict] = {}
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """初始化商品向量（带缓存）"""
        print("🔄 初始化商品Embedding...")

        # 尝试从缓存加载
        if self._load_cache():
            print(f"✅ 从缓存加载了 {len(self.item_embeddings)} 个商品Embedding")
            return

        # 生成新的embedding
        print("📝 生成商品描述和Embedding（首次启动较慢）...")

        texts_to_embed = []
        skus = []

        for item in MENU_ITEMS:
            # 使用LLM生成描述
            desc = self.llm_service.generate_item_description(item)
            self.item_texts[item.sku] = desc

            # 构建客制化特征描述
            customization_features = []
            if item.customization_constraints:
                constraints = item.customization_constraints
                # 奶类选项
                if constraints.available_milk_types:
                    milk_names = {
                        "OAT": "燕麦奶", "SOY": "豆奶", "COCONUT": "椰奶",
                        "SKIM": "脱脂奶", "WHOLE": "全脂奶"
                    }
                    available_milks = [
                        milk_names.get(m.value if hasattr(m, 'value') else m.upper(), m)
                        for m in constraints.available_milk_types
                        if (m.value if hasattr(m, 'value') else m.upper()) != "NONE"
                    ]
                    if available_milks:
                        customization_features.append(f"可选{'/'.join(available_milks[:3])}")
                # 糖度选项
                if constraints.available_sugar_levels:
                    sugar_names = {"NONE": "无糖", "LIGHT": "微糖", "HALF": "半糖", "LESS": "少糖"}
                    low_sugar_options = [
                        sugar_names.get(s.value if hasattr(s, 'value') else s.upper())
                        for s in constraints.available_sugar_levels
                        if (s.value if hasattr(s, 'value') else s.upper()) in ["NONE", "LIGHT", "HALF", "LESS"]
                    ]
                    if low_sugar_options:
                        customization_features.append(f"支持{'/'  .join(low_sugar_options[:2])}")
                # 加浓缩
                if constraints.supports_espresso_adjustment:
                    customization_features.append("可加浓缩")
                # 奶油顶
                if constraints.supports_whipped_cream:
                    customization_features.append("可加奶油顶")

            customization_text = f"客制化：{', '.join(customization_features)}。" if customization_features else ""

            # 构建用于embedding的文本（增强版含客制化特征）
            embed_text = f"{item.name}。{desc['semantic_description']}。" \
                        f"分类：{item.category.value}。" \
                        f"标签：{', '.join(item.tags)}。" \
                        f"{'新品。' if item.is_new else ''}" \
                        f"{'季节限定。' if item.is_seasonal else ''}" \
                        f"{item.calories}卡路里。¥{item.base_price}。" \
                        f"{customization_text}"

            texts_to_embed.append(embed_text)
            skus.append(item.sku)
            print(f"   📦 {item.name}")

        # 批量获取embedding
        print("🔢 调用OpenAI Embedding API...")
        embeddings = self.embedding_service.get_embeddings(texts_to_embed)

        for sku, embedding in zip(skus, embeddings):
            self.item_embeddings[sku] = np.array(embedding)

        # 保存缓存
        self._save_cache()
        print(f"✅ 生成并缓存了 {len(self.item_embeddings)} 个商品Embedding")

    def _load_cache(self) -> bool:
        """从缓存加载embedding"""
        if not ITEM_EMBEDDINGS_CACHE.exists():
            return False

        try:
            with open(ITEM_EMBEDDINGS_CACHE, "r") as f:
                cache = json.load(f)

            # 验证缓存版本
            if cache.get("version") != "v3":
                return False

            for sku, data in cache.get("items", {}).items():
                self.item_embeddings[sku] = np.array(data["embedding"])
                self.item_texts[sku] = data["text_info"]

            return len(self.item_embeddings) == len(MENU_ITEMS)
        except Exception as e:
            print(f"⚠️ 缓存加载失败: {e}")
            return False

    def _save_cache(self):
        """保存embedding到缓存"""
        CACHE_DIR.mkdir(exist_ok=True)

        cache = {
            "version": "v3",
            "model": self.embedding_service.model,
            "items": {}
        }

        for sku, embedding in self.item_embeddings.items():
            cache["items"][sku] = {
                "embedding": embedding.tolist(),
                "text_info": self.item_texts.get(sku, {})
            }

        with open(ITEM_EMBEDDINGS_CACHE, "w") as f:
            json.dump(cache, f, ensure_ascii=False)

    def get_user_embedding(self, user_profile: dict) -> np.ndarray:
        """获取用户画像的embedding"""
        # 使用LLM生成的search_query作为embedding输入
        search_query = user_profile.get("search_query", "")
        if not search_query:
            search_query = " ".join(user_profile.get("keywords", []))

        embedding = self.embedding_service.get_embedding(search_query)
        return np.array(embedding)

    def calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))


class EmbeddingRecommendationEngine:
    """Embedding增强推荐引擎"""

    def __init__(self):
        self.llm_service = RealLLMService()
        self.vector_service = OpenAIEmbeddingVectorService()
        self.menu_items = {item.sku: item for item in MENU_ITEMS}

        # 延迟导入实验服务（避免循环依赖）
        self._experiment_services = None

    @property
    def experiment_services(self):
        """懒加载实验相关服务"""
        if self._experiment_services is None:
            from app.experiment_service import (
                ab_test_service, behavior_service, session_service, explainability_service
            )
            self._experiment_services = {
                "ab_test": ab_test_service,
                "behavior": behavior_service,
                "session": session_service,
                "explainability": explainability_service
            }
        return self._experiment_services

    def recommend(
        self,
        persona_type: str,
        custom_tags: list[str] = None,
        context: dict = None,
        top_k: int = 6,
        use_llm_for_reasons: bool = True
    ) -> dict:
        """执行推荐"""
        start_time = time.time()
        reasoning_steps = []
        llm_calls = []

        # Step 1: 生成用户画像
        step1_start = time.time()
        user_profile = self.llm_service.generate_user_profile(persona_type, custom_tags)

        llm_calls.append({
            "step": 1,
            "type": "user_profile",
            "model": user_profile.get("llm_model"),
            "provider": user_profile.get("provider"),
            "latency_ms": user_profile.get("processing_time_ms", 0)
        })

        reasoning_steps.append({
            "step": 1,
            "name": "用户画像生成",
            "description": f"分析用户「{persona_type}」生成搜索query",
            "input": {"persona_type": persona_type, "custom_tags": custom_tags},
            "output": {
                "search_query": user_profile.get("search_query", "")[:50],
                "keywords": user_profile.get("keywords", [])[:5]
            },
            "duration_ms": round((time.time() - step1_start) * 1000, 2),
            "model": user_profile.get("llm_model"),
            "provider": user_profile.get("provider")
        })

        # Step 2: 用户向量化 (OpenAI Embedding)
        step2_start = time.time()
        user_embedding = self.vector_service.get_user_embedding(user_profile)

        embedding_info = self.vector_service.embedding_service.get_info()
        reasoning_steps.append({
            "step": 2,
            "name": "用户向量化",
            "description": f"使用 {embedding_info['model']} 生成用户向量",
            "input": {"query": user_profile.get("search_query", "")[:30] + "..."},
            "output": {
                "vector_dim": len(user_embedding),
                "model": embedding_info["model"]
            },
            "duration_ms": round((time.time() - step2_start) * 1000, 2),
            "model": embedding_info["model"],
            "provider": "openai"
        })

        # Step 3: 向量召回
        step3_start = time.time()
        candidates = []
        for sku, item_embedding in self.vector_service.item_embeddings.items():
            similarity = self.vector_service.calculate_similarity(
                user_embedding, item_embedding
            )
            candidates.append({
                "sku": sku,
                "similarity": similarity
            })

        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        reasoning_steps.append({
            "step": 3,
            "name": "语义向量召回",
            "description": f"从{len(candidates)}个商品中计算语义相似度",
            "input": {"total_items": len(candidates)},
            "output": {
                "top_candidates": [
                    {"sku": c["sku"], "name": self.menu_items[c["sku"]].name,
                     "score": round(c["similarity"], 4)}
                    for c in candidates[:top_k]
                ]
            },
            "duration_ms": round((time.time() - step3_start) * 1000, 2),
            "model": "Cosine Similarity",
            "provider": "numpy"
        })

        # Step 4: 业务规则重排
        step4_start = time.time()
        reranked = []
        for candidate in candidates[:top_k * 2]:
            item = self.menu_items[candidate["sku"]]
            score = candidate["similarity"]

            # 业务加权
            if item.is_new:
                score *= 1.15
            if item.is_seasonal:
                score *= 1.1
            if any(tag in user_profile.get("avoid_keywords", []) for tag in item.tags):
                score *= 0.5

            # 上下文加权
            if context:
                if context.get("time_of_day") == "morning" and item.category == Category.COFFEE:
                    score *= 1.1
                if context.get("weather") == "hot" and Temperature.ICED in item.available_temperatures:
                    score *= 1.05

            reranked.append({
                "sku": candidate["sku"],
                "base_score": candidate["similarity"],
                "final_score": score
            })

        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        reasoning_steps.append({
            "step": 4,
            "name": "业务规则重排",
            "description": "应用新品、季节、偏好规则调整",
            "input": {"candidates_count": len(candidates[:top_k * 2])},
            "output": {
                "reranked_top": [
                    {"sku": r["sku"], "name": self.menu_items[r["sku"]].name,
                     "base": round(r["base_score"], 3), "final": round(r["final_score"], 3)}
                    for r in reranked[:top_k]
                ]
            },
            "duration_ms": round((time.time() - step4_start) * 1000, 2),
            "model": "Rule-based",
            "provider": "custom"
        })

        # Step 5: 生成推荐理由
        step5_start = time.time()
        recommendations = []
        reason_llm_calls = []

        for i, ranked in enumerate(reranked[:top_k]):
            item = self.menu_items[ranked["sku"]]

            use_llm = use_llm_for_reasons and i < 3
            reason_result = self.llm_service.generate_recommendation_reason(
                item, user_profile, ranked["final_score"], use_llm=use_llm
            )

            if use_llm and reason_result.get("provider") != "local":
                reason_llm_calls.append({
                    "item": item.name,
                    "model": reason_result.get("llm_model"),
                    "latency_ms": reason_result.get("processing_time_ms", 0)
                })

            item_desc = self.vector_service.item_texts.get(ranked["sku"], {})

            recommendations.append({
                "item": {
                    "sku": item.sku,
                    "name": item.name,
                    "english_name": item.english_name,
                    "category": item.category.value,
                    "base_price": item.base_price,
                    "description": item.description,
                    "calories": item.calories,
                    "tags": item.tags,
                    "is_new": item.is_new,
                    "is_seasonal": item.is_seasonal,
                    "available_temperatures": [t.value for t in item.available_temperatures],
                    "available_sizes": [s.value for s in item.available_sizes]
                },
                "match_score": round(ranked["final_score"], 4),
                "base_score": round(ranked["base_score"], 4),
                "reason": reason_result.get("reason", ""),
                "reason_highlight": reason_result.get("highlight", ""),
                "reason_confidence": reason_result.get("confidence", "medium"),
                "semantic_description": item_desc.get("semantic_description", ""),
                "llm_generated": reason_result.get("provider") != "local"
            })

        llm_calls.extend([{"step": 5, "type": "reason", **c} for c in reason_llm_calls])

        reasoning_steps.append({
            "step": 5,
            "name": "推荐理由生成",
            "description": f"Top-{min(3, top_k)}使用LLM",
            "input": {"items_count": len(recommendations)},
            "output": {"llm_reasons": len(reason_llm_calls)},
            "duration_ms": round((time.time() - step5_start) * 1000, 2),
            "model": "GPT-4o-mini",
            "provider": "openai"
        })

        total_time = time.time() - start_time

        return {
            "user_profile": {
                "persona_type": persona_type,
                "description": user_profile.get("description", ""),
                "keywords": user_profile.get("keywords", []),
                "search_query": user_profile.get("search_query", ""),
                "avoid_keywords": user_profile.get("avoid_keywords", []),
                "custom_tags": custom_tags or []
            },
            "context": context or {},
            "reasoning_steps": reasoning_steps,
            "recommendations": recommendations,
            "llm_info": {
                "provider": self.llm_service.provider_info.get("provider"),
                "model": self.llm_service.provider_info.get("model"),
                "embedding_model": self.vector_service.embedding_service.model,
                "calls": llm_calls,
                "total_llm_calls": len(llm_calls)
            },
            "metrics": {
                "total_time_ms": round(total_time * 1000, 2),
                "candidates_evaluated": len(candidates),
                "final_recommendations": len(recommendations),
                "avg_match_score": round(
                    sum(r["match_score"] for r in recommendations) / len(recommendations),
                    4
                ) if recommendations else 0
            }
        }

    def get_available_personas(self) -> list[dict]:
        """获取所有可用的用户画像类型"""
        return [
            {
                "type": persona_type,
                "description": data["description"],
                "keywords": data["base_keywords"]
            }
            for persona_type, data in self.llm_service.persona_templates.items()
        ]

    def recommend_v2(
        self,
        persona_type: str,
        user_id: str = None,
        session_id: str = None,
        custom_tags: list[str] = None,
        context: dict = None,
        top_k: int = 6,
        use_llm_for_reasons: bool = True,
        enable_ab_test: bool = True,
        enable_behavior: bool = True,
        enable_session: bool = True,
        enable_explainability: bool = True
    ) -> dict:
        """
        增强版推荐 - 集成A/B测试、用户行为、Session个性化和解释性增强

        新增参数:
        - user_id: 用户ID（用于历史行为和A/B分组）
        - session_id: 会话ID（用于实时个性化）
        - enable_ab_test: 是否启用A/B测试
        - enable_behavior: 是否启用历史行为加权
        - enable_session: 是否启用Session实时个性化
        - enable_explainability: 是否生成详细解释
        """
        start_time = time.time()
        reasoning_steps = []
        llm_calls = []

        # 生成默认ID
        user_id = user_id or f"user_{int(time.time())}"
        session_id = session_id or f"session_{int(time.time())}"

        # === A/B测试分组 ===
        experiment_info = {}
        if enable_ab_test:
            services = self.experiment_services
            rec_variant = services["ab_test"].get_variant("rec_algorithm", user_id)
            reason_variant = services["ab_test"].get_variant("reason_style", user_id)
            experiment_info = {
                "rec_algorithm": rec_variant,
                "reason_style": reason_variant
            }

        # Step 1: 生成用户画像（融入客制化偏好）
        step1_start = time.time()
        services = self.experiment_services

        # 获取用户客制化偏好（用于增强用户画像生成）
        customization_preference = None
        if enable_behavior:
            user_behavior_profile = services["behavior"].get_user_profile(user_id)
            customization_preference = user_behavior_profile.get("customization_preference", {})

        user_profile = self.llm_service.generate_user_profile(
            persona_type, custom_tags, customization_preference
        )

        llm_calls.append({
            "step": 1,
            "type": "user_profile",
            "model": user_profile.get("llm_model"),
            "provider": user_profile.get("provider"),
            "latency_ms": user_profile.get("processing_time_ms", 0)
        })

        reasoning_steps.append({
            "step": 1,
            "name": "用户画像生成",
            "description": f"分析用户「{persona_type}」生成搜索query（含客制化偏好）",
            "input": {
                "persona_type": persona_type,
                "custom_tags": custom_tags,
                "has_customization_pref": bool(customization_preference)
            },
            "output": {
                "search_query": user_profile.get("search_query", "")[:50],
                "keywords": user_profile.get("keywords", [])[:5],
                "customization_keywords": user_profile.get("customization_keywords", [])
            },
            "duration_ms": round((time.time() - step1_start) * 1000, 2),
            "model": user_profile.get("llm_model"),
            "provider": user_profile.get("provider")
        })

        # Step 2: 用户向量化
        step2_start = time.time()
        user_embedding = self.vector_service.get_user_embedding(user_profile)
        embedding_info = self.vector_service.embedding_service.get_info()

        reasoning_steps.append({
            "step": 2,
            "name": "用户向量化",
            "description": f"使用 {embedding_info['model']} 生成用户向量",
            "input": {"query": user_profile.get("search_query", "")[:30] + "..."},
            "output": {"vector_dim": len(user_embedding), "model": embedding_info["model"]},
            "duration_ms": round((time.time() - step2_start) * 1000, 2),
            "model": embedding_info["model"],
            "provider": "openai"
        })

        # Step 3: 向量召回
        step3_start = time.time()
        candidates = []
        for sku, item_embedding in self.vector_service.item_embeddings.items():
            similarity = self.vector_service.calculate_similarity(user_embedding, item_embedding)
            candidates.append({"sku": sku, "similarity": similarity})

        candidates.sort(key=lambda x: x["similarity"], reverse=True)

        reasoning_steps.append({
            "step": 3,
            "name": "语义向量召回",
            "description": f"从{len(candidates)}个商品中计算语义相似度",
            "input": {"total_items": len(candidates)},
            "output": {
                "top_candidates": [
                    {"sku": c["sku"], "name": self.menu_items[c["sku"]].name, "score": round(c["similarity"], 4)}
                    for c in candidates[:top_k]
                ]
            },
            "duration_ms": round((time.time() - step3_start) * 1000, 2),
            "model": "Cosine Similarity",
            "provider": "numpy"
        })

        # Step 4: 多因素加权重排
        step4_start = time.time()
        services = self.experiment_services
        reranked = []

        for candidate in candidates[:top_k * 2]:
            item = self.menu_items[candidate["sku"]]
            base_score = candidate["similarity"]

            # 业务规则加权
            rule_multiplier = 1.0
            if item.is_new:
                rule_multiplier *= 1.15
            if item.is_seasonal:
                rule_multiplier *= 1.1
            if any(tag in user_profile.get("avoid_keywords", []) for tag in item.tags):
                rule_multiplier *= 0.5

            # === 扩展的上下文加权 ===
            if context:
                time_of_day = context.get("time_of_day")
                season = context.get("season")
                day_type = context.get("day_type")

                # 时间段规则
                if time_of_day == "morning":
                    if item.category == Category.COFFEE:
                        rule_multiplier *= 1.15  # 早晨咖啡加权
                    if item.category == Category.FOOD and "早餐" in item.tags:
                        rule_multiplier *= 1.2  # 早餐食品加权
                elif time_of_day == "lunch":
                    if item.category == Category.FOOD:
                        rule_multiplier *= 1.1
                elif time_of_day == "afternoon":
                    if item.category == Category.TEA:
                        rule_multiplier *= 1.1  # 下午茶加权
                    if item.category == Category.FRAPPUCCINO:
                        rule_multiplier *= 1.1
                elif time_of_day == "evening":
                    if "无咖啡因" in item.tags:
                        rule_multiplier *= 1.15  # 晚间无咖啡因加权
                    if item.category == Category.COFFEE:
                        rule_multiplier *= 0.9  # 晚间咖啡降权
                elif time_of_day == "night":
                    if item.category == Category.COFFEE:
                        rule_multiplier *= 0.8  # 夜间咖啡降权

                # 季节规则
                if season == "summer":
                    if Temperature.ICED in item.available_temperatures:
                        rule_multiplier *= 1.1
                    if "清爽" in item.tags or "冰爽" in item.tags:
                        rule_multiplier *= 1.1
                elif season == "winter":
                    if Temperature.HOT in item.available_temperatures:
                        rule_multiplier *= 1.1
                    if "温暖" in item.tags:
                        rule_multiplier *= 1.1

                # 周末规则
                if day_type == "weekend":
                    if item.is_new or item.is_seasonal:
                        rule_multiplier *= 1.1  # 周末更愿意尝新

            # === A/B测试真正算法分支 ===
            rec_variant = experiment_info.get("rec_algorithm", {}).get("variant", "hybrid")

            # 历史行为加权（使用增强版订单权重）
            behavior_multiplier = 1.0
            order_boost_detail = None
            if enable_behavior and rec_variant in ["embedding_plus", "hybrid"]:
                # 使用新的订单权重API获取详细分解
                order_boost_detail = services["behavior"].get_order_based_recommendation_boost(
                    user_id, item.sku, item.category.value, item.tags, item.base_price
                )
                behavior_multiplier = order_boost_detail["total_boost"]

            # Session实时个性化加权（仅 hybrid 变体启用）
            session_multiplier = 1.0
            if enable_session and rec_variant == "hybrid":
                session_multiplier = services["session"].get_session_boost(
                    session_id, item.tags, item.category.value, item.base_price
                )

            # 客制化偏好加权（仅 hybrid 变体启用）
            customization_multiplier = 1.0
            customization_boost_detail = None
            if enable_behavior and rec_variant == "hybrid":
                # 获取商品客制化约束
                item_constraints = None
                if item.customization_constraints:
                    item_constraints = item.customization_constraints.model_dump()

                customization_boost_detail = services["behavior"].get_customization_based_boost(
                    user_id,
                    item_constraints,
                    [t.value for t in item.available_temperatures],
                    [s.value for s in item.available_sizes]
                )
                customization_multiplier = customization_boost_detail["total_boost"]

            # === 冷启动策略 ===
            cold_start_boost = 1.0
            is_cold_start = False
            if enable_behavior:
                user_behavior_profile = services["behavior"].get_user_profile(user_id)
                if user_behavior_profile.get("is_new_user", True):
                    is_cold_start = True
                    # 1. 新品/季节限定额外加权
                    if item.is_new:
                        cold_start_boost *= 1.2
                    if item.is_seasonal:
                        cold_start_boost *= 1.15
                    # 2. 人气商品加权（基于标签）
                    if "人气" in item.tags:
                        cold_start_boost *= 1.15
                    if "经典" in item.tags:
                        cold_start_boost *= 1.1

            # 综合得分
            final_score = base_score * rule_multiplier * behavior_multiplier * session_multiplier * customization_multiplier * cold_start_boost

            # 计算匹配的关键词
            user_keywords = set(user_profile.get("keywords", []))
            item_keywords = set(item.tags)
            matched_keywords = list(user_keywords & item_keywords)

            reranked.append({
                "sku": candidate["sku"],
                "base_score": base_score,
                "rule_multiplier": rule_multiplier,
                "behavior_multiplier": behavior_multiplier,
                "session_multiplier": session_multiplier,
                "customization_multiplier": customization_multiplier,
                "cold_start_boost": cold_start_boost,
                "is_cold_start": is_cold_start,
                "final_score": final_score,
                "matched_keywords": matched_keywords,
                "order_boost_detail": order_boost_detail,
                "customization_boost_detail": customization_boost_detail,
                "algorithm_variant": rec_variant
            })

        reranked.sort(key=lambda x: x["final_score"], reverse=True)

        reasoning_steps.append({
            "step": 4,
            "name": "多因素加权重排",
            "description": "综合业务规则、历史行为、实时偏好、客制化匹配",
            "input": {
                "enable_behavior": enable_behavior,
                "enable_session": enable_session
            },
            "output": {
                "reranked_top": [
                    {
                        "sku": r["sku"],
                        "name": self.menu_items[r["sku"]].name,
                        "base": round(r["base_score"], 3),
                        "behavior": round(r["behavior_multiplier"], 2),
                        "session": round(r["session_multiplier"], 2),
                        "customization": round(r["customization_multiplier"], 2),
                        "final": round(r["final_score"], 3)
                    }
                    for r in reranked[:top_k]
                ]
            },
            "duration_ms": round((time.time() - step4_start) * 1000, 2),
            "model": "Multi-factor Reranking",
            "provider": "custom"
        })

        # Step 5: 生成推荐理由和解释
        step5_start = time.time()
        recommendations = []
        reason_llm_calls = []

        # 根据A/B测试决定推荐理由风格
        reason_style = "concise"
        if experiment_info.get("reason_style", {}).get("variant") == "detailed":
            reason_style = "detailed"

        for i, ranked in enumerate(reranked[:top_k]):
            item = self.menu_items[ranked["sku"]]
            item_desc = self.vector_service.item_texts.get(ranked["sku"], {})

            # 生成推荐客制化组合（需先于推荐理由生成，以便融入理由）
            suggested_customization = None
            if enable_behavior:
                item_constraints = None
                if item.customization_constraints:
                    item_constraints = item.customization_constraints.model_dump()

                suggested_customization = services["behavior"].get_suggested_customization_for_item(
                    user_id,
                    item.sku,
                    item_constraints,
                    [t.value for t in item.available_temperatures],
                    [s.value for s in item.available_sizes],
                    item.base_price
                )

            # 生成推荐理由（融入客制化建议）
            use_llm = use_llm_for_reasons and i < 3
            reason_result = self.llm_service.generate_recommendation_reason(
                item, user_profile, ranked["final_score"],
                use_llm=use_llm,
                suggested_customization=suggested_customization
            )

            if use_llm and reason_result.get("provider") != "local":
                reason_llm_calls.append({
                    "item": item.name,
                    "model": reason_result.get("llm_model"),
                    "latency_ms": reason_result.get("processing_time_ms", 0)
                })

            # 生成详细解释
            explanation = None
            if enable_explainability:
                explanation = services["explainability"].generate_detailed_explanation(
                    item={
                        "sku": item.sku,
                        "name": item.name,
                        "is_new": item.is_new,
                        "is_seasonal": item.is_seasonal,
                        "tags": item.tags
                    },
                    user_profile=user_profile,
                    match_score=ranked["final_score"],
                    session_boost=ranked["session_multiplier"],
                    behavior_boost=ranked["behavior_multiplier"],
                    embedding_similarity=ranked["base_score"],
                    matched_keywords=ranked["matched_keywords"],
                    experiment_info=experiment_info
                )

            recommendations.append({
                "item": {
                    "sku": item.sku,
                    "name": item.name,
                    "english_name": item.english_name,
                    "category": item.category.value,
                    "base_price": item.base_price,
                    "description": item.description,
                    "calories": item.calories,
                    "tags": item.tags,
                    "is_new": item.is_new,
                    "is_seasonal": item.is_seasonal,
                    "available_temperatures": [t.value for t in item.available_temperatures],
                    "available_sizes": [s.value for s in item.available_sizes]
                },
                "match_score": round(ranked["final_score"], 4),
                "base_score": round(ranked["base_score"], 4),
                "score_breakdown": {
                    "embedding_similarity": round(ranked["base_score"], 4),
                    "rule_multiplier": round(ranked["rule_multiplier"], 2),
                    "behavior_multiplier": round(ranked["behavior_multiplier"], 2),
                    "session_multiplier": round(ranked["session_multiplier"], 2),
                    "customization_multiplier": round(ranked["customization_multiplier"], 2),
                    "cold_start_boost": round(ranked.get("cold_start_boost", 1.0), 2),
                    "is_cold_start": ranked.get("is_cold_start", False),
                    "algorithm_variant": ranked.get("algorithm_variant", "hybrid"),
                    "order_boost_detail": ranked.get("order_boost_detail"),
                    "customization_boost_detail": ranked.get("customization_boost_detail")
                },
                "matched_keywords": ranked["matched_keywords"],
                "reason": reason_result.get("reason", ""),
                "reason_highlight": reason_result.get("highlight", ""),
                "reason_confidence": reason_result.get("confidence", "medium"),
                "semantic_description": item_desc.get("semantic_description", ""),
                "llm_generated": reason_result.get("provider") != "local",
                "explanation": explanation,
                "suggested_customization": suggested_customization
            })

        llm_calls.extend([{"step": 5, "type": "reason", **c} for c in reason_llm_calls])

        reasoning_steps.append({
            "step": 5,
            "name": "推荐理由与客制化建议生成",
            "description": f"Top-{min(3, top_k)}使用LLM，风格:{reason_style}，含客制化建议",
            "input": {"items_count": len(recommendations), "style": reason_style},
            "output": {
                "llm_reasons": len(reason_llm_calls),
                "with_explanation": enable_explainability,
                "with_suggested_customization": enable_behavior
            },
            "duration_ms": round((time.time() - step5_start) * 1000, 2),
            "model": "GPT-4o-mini",
            "provider": "openai"
        })

        total_time = time.time() - start_time

        return {
            "user_id": user_id,
            "session_id": session_id,
            "user_profile": {
                "persona_type": persona_type,
                "description": user_profile.get("description", ""),
                "keywords": user_profile.get("keywords", []),
                "search_query": user_profile.get("search_query", ""),
                "avoid_keywords": user_profile.get("avoid_keywords", []),
                "custom_tags": custom_tags or []
            },
            "context": context or {},
            "experiment": experiment_info,
            "reasoning_steps": reasoning_steps,
            "recommendations": recommendations,
            "llm_info": {
                "provider": self.llm_service.provider_info.get("provider"),
                "model": self.llm_service.provider_info.get("model"),
                "embedding_model": self.vector_service.embedding_service.model,
                "calls": llm_calls,
                "total_llm_calls": len(llm_calls)
            },
            "personalization": {
                "behavior_enabled": enable_behavior,
                "session_enabled": enable_session,
                "ab_test_enabled": enable_ab_test
            },
            "metrics": {
                "total_time_ms": round(total_time * 1000, 2),
                "candidates_evaluated": len(candidates),
                "final_recommendations": len(recommendations),
                "avg_match_score": round(
                    sum(r["match_score"] for r in recommendations) / len(recommendations), 4
                ) if recommendations else 0
            }
        }

    def recommend_with_custom_preference(
        self,
        custom_preference: str,
        user_id: str = None,
        session_id: str = None,
        context: dict = None,
        top_k: int = 6,
        enable_ab_test: bool = True,
        enable_behavior: bool = True,
        enable_session: bool = True
    ) -> dict:
        """
        自定义偏好推荐 - 支持用户自由文本输入

        Args:
            custom_preference: 用户自由文本描述，如"低卡、提神、清爽的饮品"
        """
        start_time = time.time()

        # 生成默认ID
        user_id = user_id or f"user_{int(time.time())}"
        session_id = session_id or f"session_{int(time.time())}"

        # Step 1: 使用LLM解析用户自由文本偏好
        parse_prompt = f"""分析用户的饮品偏好描述，提取关键需求。

用户描述：{custom_preference}

输出JSON：
{{
    "search_query": "用于搜索匹配饮品的查询语句，50字以内",
    "keywords": ["关键词1", "关键词2", ...],
    "avoid_keywords": ["排斥关键词"],
    "temperature_hint": "HOT/ICED/null",
    "calorie_preference": "low/medium/high/null",
    "inferred_persona": "最接近的用户类型: 健康达人/咖啡重度用户/甜品爱好者/尝鲜派/实用主义/养生白领"
}}"""

        parse_result = self.llm_service.llm.generate_json(parse_prompt, "你是用户研究专家")
        parsed = parse_result.get("content", {})

        if not isinstance(parsed, dict):
            parsed = {
                "search_query": custom_preference,
                "keywords": custom_preference.split("、"),
                "avoid_keywords": [],
                "temperature_hint": None,
                "calorie_preference": None,
                "inferred_persona": "实用主义"
            }

        # 构建用户画像
        user_profile = {
            "persona_type": "自定义偏好",
            "description": custom_preference,
            "keywords": parsed.get("keywords", []),
            "search_query": parsed.get("search_query", custom_preference),
            "avoid_keywords": parsed.get("avoid_keywords", []),
            "customization_keywords": [],
            "inferred_persona": parsed.get("inferred_persona", "实用主义"),
            "temperature_hint": parsed.get("temperature_hint"),
            "calorie_preference": parsed.get("calorie_preference"),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "llm_model": parse_result.get("model", "unknown"),
            "provider": parse_result.get("provider", "unknown")
        }

        # Step 2: 用户向量化
        user_embedding = self.vector_service.get_user_embedding(user_profile)

        # Step 3: 向量召回
        candidates = []
        for sku, item_embedding in self.vector_service.item_embeddings.items():
            similarity = self.vector_service.calculate_similarity(user_embedding, item_embedding)
            candidates.append({"sku": sku, "similarity": similarity})

        candidates.sort(key=lambda x: x["similarity"], reverse=True)

        # Step 4: 应用额外过滤（基于解析结果）
        services = self.experiment_services
        reranked = []

        for candidate in candidates[:top_k * 2]:
            item = self.menu_items[candidate["sku"]]
            base_score = candidate["similarity"]
            rule_multiplier = 1.0

            # 温度偏好过滤
            temp_hint = parsed.get("temperature_hint")
            if temp_hint == "ICED" and Temperature.ICED not in item.available_temperatures:
                rule_multiplier *= 0.5
            elif temp_hint == "HOT" and Temperature.HOT not in item.available_temperatures:
                rule_multiplier *= 0.5

            # 卡路里偏好
            calorie_pref = parsed.get("calorie_preference")
            if calorie_pref == "low" and item.calories > 200:
                rule_multiplier *= 0.7
            elif calorie_pref == "high" and item.calories < 100:
                rule_multiplier *= 0.8

            # 排斥关键词
            if any(tag in parsed.get("avoid_keywords", []) for tag in item.tags):
                rule_multiplier *= 0.3

            # 上下文加权
            if context:
                time_of_day = context.get("time_of_day")
                season = context.get("season")

                if time_of_day == "morning" and item.category == Category.COFFEE:
                    rule_multiplier *= 1.1
                if season == "summer" and Temperature.ICED in item.available_temperatures:
                    rule_multiplier *= 1.05

            # 历史行为加权
            behavior_multiplier = 1.0
            if enable_behavior:
                order_boost = services["behavior"].get_order_based_recommendation_boost(
                    user_id, item.sku, item.category.value, item.tags, item.base_price
                )
                behavior_multiplier = order_boost["total_boost"]

            # Session加权
            session_multiplier = 1.0
            if enable_session:
                session_multiplier = services["session"].get_session_boost(
                    session_id, item.tags, item.category.value, item.base_price
                )

            final_score = base_score * rule_multiplier * behavior_multiplier * session_multiplier

            # 关键词匹配
            user_keywords = set(parsed.get("keywords", []))
            item_keywords = set(item.tags)
            matched_keywords = list(user_keywords & item_keywords)

            reranked.append({
                "sku": candidate["sku"],
                "base_score": base_score,
                "rule_multiplier": rule_multiplier,
                "behavior_multiplier": behavior_multiplier,
                "session_multiplier": session_multiplier,
                "final_score": final_score,
                "matched_keywords": matched_keywords
            })

        reranked.sort(key=lambda x: x["final_score"], reverse=True)

        # Step 5: 构建推荐结果
        recommendations = []
        for ranked in reranked[:top_k]:
            item = self.menu_items[ranked["sku"]]
            item_desc = self.vector_service.item_texts.get(ranked["sku"], {})

            # 生成推荐理由
            reason_result = self.llm_service.generate_recommendation_reason(
                item, user_profile, ranked["final_score"], use_llm=(len(recommendations) < 3)
            )

            recommendations.append({
                "item": {
                    "sku": item.sku,
                    "name": item.name,
                    "english_name": item.english_name,
                    "category": item.category.value,
                    "base_price": item.base_price,
                    "description": item.description,
                    "calories": item.calories,
                    "tags": item.tags,
                    "is_new": item.is_new,
                    "is_seasonal": item.is_seasonal,
                    "available_temperatures": [t.value for t in item.available_temperatures],
                    "available_sizes": [s.value for s in item.available_sizes]
                },
                "match_score": round(ranked["final_score"], 4),
                "base_score": round(ranked["base_score"], 4),
                "score_breakdown": {
                    "embedding_similarity": round(ranked["base_score"], 4),
                    "rule_multiplier": round(ranked["rule_multiplier"], 2),
                    "behavior_multiplier": round(ranked["behavior_multiplier"], 2),
                    "session_multiplier": round(ranked["session_multiplier"], 2)
                },
                "matched_keywords": ranked["matched_keywords"],
                "reason": reason_result.get("reason", ""),
                "reason_highlight": reason_result.get("highlight", ""),
                "semantic_description": item_desc.get("semantic_description", "")
            })

        total_time = time.time() - start_time

        return {
            "user_id": user_id,
            "session_id": session_id,
            "custom_preference": custom_preference,
            "parsed_preference": {
                "search_query": parsed.get("search_query", ""),
                "keywords": parsed.get("keywords", []),
                "avoid_keywords": parsed.get("avoid_keywords", []),
                "temperature_hint": parsed.get("temperature_hint"),
                "calorie_preference": parsed.get("calorie_preference"),
                "inferred_persona": parsed.get("inferred_persona")
            },
            "user_profile": user_profile,
            "recommendations": recommendations,
            "llm_info": {
                "provider": self.llm_service.provider_info.get("provider"),
                "model": self.llm_service.provider_info.get("model")
            },
            "metrics": {
                "total_time_ms": round(total_time * 1000, 2),
                "candidates_evaluated": len(candidates),
                "final_recommendations": len(recommendations)
            }
        }


# 单例
embedding_recommendation_engine = EmbeddingRecommendationEngine()
