# 星巴克风格智能推荐系统技术方案

## 1. 项目概述

### 1.1 业务背景

在新零售场景中，"猜你喜欢"类个性化推荐功能已成为提升用户体验和转化率的关键能力。本项目以星巴克菜单为原型，构建一套基于大模型的智能推荐系统，验证LLM在推荐场景中的应用价值。

### 1.2 核心目标

- 实现基于用户画像和实时意图的个性化饮品推荐
- 支持SKU级别的客制化选项（杯型、温度、糖度、奶制品）
- 提供可视化的推荐过程展示，增强用户信任感
- 验证大模型在推荐系统中的实际效果

### 1.3 技术选型

| 组件 | 技术方案 | 说明 |
|------|----------|------|
| 后端框架 | FastAPI | 高性能异步Web框架 |
| 包管理 | uv | 现代Python包管理工具 |
| LLM服务 | OpenAI GPT-4o-mini | 用户画像生成、推荐理由生成 |
| 向量服务 | OpenAI text-embedding-3-small | 语义相似度计算 |
| 前端 | Jinja2 + Vanilla JS | 轻量级模板渲染 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   index.html    │  │ embedding_demo  │  │   Static CSS/JS │ │
│  │   (基础菜单)     │  │  (推荐演示)      │  │                 │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────────┘ │
└───────────┼─────────────────────┼───────────────────────────────┘
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  /api/menu/*    │  │ /api/embedding/ │  │ /api/customize  │ │
│  │   菜单接口       │  │   推荐接口       │  │   客制化接口     │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────────┘ │
└───────────┼─────────────────────┼───────────────────────────────┘
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   LLMService    │  │ EmbeddingService│  │  VectorService  │ │
│  │  (文本生成)      │  │  (向量生成)      │  │  (相似度计算)   │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                           │
│  ┌─────────────────────────────┐  ┌─────────────────────────┐   │
│  │      OpenAI API             │  │     Anthropic API       │   │
│  │  - GPT-4o-mini (LLM)        │  │  - Claude (备选)         │   │
│  │  - text-embedding-3-small   │  │                         │   │
│  └─────────────────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块说明

#### 2.2.1 LLM服务层 (`llm_service.py`)

采用Provider抽象模式，支持多LLM厂商无缝切换：

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None) -> dict

    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: str = None) -> dict

# 具体实现
├── OpenAIProvider      # GPT-4o-mini
├── AnthropicProvider   # Claude
└── FallbackProvider    # 降级模拟器
```

#### 2.2.2 Embedding服务层 (`embedding_service.py`)

```python
class OpenAIEmbeddingVectorService:
    """基于OpenAI Embedding的向量服务"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.item_embeddings: dict[str, np.ndarray] = {}  # 商品向量缓存

    def get_user_embedding(self, user_profile: dict) -> np.ndarray:
        """将用户查询转换为向量"""

    def calculate_similarity(self, user_embedding, item_embedding) -> float:
        """计算余弦相似度"""
```

---

## 3. 推荐算法设计

### 3.1 推荐流程

```
用户输入 (搜索词 + 用户画像类型)
           │
           ▼
    ┌──────────────┐
    │ Step 1: 构建 │
    │  用户画像     │ ──→ GPT-4o-mini 生成增强画像
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Step 2: 向量 │
    │  化用户意图   │ ──→ text-embedding-3-small
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Step 3: 计算 │
    │  语义相似度   │ ──→ Cosine Similarity
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Step 4: 排序 │
    │  Top-K筛选   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Step 5: 生成 │
    │  推荐理由     │ ──→ GPT-4o-mini 个性化文案
    └──────┬───────┘
           │
           ▼
      返回推荐结果
```

### 3.2 相似度计算

使用余弦相似度衡量用户意图与商品的匹配程度：

```python
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    计算两个向量的余弦相似度

    公式: cos(θ) = (A · B) / (||A|| × ||B||)

    返回值范围: [-1, 1]，映射到 [0, 1] 作为匹配分数
    """
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = dot_product / (norm_a * norm_b)
    return (similarity + 1) / 2  # 映射到 [0, 1]
```

### 3.3 方案对比

| 维度 | TF-IDF方案 | OpenAI Embedding方案 |
|------|-----------|---------------------|
| 语义理解 | 关键词匹配，无语义 | 深层语义理解 |
| 匹配精度 | 0%（词汇不匹配） | 60%~80% |
| 向量维度 | 动态（词汇表大小） | 固定1536维 |
| API调用 | 无 | 需要调用OpenAI |
| 响应延迟 | <10ms | ~200ms（首次） |
| 成本 | 免费 | $0.00002/1K tokens |

---

## 4. 数据模型

### 4.1 商品模型

```python
class MenuItem(BaseModel):
    id: str                    # 商品唯一ID
    name: str                  # 商品名称
    category: str              # 分类（咖啡/茶饮/星冰乐等）
    description: str           # 商品描述
    price: float               # 基础价格
    image_url: str             # 商品图片
    tags: list[str]            # 标签（提神/低糖/热销等）
    nutrition: dict            # 营养信息
    customizable: bool         # 是否支持客制化
```

### 4.2 客制化选项

```python
class Customization(BaseModel):
    cup_size: CupSize          # 中杯/大杯/超大杯
    temperature: Temperature   # 热/冰/常温
    sugar_level: SugarLevel    # 标准/少糖/无糖
    milk_type: MilkType        # 全脂/脱脂/燕麦/杏仁
```

### 4.3 用户画像模板

```python
PERSONA_TEMPLATES = {
    "健康达人": {
        "preferences": ["低糖", "低卡", "植物奶"],
        "avoid": ["高糖", "奶油"],
        "lifestyle": "注重健康，偏好清淡口味"
    },
    "咖啡重度用户": {
        "preferences": ["浓郁", "提神", "经典"],
        "avoid": ["太甜"],
        "lifestyle": "追求咖啡品质，喜欢纯粹咖啡风味"
    },
    # ... 更多画像
}
```

---

## 5. API接口设计

### 5.1 推荐接口

**POST** `/api/embedding/recommend`

请求体：
```json
{
    "user_id": "user_001",
    "search_query": "想喝一杯提神醒脑的咖啡，不太甜",
    "persona_type": "咖啡重度用户",
    "context": {
        "time_of_day": "morning",
        "weather": "sunny"
    }
}
```

响应体：
```json
{
    "user_profile": {
        "taste_preference": "偏好浓郁咖啡风味",
        "health_consciousness": "中等关注",
        "intent_keywords": ["提神", "咖啡", "不甜"]
    },
    "recommendations": [
        {
            "item": { "id": "coffee_005", "name": "冷萃咖啡", ... },
            "match_score": 0.75,
            "reason": "冷萃咖啡，浓郁顺滑，提神佳选！",
            "semantic_description": "..."
        }
    ],
    "reasoning_steps": [...],
    "llm_info": {
        "provider": "OpenAIProvider",
        "model": "gpt-4o-mini",
        "embedding_model": "text-embedding-3-small"
    }
}
```

### 5.2 其他接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/menu` | GET | 获取完整菜单 |
| `/api/menu/categories` | GET | 获取分类列表 |
| `/api/menu/{item_id}` | GET | 获取单品详情 |
| `/api/customize/options` | GET | 获取客制化选项 |
| `/api/embedding/personas` | GET | 获取用户画像列表 |

---

## 6. 性能优化

### 6.1 Embedding缓存策略

商品Embedding在服务启动时预计算并持久化缓存：

```python
CACHE_FILE = "app/cache/item_embeddings.json"

def _initialize_embeddings(self):
    """初始化商品Embedding"""
    # 1. 尝试从缓存加载
    if os.path.exists(CACHE_FILE):
        cached = json.load(open(CACHE_FILE))
        if self._validate_cache(cached):
            self.item_embeddings = cached
            return

    # 2. 批量生成Embedding（减少API调用）
    texts = [self._build_item_text(item) for item in menu_items]
    embeddings = self.embedding_service.get_embeddings(texts)

    # 3. 缓存到文件
    self._save_cache(embeddings)
```

### 6.2 性能指标

| 场景 | 首次请求 | 缓存命中 |
|------|----------|----------|
| 商品Embedding生成 | ~3s (18个商品) | 0ms |
| 用户意图Embedding | ~200ms | - |
| 相似度计算 | <1ms | <1ms |
| 推荐理由生成 | ~1.5s/个 | - |
| 端到端延迟 | ~8s | ~5s |

---

## 7. 部署与配置

### 7.1 环境变量

```bash
# .env
LLM_PROVIDER=openai          # openai | anthropic
OPENAI_API_KEY=sk-xxx        # OpenAI API密钥
ANTHROPIC_API_KEY=sk-xxx     # Anthropic API密钥（可选）
```

### 7.2 快速启动

```bash
# 安装依赖
uv sync

# 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000

# 访问
# 基础菜单: http://localhost:8000/
# 推荐演示: http://localhost:8000/embedding-demo
```

### 7.3 依赖清单

```toml
[project]
dependencies = [
    "fastapi>=0.115.6",
    "uvicorn[standard]>=0.34.0",
    "jinja2>=3.1.5",
    "python-dotenv>=1.0.1",
    "openai>=1.78.1",
    "anthropic>=0.52.0",
    "numpy>=2.2.2",
    "httpx[socks]>=0.28.1",
]
```

---

## 8. 扩展方向

### 8.1 短期优化

- [ ] 增加推荐结果的A/B测试框架
- [ ] 实现用户反馈收集与模型微调
- [ ] 添加推荐结果的解释性增强

### 8.2 中期演进

- [ ] 引入用户历史行为数据
- [ ] 实现实时个性化（基于session）
- [ ] 多模态推荐（图片理解）

### 8.3 长期规划

- [ ] 构建私有化部署的推荐模型
- [ ] 实现端到端的推荐效果评估体系
- [ ] 探索Agent化的交互式推荐

---

## 9. 附录

### 9.1 项目结构

```
rec_demo/
├── app/
│   ├── main.py              # FastAPI入口
│   ├── models.py            # 数据模型
│   ├── data.py              # 菜单数据
│   ├── llm_service.py       # LLM服务层
│   ├── embedding_service.py # Embedding推荐引擎
│   ├── cache/               # Embedding缓存
│   ├── templates/           # Jinja2模板
│   └── static/              # 静态资源
├── docs/
│   └── technical_solution.md
├── pyproject.toml
└── .env
```

### 9.2 测试结果示例

**输入**: "想喝一杯提神醒脑的咖啡，不太甜" + 咖啡重度用户

**输出**:

| 排名 | 商品 | 匹配度 | 推荐理由 |
|------|------|--------|----------|
| 1 | 冷萃咖啡 | 75.0% | 冷萃咖啡，浓郁顺滑，提神佳选！ |
| 2 | 燕麦拿铁 | 63.4% | 燕麦奶与浓郁咖啡完美结合，清新提神！ |
| 3 | 馥芮白 | 61.8% | 浓郁口感，提神效果持久 |

---

*文档版本: v1.0*
*最后更新: 2025-12-29*
