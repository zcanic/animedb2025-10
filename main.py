from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import pandas as pd
import json
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
    conn = sqlite3.connect('anime.db')

    # 读取CSV数据
    df = pd.read_csv('../full_data.csv', encoding='utf-8')

    # 重命名中文列名为英文
    column_mapping = {
        'url': 'url',
        'subject_id': 'subject_id',
        'title': 'title',
        'img_url': 'img_url',
        'year': 'year',
        'supp_title': 'supp_title',
        'year_supp': 'year_supp',
        '收藏': 'collections',
        '看过': 'watched',
        '完成率': 'completion_rate',
        '力荐': 'strong_recommend',
        '标准差': 'rating_std',
        '评分数': 'rating_count',
        '平均分': 'average_rating',
        'has_supp': 'has_supp',
        'infobox_raw': 'infobox_raw',
        'tags': 'tags',
        'character_count': 'character_count',
        'va_count': 'va_count',
        'all_characters': 'all_characters',
        'all_vas': 'all_vas',
        'characters_json': 'characters_json'
    }

    df = df.rename(columns=column_mapping)

    # 处理完成率列，转换为数字
    df['completion_rate'] = df['completion_rate'].str.rstrip('%').astype(float) / 100.0

    # 保存到SQLite数据库
    df.to_sql('anime', conn, if_exists='replace', index=False)

    # 创建索引以提高查询性能
    conn.execute("CREATE INDEX IF NOT EXISTS idx_year ON anime(year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rating ON anime(average_rating)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_collections ON anime(collections)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON anime(title)")

    conn.commit()
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
    conn = sqlite3.connect('anime.db')

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
    conn = sqlite3.connect('anime.db')

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
    conn = sqlite3.connect('anime.db')

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