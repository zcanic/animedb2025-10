import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库连接URL
DATABASE_URL = os.getenv('DATABASE_URL')

# 如果DATABASE_URL不存在，则使用示例数据模式
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./anime.db"
    print("Warning: Using SQLite database for local development")

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

# 定义Anime模型
class Anime(Base):
    __tablename__ = "anime"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    year = Column(Integer, index=True)
    average_rating = Column(Float, index=True)
    rating_count = Column(Integer)
    collections = Column(Integer)
    watched = Column(Integer)
    completion_rate = Column(Float)
    img_url = Column(Text)

# 创建表
def create_tables():
    Base.metadata.create_all(bind=engine)

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()