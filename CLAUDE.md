# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Starbucks-style personalized menu recommendation system with LLM-enhanced semantic matching. Uses OpenAI GPT-4o-mini for user profile generation and recommendation reasoning, text-embedding-3-small for semantic similarity. Includes A/B testing, user behavior tracking, and session-based personalization.

## Commands

```bash
# Install dependencies
uv sync

# Run development server (auto-reload enabled)
uv run uvicorn app.main:app --reload --port 8000

# Test basic recommendation API
uv run python -c "
import httpx
data = {'persona_type': '咖啡重度用户', 'top_k': 3}
r = httpx.post('http://localhost:8000/api/embedding/recommend', json=data, timeout=60)
print(r.json())
"

# Test V2 recommendation with personalization
uv run python -c "
import httpx
data = {'persona_type': '健康达人', 'user_id': 'test_user', 'enable_ab_test': True}
r = httpx.post('http://localhost:8000/api/embedding/recommend/v2', json=data, timeout=60)
print(r.json())
"
```

**Web UI:**
- Main menu: http://localhost:8000/
- Embedding recommendation demo: http://localhost:8000/embedding
- V2 demo with personalization: http://localhost:8000/embedding-v2
- Technical presentation: http://localhost:8000/presentation

## Architecture

```
app/
├── main.py               # FastAPI routes (menu, recommendations, experiments, feedback)
├── models.py             # Pydantic models (MenuItem, Customization, enums)
├── data.py               # Menu item definitions (MENU_ITEMS list, 18 items)
├── llm_service.py        # LLM provider abstraction + OpenAI Embedding service
├── embedding_service.py  # Core recommendation engine (V1 and V2)
├── experiment_service.py # A/B testing, feedback, behavior tracking, session service
├── recommendation.py     # Basic rule-based recommendation (legacy)
├── templates/            # Jinja2 HTML (index, embedding_demo, embedding_demo_v2, presentation)
├── static/               # CSS/JS assets
├── cache/                # Persisted item embeddings (auto-generated)
└── data/                 # Runtime data (user_feedback.json, user_behavior.json, user_orders.json, experiments.json)
```

### Key Components

**LLM Service (`llm_service.py`):**
- Provider pattern: `OpenAIProvider`, `AnthropicProvider`, `FallbackProvider`
- Auto-selects based on available API keys
- `LLMService` singleton for text generation, `OpenAIEmbeddingService` for vectors

**Embedding Recommendation (`embedding_service.py`):**
- `EmbeddingRecommendationEngine.recommend()`: V1 API, 5-step pipeline
- `EmbeddingRecommendationEngine.recommend_v2()`: Enhanced with A/B testing, behavior, session personalization
- `OpenAIEmbeddingVectorService`: Manages item embeddings with disk cache
- `RealLLMService`: Persona templates (健康达人, 咖啡重度用户, 甜品爱好者, 尝鲜派, 实用主义, 养生白领)

**Experiment Service (`experiment_service.py`):**
- `ABTestService`: Hash-based user bucketing, default experiments: `rec_algorithm`, `reason_style`
- `FeedbackService`: Like/dislike/click/order tracking per item
- `BehaviorService`: User order history with time-decay weighting (30-day half-life)
- `SessionService`: Real-time preference updates within a session
- `ExplainabilityService`: Detailed recommendation explanations

**Recommendation Flow (V2):**
1. A/B test assignment for user
2. Generate user profile from persona type → LLM call
3. Embed user search query → OpenAI Embedding API
4. Calculate cosine similarity against cached item embeddings
5. Multi-factor reranking: business rules × behavior boost × session boost
6. Generate recommendation reasons with explainability

## Environment Variables

```bash
LLM_PROVIDER=openai          # "openai" or "anthropic"
OPENAI_API_KEY=sk-xxx        # Required for embeddings + LLM
ANTHROPIC_API_KEY=sk-xxx     # Optional, for Claude fallback
```

If no API keys are set, falls back to `FallbackProvider` (simulated responses).

## Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/embedding/recommend` | POST | V1 recommendation (requires `persona_type`) |
| `/api/embedding/recommend/v2` | POST | V2 with A/B test, behavior, session, explainability |
| `/api/embedding/personas` | GET | List available persona templates |
| `/api/menu` | GET | Full menu with categories |
| `/api/experiments` | GET | List all A/B experiments |
| `/api/feedback` | POST | Record user feedback (like/dislike/click/order) |
| `/api/behavior` | POST | Record user behavior events |
| `/api/orders` | POST | Record order history |
| `/api/orders/simulate` | POST | Generate simulated order history for testing |
| `/api/session/{session_id}` | GET | Get session preferences |

## Notes

- First startup is slow (~10s) as it generates embeddings for all 18 menu items
- Subsequent starts use cached embeddings from `app/cache/`
- Delete cache file to regenerate embeddings after menu changes
- Runtime data (feedback, orders, experiments) stored in `app/data/` (auto-created)
- Behavior boost uses exponential time decay with 30-day half-life
