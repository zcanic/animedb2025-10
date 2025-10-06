from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
from contextlib import contextmanager
import threading
import atexit
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool, PoolError
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="AnimeDB API", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
POOL_MIN_CONN = int(os.getenv("DB_POOL_MIN", "1"))
POOL_MAX_CONN = int(os.getenv("DB_POOL_MAX", "5"))

_db_pool: Optional[SimpleConnectionPool] = None
_pool_lock = threading.Lock()

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _resolve_database_url(prefer_pool: bool = True) -> Optional[str]:
    """按照Vercel文档优先使用 POSTGRES_URL (连接池)"""
    pooled_url = os.getenv("POSTGRES_URL") if prefer_pool else None
    direct_url = os.getenv("POSTGRES_URL_NON_POOLING")
    legacy_url = os.getenv("DATABASE_URL")

    database_url = pooled_url or legacy_url or direct_url

    if database_url and "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url


def _initialise_pool() -> Optional[SimpleConnectionPool]:
    global _db_pool

    with _pool_lock:
        if _db_pool is not None:
            return _db_pool

        database_url = _resolve_database_url(prefer_pool=True)

        if not database_url:
            print("No database URL found, using sample data")
            return None

        try:
            print(f"Initialising PostgreSQL connection pool (max {POOL_MAX_CONN})")
            _db_pool = SimpleConnectionPool(
                POOL_MIN_CONN,
                POOL_MAX_CONN,
                dsn=database_url,
            )

            # 验证连接
            conn = _db_pool.getconn()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            finally:
                _db_pool.putconn(conn)

            print("PostgreSQL connection pool ready")
            return _db_pool
        except Exception as exc:
            print(f"Database pool initialisation failed: {exc}")
            _db_pool = None
            return None


@contextmanager
def get_db_connection():
    """提供一个可复用的数据库连接上下文 (Vercel 推荐连接池)"""
    pool = _db_pool or _initialise_pool()

    if pool is None:
        yield None
        return

    try:
        conn = pool.getconn()
    except PoolError as pool_error:
        print(f"Database pool exhausted: {pool_error}")
        yield None
        return

    try:
        yield conn
        # 如调用方未提交事务，回滚以保持连接干净
        if not conn.closed:
            conn.rollback()
    finally:
        pool.putconn(conn)


def _close_pool():
    global _db_pool
    if _db_pool is not None:
        print("Closing PostgreSQL connection pool")
        _db_pool.closeall()
        _db_pool = None


atexit.register(_close_pool)

# 示例数据 - 当数据库不可用时使用
sample_anime_data = [
    {
        "id": 1,
        "title": "命运石之门",
        "year": 2011,
        "average_rating": 8.8,
        "rating_count": 35783,
        "collections": 66311,
        "watched": 52705,
        "completion_rate": 0.762,
        "img_url": "https://lain.bgm.tv/r/400/pic/cover/l/11/34/30055_GrfZ7.jpg"
    },
    {
        "id": 2,
        "title": "魔法少女小圆",
        "year": 2011,
        "average_rating": 8.6,
        "rating_count": 34624,
        "collections": 60794,
        "watched": 51845,
        "completion_rate": 0.843,
        "img_url": "https://lain.bgm.tv/r/400/pic/cover/l/c4/e0/85799_UoiOt.jpg"
    },
    {
        "id": 3,
        "title": "孤独摇滚",
        "year": 2022,
        "average_rating": 8.4,
        "rating_count": 35009,
        "collections": 62391,
        "watched": 52665,
        "completion_rate": 0.892,
        "img_url": "https://lain.bgm.tv/r/400/pic/cover/l/2e/62/29889_C2QHh.jpg"
    }
]

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
    with get_db_connection() as conn:
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # 首先检查表是否存在
                    cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'anime'
                    );
                """)
                    table_exists = cursor.fetchone()['exists']

                    if not table_exists:
                        print("Table 'anime' does not exist, creating it...")
                        # 创建表
                        cursor.execute("""
                        CREATE TABLE anime (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(255) NOT NULL,
                            year INTEGER,
                            average_rating FLOAT,
                            rating_count INTEGER,
                            collections INTEGER,
                            watched INTEGER,
                            completion_rate FLOAT,
                            img_url TEXT
                        )
                    """)

                        # 插入示例数据
                        for anime in sample_anime_data:
                            cursor.execute("""
                            INSERT INTO anime (title, year, average_rating, rating_count, collections, watched, completion_rate, img_url)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            anime['title'], anime['year'], anime['average_rating'],
                            anime['rating_count'], anime['collections'], anime['watched'],
                            anime['completion_rate'], anime['img_url']
                        ))

                        conn.commit()
                        print("Table 'anime' created with sample data")

                    # 构建查询
                    query = "SELECT * FROM anime WHERE 1=1"
                    params = []

                    # 搜索过滤
                    if search:
                        query += " AND title ILIKE %s"
                        params.append(f"%{search}%")

                    # 年份过滤
                    if year_from is not None:
                        query += " AND year >= %s"
                        params.append(year_from)
                    if year_to is not None:
                        query += " AND year <= %s"
                        params.append(year_to)

                    # 评分过滤
                    if rating_from is not None:
                        query += " AND average_rating >= %s"
                        params.append(rating_from)
                    if rating_to is not None:
                        query += " AND average_rating <= %s"
                        params.append(rating_to)

                    # 排序
                    order_column = sort_by
                    order_direction = "DESC" if sort_order == "desc" else "ASC"
                    query += f" ORDER BY {order_column} {order_direction}"

                    # 获取总数
                    count_query = "SELECT COUNT(*) FROM (" + query + ") as subquery"
                    cursor.execute(count_query, params)
                    total = cursor.fetchone()['count']

                    # 分页
                    offset = (page - 1) * page_size
                    query += " LIMIT %s OFFSET %s"
                    params.extend([page_size, offset])

                    cursor.execute(query, params)
                    anime_data = cursor.fetchall()

                    total_pages = (total + page_size - 1) // page_size

                    return {
                        "data": anime_data,
                        "total": total,
                        "page": page,
                        "page_size": page_size,
                        "total_pages": total_pages
                    }

            except Exception as e:
                print(f"Database query error: {e}")
                return get_fallback_data(page, page_size, search, year_from, year_to, rating_from, rating_to, sort_by, sort_order)

    # 使用示例数据
    return get_fallback_data(page, page_size, search, year_from, year_to, rating_from, rating_to, sort_by, sort_order)

@app.get("/api/anime/stats")
async def get_stats():
    with get_db_connection() as conn:
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # 检查表是否存在
                    cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'anime'
                    );
                """)
                    table_exists = cursor.fetchone()['exists']

                    if not table_exists:
                        return get_fallback_stats()

                    cursor.execute("""
                    SELECT
                        COUNT(*) as total_anime,
                        MIN(year) as earliest_year,
                        MAX(year) as latest_year,
                        AVG(average_rating) as avg_rating,
                        SUM(collections) as total_collections,
                        SUM(watched) as total_watched
                    FROM anime
                """)
                    stats = cursor.fetchone()

                    return {
                        "total_anime": stats['total_anime'] or 0,
                        "earliest_year": stats['earliest_year'] or 0,
                        "latest_year": stats['latest_year'] or 0,
                        "avg_rating": round(float(stats['avg_rating'] or 0), 2),
                        "total_collections": stats['total_collections'] or 0,
                        "total_watched": stats['total_watched'] or 0
                    }

            except Exception as e:
                print(f"Database stats error: {e}")
                return get_fallback_stats()

    # 使用示例统计数据
    return get_fallback_stats()

def get_fallback_data(page, page_size, search, year_from, year_to, rating_from, rating_to, sort_by, sort_order):
    """后备数据 - 当数据库不可用时使用"""
    filtered_data = sample_anime_data.copy()

    # 搜索过滤
    if search:
        filtered_data = [anime for anime in filtered_data if search.lower() in anime["title"].lower()]

    # 年份过滤
    if year_from is not None:
        filtered_data = [anime for anime in filtered_data if anime["year"] >= year_from]
    if year_to is not None:
        filtered_data = [anime for anime in filtered_data if anime["year"] <= year_to]

    # 评分过滤
    if rating_from is not None:
        filtered_data = [anime for anime in filtered_data if anime["average_rating"] >= rating_from]
    if rating_to is not None:
        filtered_data = [anime for anime in filtered_data if anime["average_rating"] <= rating_to]

    # 排序
    reverse = sort_order == "desc"
    filtered_data.sort(key=lambda x: x[sort_by], reverse=reverse)

    # 分页
    total = len(filtered_data)
    total_pages = (total + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    paginated_data = filtered_data[start_idx:end_idx]

    return {
        "data": paginated_data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_fallback_stats():
    """后备统计数据"""
    return {
        "total_anime": len(sample_anime_data),
        "earliest_year": min(anime["year"] for anime in sample_anime_data),
        "latest_year": max(anime["year"] for anime in sample_anime_data),
        "avg_rating": round(sum(anime["average_rating"] for anime in sample_anime_data) / len(sample_anime_data), 2),
        "total_collections": sum(anime["collections"] for anime in sample_anime_data),
        "total_watched": sum(anime["watched"] for anime in sample_anime_data)
    }

@app.get("/")
async def root():
    if FRONTEND_DIR.exists():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        print("Warning: index.html not found in frontend directory")
    return {"message": "AnimeDB API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AnimeDB API is working correctly"}

# 挂载前端静态文件 - 在Vercel中由静态构建处理
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print(f"Warning: frontend directory not found at {FRONTEND_DIR}")
