"""
LLM服务层 - 支持OpenAI和Claude API

使用方法:
1. 设置环境变量 OPENAI_API_KEY 或 ANTHROPIC_API_KEY
2. 设置 LLM_PROVIDER 为 "openai" 或 "anthropic"（默认openai）
"""
import os
import json
import time
from abc import ABC, abstractmethod
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class LLMProvider(ABC):
    """LLM提供者抽象基类"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None) -> dict:
        """生成文本响应"""
        pass

    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: str = None) -> dict:
        """生成JSON格式响应"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API提供者"""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        from openai import OpenAI

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def generate(self, prompt: str, system_prompt: str = None) -> dict:
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        content = response.choices[0].message.content
        elapsed = time.time() - start_time

        return {
            "content": content,
            "model": self.model,
            "provider": "openai",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "latency_ms": round(elapsed * 1000, 2)
        }

    def generate_json(self, prompt: str, system_prompt: str = None) -> dict:
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        elapsed = time.time() - start_time

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"raw": content, "error": "JSON parse failed"}

        return {
            "content": parsed,
            "model": self.model,
            "provider": "openai",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "latency_ms": round(elapsed * 1000, 2)
        }


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API提供者"""

    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        from anthropic import Anthropic

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def generate(self, prompt: str, system_prompt: str = None) -> dict:
        start_time = time.time()

        kwargs = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)

        content = response.content[0].text
        elapsed = time.time() - start_time

        return {
            "content": content,
            "model": self.model,
            "provider": "anthropic",
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            "latency_ms": round(elapsed * 1000, 2)
        }

    def generate_json(self, prompt: str, system_prompt: str = None) -> dict:
        # Claude没有原生JSON模式，通过prompt引导
        json_prompt = f"{prompt}\n\n请以JSON格式返回结果，不要包含任何其他文本。"
        result = self.generate(json_prompt, system_prompt)

        content = result["content"]
        # 尝试提取JSON
        try:
            # 处理可能的markdown代码块
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            parsed = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            parsed = {"raw": content, "error": "JSON parse failed"}

        result["content"] = parsed
        return result


class FallbackProvider(LLMProvider):
    """降级模拟器 - 当没有API key时使用"""

    def __init__(self):
        self.model = "fallback-simulator"

    def generate(self, prompt: str, system_prompt: str = None) -> dict:
        start_time = time.time()
        # 简单的模拟响应
        content = self._simulate_response(prompt)
        elapsed = time.time() - start_time

        return {
            "content": content,
            "model": self.model,
            "provider": "fallback",
            "usage": {"total_tokens": len(prompt) // 4},
            "latency_ms": round(elapsed * 1000, 2)
        }

    def generate_json(self, prompt: str, system_prompt: str = None) -> dict:
        result = self.generate(prompt, system_prompt)
        # 尝试解析为JSON，如果失败返回默认结构
        try:
            result["content"] = json.loads(result["content"])
        except (json.JSONDecodeError, TypeError):
            result["content"] = {"simulated": True, "message": result["content"]}
        return result

    def _simulate_response(self, prompt: str) -> str:
        """基于prompt关键词生成模拟响应"""
        if "商品描述" in prompt or "饮品" in prompt:
            return "这是一款精心调制的饮品，口感醇厚，香气扑鼻，是咖啡爱好者的理想选择。"
        elif "用户画像" in prompt:
            return json.dumps({
                "taste_preference": "偏好醇厚口感",
                "health_consciousness": "中等关注",
                "intent_keywords": ["咖啡", "提神", "美味"]
            }, ensure_ascii=False)
        elif "推荐理由" in prompt:
            return "根据您的偏好推荐，这款饮品非常适合您。"
        else:
            return "这是一个模拟响应，请配置真实的API key以获得更好的效果。"


class LLMService:
    """
    LLM服务统一入口

    自动选择可用的provider:
    1. 优先使用环境变量 LLM_PROVIDER 指定的provider
    2. 如果未指定，按 openai -> anthropic -> fallback 顺序尝试
    """

    def __init__(self):
        self.provider = self._init_provider()
        self.provider_name = type(self.provider).__name__

    def _init_provider(self) -> LLMProvider:
        """初始化LLM提供者"""
        preferred = os.getenv("LLM_PROVIDER", "").lower()

        # 按指定或默认顺序尝试
        if preferred == "anthropic":
            providers_to_try = ["anthropic", "openai", "fallback"]
        else:
            providers_to_try = ["openai", "anthropic", "fallback"]

        for provider_name in providers_to_try:
            try:
                if provider_name == "openai" and os.getenv("OPENAI_API_KEY"):
                    return OpenAIProvider()
                elif provider_name == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
                    return AnthropicProvider()
                elif provider_name == "fallback":
                    print("⚠️  No LLM API key found, using fallback simulator")
                    return FallbackProvider()
            except Exception as e:
                print(f"Failed to init {provider_name}: {e}")
                continue

        return FallbackProvider()

    def generate(self, prompt: str, system_prompt: str = None) -> dict:
        """生成文本响应"""
        return self.provider.generate(prompt, system_prompt)

    def generate_json(self, prompt: str, system_prompt: str = None) -> dict:
        """生成JSON格式响应"""
        return self.provider.generate_json(prompt, system_prompt)

    def get_info(self) -> dict:
        """获取当前provider信息"""
        return {
            "provider": self.provider_name,
            "model": getattr(self.provider, "model", "unknown")
        }


class OpenAIEmbeddingService:
    """
    OpenAI Embedding服务
    使用 text-embedding-3-small 模型
    """

    def __init__(self):
        from openai import OpenAI

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "text-embedding-3-small"
        self.dimension = 1536  # text-embedding-3-small 的维度

    def get_embedding(self, text: str) -> list[float]:
        """获取单个文本的embedding"""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """批量获取embedding（更高效）"""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        # 按原始顺序返回
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    def get_info(self) -> dict:
        return {
            "model": self.model,
            "dimension": self.dimension,
            "provider": "openai"
        }


# 单例
llm_service = LLMService()

# Embedding服务单例（懒加载）
_embedding_service = None

def get_embedding_service() -> OpenAIEmbeddingService:
    """获取Embedding服务（懒加载）"""
    global _embedding_service
    if _embedding_service is None:
        try:
            _embedding_service = OpenAIEmbeddingService()
            print(f"✅ OpenAI Embedding服务已初始化: {_embedding_service.model}")
        except Exception as e:
            print(f"⚠️ OpenAI Embedding服务初始化失败: {e}")
            raise
    return _embedding_service
