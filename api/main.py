from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncpg
from typing import Optional, List
import json

app = FastAPI(
    title="Anime CSV API",
    description="API for managing anime data from CSV files",
    version="1.0.0"
)

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
            # 使用 Vercel PostgreSQL 连接字符串
            postgres_url = os.getenv("POSTGRES_URL")
            if not postgres_url:
                print("Warning: POSTGRES_URL environment variable not set")
                return

            self.pool = await asyncpg.create_pool(
                postgres_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            print("Database connection pool created")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("Database connection pool closed")

    async def get_connection(self):
        if not self.pool:
            await self.connect()
        return self.pool

db = Database()

# 启动和关闭事件
@app.on_event("startup")
async def startup():
    await db.connect()
    print("FastAPI application started")

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
    print("FastAPI application stopped")

# 依赖注入
async def get_db():
    pool = await db.get_connection()
    if not pool:
        raise HTTPException(status_code=500, detail="Database not available")
    async with pool.acquire() as connection:
        yield connection

# API 路由
@app.get("/")
async def root():
    return {
        "message": "Anime CSV API is running",
        "version": "1.0.0",
        "database": "connected" if db.pool else "disconnected"
    }

@app.get("/health")
async def health_check(db=Depends(get_db)):
    """健康检查端点"""
    try:
        # 测试数据库连接
        result = await db.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-10-06T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.get("/anime")
async def get_anime_list(
    db=Depends(get_db),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """获取动漫列表"""
    try:
        # 检查表是否存在
        table_exists = await db.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'anime'
            )
        """)

        if not table_exists:
            return {
                "anime": [],
                "total": 0,
                "message": "Anime table does not exist yet"
            }

        # 获取数据
        rows = await db.fetch(
            "SELECT * FROM anime ORDER BY id LIMIT $1 OFFSET $2",
            limit, offset
        )

        total_count = await db.fetchval("SELECT COUNT(*) FROM anime")

        return {
            "anime": rows,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/anime/{anime_id}")
async def get_anime_by_id(anime_id: int, db=Depends(get_db)):
    """根据ID获取动漫详情"""
    try:
        row = await db.fetchrow("SELECT * FROM anime WHERE id = $1", anime_id)
        if not row:
            raise HTTPException(status_code=404, detail="Anime not found")
        return {"anime": row}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/anime/search")
async def search_anime(
    db=Depends(get_db),
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    """搜索动漫"""
    try:
        search_pattern = f"%{query}%"
        rows = await db.fetch("""
            SELECT * FROM anime
            WHERE title ILIKE $1 OR genre ILIKE $1 OR studio ILIKE $1
            LIMIT $2
        """, search_pattern, limit)

        return {
            "query": query,
            "results": rows,
            "count": len(rows)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# 数据库初始化端点（仅用于开发）
@app.post("/admin/init-database")
async def init_database(db=Depends(get_db)):
    """初始化数据库表结构"""
    try:
        # 创建 anime 表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS anime (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                genre VARCHAR(100),
                episodes INTEGER,
                rating DECIMAL(3,2),
                studio VARCHAR(100),
                year INTEGER,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        await db.execute("CREATE INDEX IF NOT EXISTS idx_anime_title ON anime(title)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_anime_genre ON anime(genre)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_anime_year ON anime(year)")

        return {"message": "Database initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization error: {str(e)}")

# Vercel serverless 适配
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    # Vercel serverless 函数入口
    try:
        from mangum import Mangum
        handler = Mangum(app)
    except ImportError:
        print("Mangum not available - running in development mode")