from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from database import get_db, Anime

router = APIRouter()

@router.get("/")
async def get_anime(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    rating_from: Optional[float] = Query(None, ge=0, le=10),
    rating_to: Optional[float] = Query(None, ge=0, le=10),
    sort_by: str = Query("collections", regex="^(title|year|average_rating|rating_count|collections|watched)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    try:
        # 构建查询
        query = db.query(Anime)

        # 搜索过滤
        if search:
            query = query.filter(Anime.title.ilike(f"%{search}%"))

        # 年份过滤
        if year_from is not None:
            query = query.filter(Anime.year >= year_from)
        if year_to is not None:
            query = query.filter(Anime.year <= year_to)

        # 评分过滤
        if rating_from is not None:
            query = query.filter(Anime.average_rating >= rating_from)
        if rating_to is not None:
            query = query.filter(Anime.average_rating <= rating_to)

        # 排序
        order_column = getattr(Anime, sort_by)
        if sort_order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        # 获取总数
        total = query.count()

        # 分页
        total_pages = (total + page_size - 1) // page_size
        start_idx = (page - 1) * page_size

        anime_data = query.offset(start_idx).limit(page_size).all()

        # 转换为字典格式
        anime_list = []
        for anime in anime_data:
            anime_list.append({
                "id": anime.id,
                "title": anime.title,
                "year": anime.year,
                "average_rating": anime.average_rating,
                "rating_count": anime.rating_count,
                "collections": anime.collections,
                "watched": anime.watched,
                "completion_rate": anime.completion_rate,
                "img_url": anime.img_url
            })

        return {
            "data": anime_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    except Exception as e:
        # 如果数据库查询失败，返回示例数据作为后备
        print(f"Database error: {e}")
        return get_fallback_data(page, page_size, search, year_from, year_to, rating_from, rating_to, sort_by, sort_order)

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    try:
        # 从数据库获取统计数据
        total_anime = db.query(func.count(Anime.id)).scalar()
        avg_rating = db.query(func.avg(Anime.average_rating)).scalar()
        total_collections = db.query(func.sum(Anime.collections)).scalar()
        total_watched = db.query(func.sum(Anime.watched)).scalar()
        earliest_year = db.query(func.min(Anime.year)).scalar()
        latest_year = db.query(func.max(Anime.year)).scalar()

        return {
            "total_anime": total_anime or 0,
            "earliest_year": earliest_year or 0,
            "latest_year": latest_year or 0,
            "avg_rating": round(avg_rating, 2) if avg_rating else 0,
            "total_collections": total_collections or 0,
            "total_watched": total_watched or 0
        }

    except Exception as e:
        # 如果数据库查询失败，返回示例统计数据
        print(f"Database stats error: {e}")
        return get_fallback_stats()

def get_fallback_data(page, page_size, search, year_from, year_to, rating_from, rating_to, sort_by, sort_order):
    """后备数据 - 当数据库不可用时使用"""
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

    # 过滤数据
    filtered_data = sample_anime_data.copy()

    if search:
        filtered_data = [anime for anime in filtered_data if search.lower() in anime["title"].lower()]

    if year_from is not None:
        filtered_data = [anime for anime in filtered_data if anime["year"] >= year_from]
    if year_to is not None:
        filtered_data = [anime for anime in filtered_data if anime["year"] <= year_to]

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
        "total_anime": 3,
        "earliest_year": 2011,
        "latest_year": 2022,
        "avg_rating": 8.6,
        "total_collections": 189496,
        "total_watched": 157215
    }