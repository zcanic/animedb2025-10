from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import json

router = APIRouter()

# 示例数据 - 在实际应用中应该从数据库获取
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
    },
    {
        "id": 4,
        "title": "进击的巨人",
        "year": 2013,
        "average_rating": 8.9,
        "rating_count": 29908,
        "collections": 56614,
        "watched": 44579,
        "completion_rate": 0.796,
        "img_url": ""
    },
    {
        "id": 5,
        "title": "钢之炼金术师",
        "year": 2009,
        "average_rating": 9.1,
        "rating_count": 28567,
        "collections": 51262,
        "watched": 43455,
        "completion_rate": 0.912,
        "img_url": ""
    }
]

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
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    # 过滤数据
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

@router.get("/stats")
async def get_stats():
    total_anime = len(sample_anime_data)
    avg_rating = sum(anime["average_rating"] for anime in sample_anime_data) / total_anime
    total_collections = sum(anime["collections"] for anime in sample_anime_data)
    total_watched = sum(anime["watched"] for anime in sample_anime_data)

    return {
        "total_anime": total_anime,
        "earliest_year": min(anime["year"] for anime in sample_anime_data),
        "latest_year": max(anime["year"] for anime in sample_anime_data),
        "avg_rating": round(avg_rating, 2),
        "total_collections": total_collections,
        "total_watched": total_watched
    }