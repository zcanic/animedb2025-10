# Vercel PostgreSQL + FastAPI 部署完整指南

## 1. Vercel PostgreSQL 连接方法

### 连接字符串格式
Vercel PostgreSQL 提供两种连接字符串格式：

```python
# 方法1: 使用环境变量
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Vercel PostgreSQL 环境变量
POSTGRES_URL = os.getenv("POSTGRES_URL")
POSTGRES_PRISMA_URL = os.getenv("POSTGRES_PRISMA_URL")
POSTGRES_URL_NON_POOLING = os.getenv("POSTGRES_URL_NON_POOLING")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")

# 连接函数
def get_db_connection():
    try:
        # 使用连接池URL（推荐）
        if POSTGRES_URL:
            conn = psycopg2.connect(POSTGRES_URL, cursor_factory=RealDictCursor)
        # 或者使用独立参数
        else:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DATABASE,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                cursor_factory=RealDictCursor
            )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
```

### 异步连接（推荐用于 FastAPI）
```python
import os
import asyncpg
from fastapi import FastAPI, Depends

async def get_db():
    conn = await asyncpg.connect(os.getenv("POSTGRES_URL"))
    try:
        yield conn
    finally:
        await conn.close()

app = FastAPI()

@app.get("/data")
async def get_data(db=Depends(get_db)):
    rows = await db.fetch("SELECT * FROM your_table LIMIT 10")
    return {"data": rows}
```

## 2. FastAPI 在 Vercel 上的部署配置

### vercel.json 配置
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/api/main.py"
    }
  ],
  "env": {
    "PYTHONPATH": "./api"
  }
}
```

### 项目结构
```
project/
├── api/
│   ├── main.py          # FastAPI 应用入口
│   ├── dependencies.py  # 数据库依赖
│   ├── models.py        # 数据模型
│   └── routers/         # API 路由
├── requirements.txt     # Python 依赖
└── vercel.json         # Vercel 配置
```

### requirements.txt
```txt
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.7
asyncpg==0.28.0
python-multipart==0.0.6
python-dotenv==1.0.0
```

## 3. Vercel 路由配置最佳实践

### 多路由配置
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1.py"
    },
    {
      "src": "/(.*)",
      "dest": "/api/main.py"
    }
  ]
}
```

### 文件结构示例
```
api/
├── main.py              # 主应用
├── auth.py              # 认证路由
├── users.py             # 用户路由
└── items.py             # 项目路由
```

## 4. 环境变量设置

### Vercel 环境变量配置
在 Vercel 项目设置中添加：

```bash
# 数据库连接
POSTGRES_URL=postgresql://user:password@host:port/database
POSTGRES_PRISMA_URL=postgresql://user:password@host:port/database?pgbouncer=true
POSTGRES_URL_NON_POOLING=postgresql://user:password@host:port/database

# 应用配置
SECRET_KEY=your_secret_key
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com
```

### 本地开发环境 (.env)
```bash
POSTGRES_URL=postgresql://localhost:5432/your_database
SECRET_KEY=local_secret_key
ENVIRONMENT=development
```

## 5. 完整的 FastAPI 应用示例

### api/main.py
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncpg
from typing import Optional

app = FastAPI(title="Anime API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库连接池
class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                os.getenv("POSTGRES_URL"),
                min_size=1,
                max_size=10
            )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def get_connection(self):
        if not self.pool:
            await self.connect()
        return self.pool

db = Database()

# 启动和关闭事件
@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

# 依赖注入
async def get_db():
    pool = await db.get_connection()
    async with pool.acquire() as connection:
        yield connection

# API 路由
@app.get("/")
async def root():
    return {"message": "Anime API is running"}

@app.get("/anime")
async def get_anime(db=Depends(get_db)):
    try:
        rows = await db.fetch("SELECT * FROM anime LIMIT 50")
        return {"anime": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/anime/{anime_id}")
async def get_anime_by_id(anime_id: int, db=Depends(get_db)):
    try:
        row = await db.fetchrow("SELECT * FROM anime WHERE id = $1", anime_id)
        if not row:
            raise HTTPException(status_code=404, detail="Anime not found")
        return {"anime": row}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Vercel 需要这个处理程序
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    # Vercel 服务器less 函数入口
    from mangum import Mangum
    handler = Mangum(app)
```

## 6. 错误排查指南

### 常见问题及解决方案

#### 1. 数据库连接失败
```python
# 检查连接
import psycopg2
try:
    conn = psycopg2.connect(os.getenv("POSTGRES_URL"))
    print("Connection successful")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

#### 2. 环境变量未加载
```python
# 检查环境变量
import os
print("POSTGRES_URL:", "SET" if os.getenv("POSTGRES_URL") else "NOT SET")
print("All environment variables:", dict(os.environ))
```

#### 3. 依赖问题
确保 requirements.txt 包含：
```txt
mangum==0.17.0  # 用于 Vercel serverless 适配
```

#### 4. 路由配置错误
检查 vercel.json 中的路由配置是否正确指向 Python 文件。

### 调试技巧
1. 使用 Vercel CLI 本地测试：`vercel dev`
2. 检查 Vercel 部署日志
3. 使用 try-catch 包装数据库操作
4. 添加详细的错误日志记录

## 7. 性能优化建议

### 连接池配置
```python
# 优化连接池设置
pool = await asyncpg.create_pool(
    os.getenv("POSTGRES_URL"),
    min_size=2,
    max_size=10,
    max_inactive_connection_lifetime=300
)
```

### 查询优化
```python
# 使用参数化查询防止 SQL 注入
async def get_anime_by_genre(genre: str, db=Depends(get_db)):
    return await db.fetch(
        "SELECT * FROM anime WHERE genre = $1 LIMIT 50",
        genre
    )
```

这个指南提供了完整的 Vercel PostgreSQL 和 FastAPI 集成方案，涵盖了从基础连接到生产部署的所有关键环节。
