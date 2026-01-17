# AI 点单推荐系统 MCP 接口文档

## 概述

本文档描述了星巴克 AI 点单场景下的 MCP (Model Context Protocol) 接口规范。该接口基于现有推荐系统 V3，专门针对 AI 对话点单场景优化，支持自然语言理解、硬约束过滤、置信度评估等能力。

### 核心能力

| 能力 | 描述 |
|------|------|
| 自然语言理解 | 将用户口语化表达转换为推荐意图 |
| 硬约束过滤 | 支持无咖啡因、低卡、价格限制等硬性条件 |
| 置信度评估 | 输出推荐置信度，辅助 AI 决策是否追问 |
| 上下文感知 | 集成时段、天气、门店等上下文因子 |
| 话术生成 | 提供建议的 AI 回复话术 |

---

## MCP 服务器配置

### 服务器信息

```json
{
  "name": "starbucks-ai-ordering",
  "version": "1.0.0",
  "description": "星巴克AI点单推荐MCP服务"
}
```

### 启动方式

```bash
# 独立启动 MCP 服务器
uv run python -m app.mcp_server

# 或作为 FastAPI 应用的一部分
uv run uvicorn app.main:app --reload --port 8000
```

### Claude Desktop 配置

```json
{
  "mcpServers": {
    "starbucks-ordering": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"],
      "cwd": "/path/to/rec_demo"
    }
  }
}
```

---

## 工具列表

### 1. recommend_products

推荐商品工具，根据用户意图和约束条件返回最佳商品推荐。

#### 参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| `user_id` | string | 是 | 用户唯一标识 |
| `query` | string | 是 | 用户自然语言查询，如"来一杯提神的咖啡" |
| `store_id` | string | 否 | 门店ID，用于库存和门店特色过滤 |
| `session_id` | string | 否 | 会话ID，用于会话内偏好追踪 |
| `constraints` | object | 否 | 硬约束条件，见下表 |
| `top_k` | integer | 否 | 返回推荐数量，默认 2 |
| `context_override` | object | 否 | 上下文覆盖，如 `{"weather": "hot"}` |

#### Constraints 约束参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| `caffeine_free` | boolean | 无咖啡因，过滤所有含咖啡因饮品 |
| `low_calorie` | boolean | 低卡路里 (<100 卡) |
| `dairy_free` | boolean | 无乳制品 |
| `max_price` | number | 最高价格限制 |
| `categories` | string[] | 限定品类，如 `["咖啡", "茶饮"]` |
| `exclude_categories` | string[] | 排除品类 |
| `temperature_only` | string | 限定温度，如 `"冰"` 或 `"热"` |

#### 返回值

```typescript
{
  success: boolean;
  recommendations: Array<{
    product: {
      sku: string;
      name: string;
      english_name: string;
      category: string;
      base_price: number;
      calories: number;
      description: string;
      tags: string[];
      is_new: boolean;
      is_seasonal: boolean;
    };
    customization: {
      temperature: string;      // "冰" | "热" | "少冰" 等
      cup_size: string;         // "TALL" | "GRANDE" | "VENTI"
      sugar_level: string;      // "不另外加糖" | "少糖" 等
      milk_type: string | null; // "全脂奶" | "燕麦奶" 等
      espresso_shots: number | null;
    };
    pricing: {
      base_price: number;
      adjustment: number;       // 客制化价格调整
      final_price: number;
    };
    recommendation: {
      confidence: number;       // 0.0 - 1.0
      confidence_level: string; // "high" | "medium" | "low"
      reason: string;           // 推荐理由
      reason_highlight: string; // 亮点说明
      matched_keywords: string[];
    };
  }>;
  meta: {
    query: string;
    total_candidates: number;
    filtered_count: number;
    constraints_applied: object;
    context: {
      time_period: string;
      store_id: string | null;
    };
  };
  need_clarification: boolean;    // 是否需要追问
  clarification_options: string[]; // 追问选项
  suggested_response: string;      // 建议的AI回复话术
}
```

#### 示例

**请求:**
```json
{
  "name": "recommend_products",
  "arguments": {
    "user_id": "user_12345",
    "query": "来一杯提神的咖啡，不要太贵",
    "constraints": {
      "max_price": 35
    },
    "top_k": 2
  }
}
```

**响应:**
```json
{
  "success": true,
  "recommendations": [
    {
      "product": {
        "sku": "COF005",
        "name": "冷萃咖啡",
        "english_name": "Cold Brew",
        "category": "咖啡",
        "base_price": 32,
        "calories": 5,
        "description": "低温慢萃20小时，口感顺滑无酸涩",
        "tags": ["冷萃", "低卡", "顺滑", "提神"],
        "is_new": true,
        "is_seasonal": false
      },
      "customization": {
        "temperature": "冰",
        "cup_size": "GRANDE",
        "sugar_level": "不另外加糖",
        "milk_type": null,
        "espresso_shots": null
      },
      "pricing": {
        "base_price": 32,
        "adjustment": 0,
        "final_price": 32
      },
      "recommendation": {
        "confidence": 0.72,
        "confidence_level": "high",
        "reason": "冷萃咖啡顺滑浓郁，完美提神，适合你！",
        "reason_highlight": "低温慢萃20小时，咖啡香气醇厚。",
        "matched_keywords": ["提神", "咖啡"]
      }
    }
  ],
  "meta": {
    "query": "来一杯提神的咖啡，不要太贵",
    "total_candidates": 6,
    "filtered_count": 2,
    "constraints_applied": {"max_price": 35},
    "context": {"time_period": "afternoon", "store_id": null}
  },
  "need_clarification": false,
  "clarification_options": [],
  "suggested_response": "为您推荐冷萃咖啡，冰/大杯，32.0元。冷萃咖啡顺滑浓郁，完美提神，适合你！"
}
```

---

### 2. get_user_preferences

获取用户历史偏好，用于个性化推荐和对话上下文理解。

#### 参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| `user_id` | string | 是 | 用户唯一标识 |

#### 返回值

```typescript
{
  success: boolean;
  user_id: string;
  is_new_user: boolean;
  message: string;
  preferences: {
    favorite_categories?: string[];      // 偏好品类
    favorite_items?: string[];           // 常点商品
    temperature_preference?: string;     // 温度偏好
    sweetness_preference?: string;       // 甜度偏好
    milk_preference?: string;            // 奶制品偏好
    avg_order_price?: number;            // 平均订单金额
    order_frequency?: string;            // 下单频率
    last_order_date?: string;            // 最近下单日期
  };
}
```

#### 示例

**请求:**
```json
{
  "name": "get_user_preferences",
  "arguments": {
    "user_id": "user_12345"
  }
}
```

**响应 (老用户):**
```json
{
  "success": true,
  "user_id": "user_12345",
  "is_new_user": false,
  "message": "已获取用户偏好",
  "preferences": {
    "favorite_categories": ["咖啡", "茶饮"],
    "favorite_items": ["美式咖啡", "冷萃咖啡"],
    "temperature_preference": "冰",
    "sweetness_preference": "少糖",
    "milk_preference": "燕麦奶",
    "avg_order_price": 35.5,
    "order_frequency": "高频",
    "last_order_date": "2024-01-15"
  }
}
```

**响应 (新用户):**
```json
{
  "success": true,
  "user_id": "user_new",
  "is_new_user": true,
  "message": "新用户，暂无历史偏好",
  "preferences": {}
}
```

---

### 3. get_store_menu

获取门店菜单和库存信息。

#### 参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| `store_id` | string | 否 | 门店ID，为空则返回全量菜单 |
| `category` | string | 否 | 筛选品类 |

#### 返回值

```typescript
{
  success: boolean;
  store_id: string | null;
  store_name: string | null;
  categories: string[];
  items: Array<{
    sku: string;
    name: string;
    category: string;
    base_price: number;
    available: boolean;
    stock_level: string;  // "high" | "medium" | "low" | "out"
  }>;
  total_count: number;
}
```

---

## REST API 替代方案

如果无法使用 MCP，可直接调用等效的 REST API：

### POST /api/ai-ordering/recommend

```bash
curl -X POST http://localhost:8000/api/ai-ordering/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345",
    "query": "来一杯提神的咖啡",
    "constraints": {"caffeine_free": false, "max_price": 40},
    "top_k": 2
  }'
```

### GET /api/ai-ordering/user-preferences/{user_id}

```bash
curl http://localhost:8000/api/ai-ordering/user-preferences/user_12345
```

---

## 置信度说明

置信度 (confidence) 综合以下因子计算：

| 因子 | 权重 | 说明 |
|------|------|------|
| 语义相似度 | 40% | Query 与商品描述的向量相似度 |
| 行为匹配度 | 25% | 与用户历史偏好的匹配程度 |
| 上下文匹配度 | 20% | 时段、天气等上下文因子匹配 |
| 客制化匹配度 | 15% | 推荐客制化与用户偏好的匹配 |

### 置信度等级

| 等级 | 范围 | 建议行为 |
|------|------|----------|
| high | >= 0.7 | 直接推荐，无需追问 |
| medium | 0.5 - 0.7 | 可推荐，可选择性追问确认 |
| low | < 0.5 | 建议追问澄清用户意图 |

---

## 追问机制

当以下情况发生时，`need_clarification` 为 `true`：

1. **无匹配结果**: 约束条件过于严格，没有符合的商品
2. **低置信度**: 最高置信度 < 0.5，无法确定用户意图
3. **模糊表达**: 用户表达过于笼统（如"随便来一杯"）

追问选项示例：
```json
{
  "need_clarification": true,
  "clarification_options": [
    "您想喝咖啡还是茶饮？",
    "您有什么口味偏好吗？",
    "您对价格有要求吗？"
  ]
}
```

---

## 使用场景示例

### 场景 1: 明确点单

**用户**: "来一杯冰美式"

```json
{
  "query": "来一杯冰美式",
  "constraints": {"temperature_only": "冰"}
}
```

**AI 回复**: "好的，为您推荐冰美式咖啡，大杯，28元。需要调整杯型或加浓缩吗？"

### 场景 2: 模糊推荐

**用户**: "有什么低卡的推荐吗"

```json
{
  "query": "低卡推荐",
  "constraints": {"low_calorie": true}
}
```

**AI 回复**: "为您推荐冷萃咖啡，仅5卡路里，口感顺滑提神！或者您也可以试试美式咖啡~"

### 场景 3: 约束过滤

**用户**: "我不能喝咖啡因，有什么推荐"

```json
{
  "query": "饮品推荐",
  "constraints": {"caffeine_free": true}
}
```

**AI 回复**: "为您推荐芝芝抹茶，无咖啡因茶饮，香浓芝士奶盖配抹茶，颜值与美味并存！"

### 场景 4: 需要追问

**用户**: "来杯喝的"

```json
// 返回 need_clarification: true
```

**AI 回复**: "好的，您想喝咖啡还是茶饮呢？或者告诉我您的口味偏好？"

---

## 错误处理

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| 400 | 参数错误 | 检查必填参数 |
| 404 | 用户不存在 | 视为新用户处理 |
| 500 | 服务器错误 | 降级到基础推荐 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2024-01 | 初始版本，支持基础推荐和约束过滤 |

---

## 附录: 支持的品类和标签

### 品类 (Category)

- 咖啡
- 茶饮
- 星冰乐
- 清爽系列
- 食品

### 常用标签 (Tags)

| 类型 | 标签示例 |
|------|----------|
| 口味 | 甜蜜、浓郁、清爽、果香、奶香 |
| 功能 | 提神、低卡、无咖啡因、养生 |
| 特性 | 新品、限定、网红、经典、人气 |
| 温度 | 冰爽、温暖 |
