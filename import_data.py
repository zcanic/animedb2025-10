import pandas as pd
import os
from sqlalchemy import create_engine
from database import Anime, Base
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def import_csv_to_postgres():
    """将CSV数据导入到PostgreSQL数据库"""

    # 获取数据库连接URL
    DATABASE_URL = os.getenv('DATABASE_URL')

    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        return

    try:
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL)

        # 创建表
        Base.metadata.create_all(bind=engine)

        # 读取CSV文件
        csv_path = "full_data.csv"
        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found at {csv_path}")
            return

        # 读取CSV数据
        df = pd.read_csv(csv_path)

        # 数据清理和映射
        anime_data = []
        for index, row in df.iterrows():
            try:
                anime = Anime(
                    id=index + 1,
                    title=row.get('标题', ''),
                    year=int(row.get('年份', 0)) if pd.notna(row.get('年份')) else 0,
                    average_rating=float(row.get('平均评分', 0)) if pd.notna(row.get('平均评分')) else 0,
                    rating_count=int(row.get('评分人数', 0)) if pd.notna(row.get('评分人数')) else 0,
                    collections=int(row.get('收藏数', 0)) if pd.notna(row.get('收藏数')) else 0,
                    watched=int(row.get('看过人数', 0)) if pd.notna(row.get('看过人数')) else 0,
                    completion_rate=float(row.get('完成率', 0)) if pd.notna(row.get('完成率')) else 0,
                    img_url=row.get('图片链接', '')
                )
                anime_data.append(anime)
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue

        # 批量插入数据
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # 清空现有数据
            db.query(Anime).delete()

            # 批量插入新数据
            db.bulk_save_objects(anime_data)
            db.commit()

            print(f"Successfully imported {len(anime_data)} anime records")

        except Exception as e:
            db.rollback()
            print(f"Error during database operation: {e}")
        finally:
            db.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import_csv_to_postgres()