# 腾讯云 CloudBase 部署指南

## 快速部署

### 方式一：控制台上传压缩包

1. **打包代码**
```bash
# 在项目根目录执行
zip -r starbucks-rec.zip . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.venv*" \
  -x "*.env*" \
  -x "*node_modules*" \
  -x "*.playwright-mcp*" \
  -x "app/data/*.db" \
  -x "app/data/*.json"
```

2. **登录 CloudBase 控制台**
   - 访问 https://console.cloud.tencent.com/tcb
   - 选择环境 → 云托管 → 新建服务

3. **配置服务**

| 配置项 | 值 |
|--------|-----|
| 服务名称 | `starbucks-rec` |
| 代码包类型 | 压缩包 |
| 服务端口 | `80` |
| 访问端口 | `80` |

4. **环境变量设置**

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `OPENAI_API_KEY` | `sk-xxx` | OpenAI API 密钥 (必填) |
| `LLM_PROVIDER` | `openai` | LLM 提供商 |

5. **构建设置**
   - Dockerfile 路径: `Dockerfile`
   - 构建目录: `/`

6. **更多配置**
   - CPU: 1 核
   - 内存: 2 GB
   - 最小副本数: 0 (按量计费)
   - 最大副本数: 10
   - 扩缩容策略: CPU 使用率 60%

---

### 方式二：CLI 部署

1. **安装 CloudBase CLI**
```bash
npm install -g @cloudbase/cli
```

2. **登录**
```bash
tcb login
```

3. **初始化环境**
```bash
# 设置环境 ID
export ENV_ID=your-env-id
export OPENAI_API_KEY=sk-xxx
```

4. **部署**
```bash
tcb framework deploy
```

---

### 方式三：Docker 本地构建后推送

1. **本地构建镜像**
```bash
docker build -t starbucks-rec:latest .
```

2. **测试运行**
```bash
docker run -d \
  -p 8080:80 \
  -e OPENAI_API_KEY=sk-xxx \
  --name starbucks-rec \
  starbucks-rec:latest
```

3. **访问测试**
```bash
# 健康检查
curl http://localhost:8080/api/health

# 推荐接口
curl -X POST http://localhost:8080/api/ai-ordering/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","query":"来一杯咖啡","top_k":2}'
```

4. **推送到腾讯云镜像仓库**
```bash
# 登录镜像仓库
docker login ccr.ccs.tencentyun.com -u xxx

# 打标签
docker tag starbucks-rec:latest \
  ccr.ccs.tencentyun.com/your-namespace/starbucks-rec:latest

# 推送
docker push ccr.ccs.tencentyun.com/your-namespace/starbucks-rec:latest
```

5. **在 CloudBase 控制台选择镜像部署**

---

## 文件结构

```
rec_demo/
├── Dockerfile           # Docker 构建文件
├── .dockerignore        # Docker 忽略文件
├── cloudbaserc.json     # CloudBase 配置
├── pyproject.toml       # Python 依赖
├── uv.lock              # 依赖锁定
└── app/
    ├── main.py          # FastAPI 入口
    ├── data/            # 运行时数据 (自动创建)
    ├── cache/           # Embedding 缓存
    ├── static/          # 静态资源
    └── templates/       # HTML 模板
```

---

## 环境变量说明

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `OPENAI_API_KEY` | 是 | - | OpenAI API 密钥 |
| `LLM_PROVIDER` | 否 | `openai` | LLM 提供商 (openai/anthropic) |
| `ANTHROPIC_API_KEY` | 否 | - | Anthropic API 密钥 (备用) |

---

## 健康检查

CloudBase 会定期调用健康检查端点确认服务状态：

```
GET /api/health
```

响应：
```json
{
  "status": "healthy",
  "service": "starbucks-recommendation",
  "version": "1.0.0"
}
```

---

## 常见问题

### Q: 首次启动较慢？
A: 首次启动需要生成商品 Embedding 缓存 (约 10-30 秒)，后续启动会使用缓存。

### Q: 如何查看日志？
A: CloudBase 控制台 → 云托管 → 服务详情 → 日志

### Q: API 超时？
A: 检查 OPENAI_API_KEY 是否正确配置，建议超时设置 60s+

### Q: 如何更新部署？
A: 重新上传压缩包或执行 `tcb framework deploy`

---

## 费用估算

CloudBase 云托管按实际使用计费：

| 资源 | 规格 | 单价 (参考) |
|------|------|-------------|
| CPU | 1 核 | 约 0.055 元/核/小时 |
| 内存 | 2 GB | 约 0.032 元/GB/小时 |
| 流量 | - | 约 0.8 元/GB |

**提示**: 设置最小副本数为 0 可实现无请求时零费用。

---

## 访问地址

部署成功后，访问地址格式：
```
https://{envId}.service.tcloudbase.com/starbucks-rec/
```

主要页面：
- 首页 (智能推荐演示): `/`
- 经典菜单: `/classic`
- 技术方案PPT: `/presentation`
- 健康检查: `/api/health`
- AI点单API: `/api/ai-ordering/recommend`
