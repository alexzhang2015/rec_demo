# /cloudbase-deploy

腾讯云 CloudBase 部署打包技能。生成用于云托管的部署压缩包。

## 功能

- 打包项目代码为 zip 文件
- 自动排除开发/临时文件
- 生成带时间戳的包名
- 显示包大小和内容摘要

## 使用方式

```
/cloudbase-deploy          # 默认打包
/cloudbase-deploy clean    # 清理旧的部署包
/cloudbase-deploy check    # 检查部署配置
```

## 执行步骤

### 1. 检查必要文件

首先确认以下部署必要文件存在：
- `Dockerfile` - 容器构建文件
- `pyproject.toml` - Python 依赖
- `app/main.py` - 应用入口

如果缺失，提醒用户。

### 2. 清理旧包 (如果参数是 clean)

```bash
rm -f starbucks-rec*.zip
```

### 3. 检查配置 (如果参数是 check)

检查并显示：
- Dockerfile 内容摘要
- cloudbaserc.json 配置
- 环境变量要求

### 4. 执行打包 (默认)

执行以下命令创建部署包：

```bash
# 生成带时间戳的文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="starbucks-rec_${TIMESTAMP}.zip"

# 打包，排除不需要的文件（保留 app/cache 用于快速启动）
zip -r "$PACKAGE_NAME" . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.venv*" \
  -x "venv/*" \
  -x ".venv/*" \
  -x "*.env" \
  -x ".env.*" \
  -x "*node_modules*" \
  -x "*.playwright-mcp*" \
  -x "app/data/*.db" \
  -x "app/data/*.json" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x "*.log" \
  -x "logs/*" \
  -x "*.zip" \
  -x "*.tar.gz" \
  -x ".DS_Store" \
  -x "*.swp" \
  -x "*.swo" \
  -x "tests/*" \
  -x ".claude/*" \
  -x ".idea/*" \
  -x ".vscode/*"
```

### 5. 显示结果

打包完成后显示：
- 包文件名和大小
- 包含的主要文件列表 (使用 `unzip -l` 查看前 20 个文件)
- 下一步操作提示

## 输出示例

```
✅ 部署包创建成功！

📦 文件: starbucks-rec_20260117_161500.zip
📏 大小: 2.3 MB

📁 包含文件 (前20个):
  - Dockerfile
  - pyproject.toml
  - uv.lock
  - cloudbaserc.json
  - app/main.py
  - app/embedding_service.py
  ...

🚀 下一步:
1. 登录腾讯云 CloudBase 控制台
2. 进入「云托管」→「新建服务」
3. 选择「压缩包」上传方式
4. 上传 starbucks-rec_20260117_161500.zip
5. 配置环境变量: OPENAI_API_KEY=sk-xxx
6. 点击部署

📖 详细文档: docs/CLOUDBASE_DEPLOY.md
```

## 注意事项

- 确保 `Dockerfile` 和 `pyproject.toml` 存在
- 确保 `app/cache/item_embeddings.json` 存在（容器启动依赖此缓存）
- 如需使用 AI 推荐功能，在 CloudBase 配置 `OPENAI_API_KEY` 环境变量
- 包含缓存后部署包约 700KB-1MB，容器可快速启动无需调用 API
