from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.anime import router as anime_router

app = FastAPI(title="AnimeDB API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(anime_router, prefix="/api/anime", tags=["anime"])

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