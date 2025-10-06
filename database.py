import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取Vercel PostgreSQL连接URL - 优先使用POSTGRES_URL
DATABASE_URL = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')

# 延迟创建引擎，避免在导入时失败
engine = None
SessionLocal = None

# 创建Base类
Base = declarative_base()

def get_engine():
    """获取数据库引擎，延迟创建"""
    global engine, SessionLocal

    if engine is None:
        if not DATABASE_URL:
            # 如果没有数据库URL，使用SQLite作为后备
            engine = create_engine("sqlite:///./anime.db", connect_args={"check_same_thread": False})
            print("Warning: Using SQLite database for local development")
        else:
            # 使用PostgreSQL - 确保连接字符串包含SSL模式
            try:
                # 确保连接字符串包含sslmode
                if 'sslmode=' not in DATABASE_URL:
                    if '?' in DATABASE_URL:
                        DATABASE_URL += "&sslmode=require"
                    else:
                        DATABASE_URL += "?sslmode=require"

                engine = create_engine(DATABASE_URL)
                print("Successfully connected to PostgreSQL database")

                # 测试连接
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                    print("Database connection test passed")

            except Exception as e:
                print(f"Failed to connect to PostgreSQL: {e}")
                # 后备到SQLite
                engine = create_engine("sqlite:///./anime.db", connect_args={"check_same_thread": False})
                print("Falling back to SQLite database")

        # 创建SessionLocal
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine

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
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

# 数据库依赖
def get_db():
    get_engine()  # 确保引擎已创建
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()