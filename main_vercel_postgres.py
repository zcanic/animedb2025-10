from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="AnimeDB API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """获取数据库连接"""
    try:
        # 优先使用Vercel PostgreSQL连接
        database_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')

        if database_url:
            # 确保连接字符串包含SSL模式
            if 'sslmode=' not in database_url:
                if '?' in database_url:
                    database_url += "&sslmode=require"
                else:
                    database_url += "?sslmode=require"

            conn = psycopg2.connect(database_url)
            print("Connected to Vercel PostgreSQL")
            return conn
        else:
            # 后备到示例数据模式
            print("No database URL found, using sample data")
            return None

    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Falling back to sample data")
        return None

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

@app.get("/api/anime/")
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
    conn = get_db_connection()

    if conn:
        # 使用PostgreSQL数据库
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
            # 后备到示例数据
            conn.close()
            return get_fallback_data(page, page_size, search, year_from, year_to, rating_from, rating_to, sort_by, sort_order)
        finally:
            conn.close()
    else:
        # 使用示例数据
        return get_fallback_data(page, page_size, search, year_from, year_to, rating_from, rating_to, sort_by, sort_order)

@app.get("/api/anime/stats")
async def get_stats():
    conn = get_db_connection()

    if conn:
        # 使用PostgreSQL数据库
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
            # 后备到示例统计数据
            conn.close()
            return get_fallback_stats()
        finally:
            conn.close()
    else:
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
    return {"message": "AnimeDB API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "AnimeDB API is working correctly"}

# 挂载前端静态文件
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)