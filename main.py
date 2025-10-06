from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import json
import os
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI(title="AnimeDB API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库初始化
def init_database():
    # 在Vercel环境中，使用临时文件路径
    db_path = '/tmp/anime.db' if os.environ.get('VERCEL') else 'anime.db'

    # 如果数据库文件已存在，直接返回
    if os.path.exists(db_path):
        print(f"Database already exists at {db_path}")
        return

    conn = sqlite3.connect(db_path)

    try:
        # 读取CSV数据 - 在Vercel中需要从其他位置读取
        # 这里我们使用一个简单的内存数据集作为演示
        # 在实际部署中，您需要将CSV文件上传到Vercel或使用外部存储
        print("Initializing database...")

        # 创建一个简单的示例数据集
        sample_data = [
            (1, "命运石之门", 2011, 8.8, 35783, 66311, 52705, 0.762),
            (2, "魔法少女小圆", 2011, 8.6, 34624, 60794, 51845, 0.843),
            (3, "孤独摇滚", 2022, 8.4, 35009, 62391, 52665, 0.892),
            (4, "进击的巨人", 2013, 8.9, 29908, 56614, 44579, 0.796),
            (5, "钢之炼金术师", 2009, 9.1, 28567, 51262, 43455, 0.912)
        ]

        # 创建表
        conn.execute('''
            CREATE TABLE anime (
                id INTEGER PRIMARY KEY,
                title TEXT,
                year INTEGER,
                average_rating REAL,
                rating_count INTEGER,
                collections INTEGER,
                watched INTEGER,
                completion_rate REAL,
                img_url TEXT,
                tags TEXT
            )
        ''')

        # 插入示例数据
        for data in sample_data:
            conn.execute('''
                INSERT INTO anime (id, title, year, average_rating, rating_count, collections, watched, completion_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)

        # 创建索引
        conn.execute("CREATE INDEX idx_year ON anime(year)")
        conn.execute("CREATE INDEX idx_rating ON anime(average_rating)")
        conn.execute("CREATE INDEX idx_collections ON anime(collections)")
        conn.execute("CREATE INDEX idx_title ON anime(title)")

        conn.commit()
        print("Database initialized successfully")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        # 如果初始化失败，创建一个空的数据库结构
        conn.execute('''
            CREATE TABLE IF NOT EXISTS anime (
                id INTEGER PRIMARY KEY,
                title TEXT,
                year INTEGER,
                average_rating REAL,
                rating_count INTEGER,
                collections INTEGER,
                watched INTEGER,
                completion_rate REAL,
                img_url TEXT,
                tags TEXT
            )
        ''')
        conn.commit()
    finally:
        conn.close()

# 响应模型
class AnimeResponse(BaseModel):
    id: int
    title: str
    year: int
    average_rating: float
    rating_count: int
    collections: int
    watched: int
    completion_rate: float
    img_url: Optional[str]
    tags: Optional[str]

class PaginatedResponse(BaseModel):
    data: List[AnimeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# API路由
@app.get("/")
async def root():
    return {"message": "AnimeDB API is running"}

@app.get("/api/anime")
async def get_anime(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    rating_from: Optional[float] = Query(None, ge=0, le=10),
    rating_to: Optional[float] = Query(None, ge=0, le=10),
    sort_by: str = Query("collections", regex="^(title|year|average_rating|rating_count|collections|watched)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    db_path = '/tmp/anime.db' if os.environ.get('VERCEL') else 'anime.db'
    conn = sqlite3.connect(db_path)

    # 构建查询条件
    where_conditions = []
    params = []

    if search:
        where_conditions.append("title LIKE ?")
        params.append(f"%{search}%")

    if year_from is not None:
        where_conditions.append("year >= ?")
        params.append(year_from)

    if year_to is not None:
        where_conditions.append("year <= ?")
        params.append(year_to)

    if rating_from is not None:
        where_conditions.append("average_rating >= ?")
        params.append(rating_from)

    if rating_to is not None:
        where_conditions.append("average_rating <= ?")
        params.append(rating_to)

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    # 获取总数
    count_query = f"SELECT COUNT(*) FROM anime WHERE {where_clause}"
    total = conn.execute(count_query, params).fetchone()[0]

    # 计算分页
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size

    # 构建排序
    order_clause = f"{sort_by} {sort_order.upper()}"

    # 执行查询
    query = f"""
        SELECT rowid as id, title, year, average_rating, rating_count,
               collections, watched, completion_rate, img_url, tags
        FROM anime
        WHERE {where_clause}
        ORDER BY {order_clause}
        LIMIT ? OFFSET ?
    """

    params.extend([page_size, offset])
    cursor = conn.execute(query, params)

    results = []
    for row in cursor:
        results.append(AnimeResponse(
            id=row[0],
            title=row[1],
            year=row[2],
            average_rating=row[3],
            rating_count=row[4],
            collections=row[5],
            watched=row[6],
            completion_rate=row[7],
            img_url=row[8],
            tags=row[9]
        ))

    conn.close()

    return PaginatedResponse(
        data=results,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@app.get("/api/anime/{anime_id}")
async def get_anime_detail(anime_id: int):
    db_path = '/tmp/anime.db' if os.environ.get('VERCEL') else 'anime.db'
    conn = sqlite3.connect(db_path)

    query = """
        SELECT * FROM anime WHERE rowid = ?
    """

    cursor = conn.execute(query, (anime_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Anime not found")

    # 获取列名
    columns = [description[0] for description in cursor.description]
    anime_data = dict(zip(columns, row))

    conn.close()
    return anime_data

@app.get("/api/stats")
async def get_stats():
    db_path = '/tmp/anime.db' if os.environ.get('VERCEL') else 'anime.db'
    conn = sqlite3.connect(db_path)

    stats = {
        "total_anime": conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0],
        "earliest_year": conn.execute("SELECT MIN(year) FROM anime").fetchone()[0],
        "latest_year": conn.execute("SELECT MAX(year) FROM anime").fetchone()[0],
        "avg_rating": conn.execute("SELECT AVG(average_rating) FROM anime WHERE average_rating > 0").fetchone()[0],
        "total_collections": conn.execute("SELECT SUM(collections) FROM anime").fetchone()[0],
        "total_watched": conn.execute("SELECT SUM(watched) FROM anime").fetchone()[0]
    }

    conn.close()
    return stats

# 初始化数据库
@app.on_event("startup")
async def startup_event():
    try:
        init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")

# 挂载前端静态文件
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)