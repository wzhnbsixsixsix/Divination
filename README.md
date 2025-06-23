# FateWave 占卜系统后端

这是一个基于 FastAPI 的占卜系统后端，集成了 OpenRouter API 用于提供 AI 占卜服务。

## 功能特性

- 🔮 **占卜服务**: 集成 OpenRouter API，支持多语言占卜
- 📊 **使用统计**: 记录和统计用户使用情况
- 🏪 **历史记录**: 保存用户的占卜历史
- 🔒 **使用限制**: 支持免费用户使用次数限制
- 📝 **会话管理**: 支持匿名用户的会话追踪
- 🛡️ **安全性**: API 密钥后端管理，避免前端暴露
- 📋 **完整日志**: 记录所有 API 调用和使用统计

## 快速开始

### 1. 环境要求

- Python 3.8+
- PostgreSQL 12+

### 2. 安装依赖

```bash
cd DivinationBackend
pip install -r requirements.txt
```

### 3. 配置环境变量

复制并编辑环境变量文件：

```bash
cp env.example .env
```

修改 `.env` 文件中的配置：

```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/divination_db

# OpenRouter API 密钥
OPENROUTER_API_KEY=your_openrouter_api_key_here

# JWT 密钥（可以用 openssl rand -hex 32 生成）
SECRET_KEY=your_secret_key_here

# 应用配置
DEBUG=True
CORS_ORIGINS=http://localhost:3000,https://fatewave.com

# 免费使用次数限制
FREE_USAGE_LIMIT=3
```

### 4. 创建数据库

```bash
# 创建 PostgreSQL 数据库
createdb divination_db
```

### 5. 运行应用

```bash
# 开发环境运行
python main.py

# 或者使用 uvicorn 直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs` 查看 API 文档。

## API 接口

### 核心接口

#### 1. 创建占卜 `POST /api/divination`

```json
{
  "question": "我的事业运势如何？",
  "language": "zh-CN",
  "session_id": "optional-session-id"
}
```

#### 2. 获取使用统计 `GET /api/divination/usage`

```bash
GET /api/divination/usage?session_id=your-session-id
```

#### 3. 获取占卜历史 `GET /api/divination/history`

```bash
GET /api/divination/history?session_id=your-session-id&page=1&size=10
```

#### 4. 创建会话 `POST /api/divination/session`

返回新的会话 ID 用于匿名用户追踪。

### 系统接口

- `GET /health` - 健康检查
- `GET /` - 系统信息
- `GET /test/openrouter` - 测试 OpenRouter 连接（仅调试模式）

## 数据库结构

### 主要表

1. **users** - 用户表
   - 用户信息、使用统计、会员状态

2. **divinations** - 占卜记录表
   - 问题、答案、时间戳、用户关联

3. **usage_logs** - 使用日志表
   - API 调用记录、统计信息

## 前端集成

### 替换前端 API 调用

将前端的 OpenRouter 直接调用改为后端 API：

```typescript
// 旧的前端代码
const completion = await client.chat.completions.create({...});

// 新的后端调用
const response = await fetch('/api/divination', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: question,
    language: 'zh-CN',
    session_id: sessionId
  })
});

const data = await response.json();
```

### 会话管理

```typescript
// 获取或创建会话ID
let sessionId = localStorage.getItem('fatewave_session');

if (!sessionId) {
  const response = await fetch('/api/divination/session', {
    method: 'POST'
  });
  const data = await response.json();
  sessionId = data.data.session_id;
  localStorage.setItem('fatewave_session', sessionId);
}
```

## 部署建议

### 生产环境配置

1. 设置 `DEBUG=False`
2. 使用强密码和安全的数据库连接
3. 配置 HTTPS
4. 设置适当的 CORS 策略
5. 使用 Gunicorn 或 uWSGI 作为 WSGI 服务器

### Docker 部署（可选）

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 安全考虑

1. **API 密钥安全**: OpenRouter API 密钥只在后端使用，不会暴露给前端
2. **使用限制**: 实现了免费用户的使用次数限制
3. **日志记录**: 记录所有 API 调用用于监控和审计
4. **CORS 配置**: 限制跨域请求来源

## 监控和维护

- 查看 `/health` 端点监控服务状态
- 检查数据库中的 `usage_logs` 表了解使用情况
- 定期清理旧的日志记录

## 许可证

本项目采用 MIT 许可证。 # Divination
