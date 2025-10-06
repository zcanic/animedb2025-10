# Vercel PostgreSQL + FastAPI 部署指南

## 部署步骤

### 1. 准备项目
确保项目结构如下：
```
anime_csv/
├── api/
│   └── main.py          # FastAPI 应用
├── requirements.txt     # Python 依赖
├── vercel.json         # Vercel 配置
└── .env.example        # 环境变量模板
```

### 2. 安装 Vercel CLI
```bash
npm install -g vercel
```

### 3. 本地测试
```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 本地运行
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 部署到 Vercel
```bash
# 登录 Vercel
vercel login

# 部署项目
vercel --prod
```

## Vercel PostgreSQL 设置

### 1. 创建 PostgreSQL 数据库
1. 登录 Vercel 控制台
2. 进入项目设置
3. 在 "Storage" 部分创建新的 PostgreSQL 数据库
4. 复制连接字符串

### 2. 配置环境变量
在 Vercel 项目设置中添加以下环境变量：

```bash
POSTGRES_URL=你的PostgreSQL连接字符串
POSTGRES_PRISMA_URL=你的Prisma连接字符串
POSTGRES_URL_NON_POOLING=你的非连接池字符串
SECRET_KEY=你的应用密钥
ENVIRONMENT=production
CORS_ORIGINS=你的前端域名
```

## 数据库初始化

部署后，访问以下端点初始化数据库：

```bash
# 初始化数据库表
POST https://your-app.vercel.app/admin/init-database
```

## API 端点

### 基础端点
- `GET /` - 应用状态
- `GET /health` - 健康检查

### 动漫数据端点
- `GET /anime` - 获取动漫列表
- `GET /anime/{id}` - 获取特定动漫
- `GET /anime/search?query=搜索词` - 搜索动漫

### 管理端点
- `POST /admin/init-database` - 初始化数据库（仅开发）

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 POSTGRES_URL 环境变量是否正确
   - 确认数据库服务已启动

2. **路由 404 错误**
   - 检查 vercel.json 配置
   - 确保文件路径正确

3. **依赖安装失败**
   - 检查 requirements.txt 格式
   - 确认 Python 版本兼容性

### 调试方法

1. **查看部署日志**
   ```bash
   vercel logs
   ```

2. **本地调试**
   ```bash
   vercel dev
   ```

3. **检查环境变量**
   ```bash
   vercel env ls
   ```

## 性能优化

1. **启用连接池** - 使用 POSTGRES_URL 而非非池化连接
2. **添加索引** - 为常用查询字段添加数据库索引
3. **使用异步操作** - 充分利用 FastAPI 的异步特性
4. **配置缓存** - 为静态数据添加缓存层

## 安全建议

1. **环境变量保护** - 不要将敏感信息提交到代码仓库
2. **CORS 配置** - 限制允许的域名
3. **输入验证** - 使用 FastAPI 的验证功能
4. **SQL 注入防护** - 使用参数化查询

这个指南涵盖了从本地开发到生产部署的完整流程。