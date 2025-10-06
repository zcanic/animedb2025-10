import pandas as pd
import os
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def import_csv_to_prisma_postgres():
    """将CSV数据导入到Prisma PostgreSQL数据库"""

    # 获取数据库连接URL
    database_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')

    if not database_url:
        print("Error: No database URL found. Please set POSTGRES_URL or DATABASE_URL environment variable")
        return

    try:
        # 确保连接字符串包含SSL模式
        if 'sslmode=' not in database_url:
            if '?' in database_url:
                database_url += "&sslmode=require"
            else:
                database_url += "?sslmode=require"

        print(f"Connecting to Prisma PostgreSQL: {database_url[:50]}...")

        # 连接到数据库
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("Connected to Prisma PostgreSQL database")

        # 创建表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anime (
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

        # 清空现有数据
        cursor.execute("DELETE FROM anime")

        # 读取CSV文件
        csv_path = "full_data.csv"
        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found at {csv_path}")
            print("Using sample data instead")

            # 插入示例数据
            sample_data = [
                ("命运石之门", 2011, 8.8, 35783, 66311, 52705, 0.762, "https://lain.bgm.tv/r/400/pic/cover/l/11/34/30055_GrfZ7.jpg"),
                ("魔法少女小圆", 2011, 8.6, 34624, 60794, 51845, 0.843, "https://lain.bgm.tv/r/400/pic/cover/l/c4/e0/85799_UoiOt.jpg"),
                ("孤独摇滚", 2022, 8.4, 35009, 62391, 52665, 0.892, "https://lain.bgm.tv/r/400/pic/cover/l/2e/62/29889_C2QHh.jpg")
            ]

            cursor.executemany("""
                INSERT INTO anime (title, year, average_rating, rating_count, collections, watched, completion_rate, img_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, sample_data)

            print("Inserted 3 sample anime records")

        else:
            # 读取CSV数据
            df = pd.read_csv(csv_path)

            # 数据清理和映射
            anime_data = []
            for index, row in df.iterrows():
                try:
                    anime_data.append((
                        row.get('标题', ''),
                        int(row.get('年份', 0)) if pd.notna(row.get('年份')) else 0,
                        float(row.get('平均评分', 0)) if pd.notna(row.get('平均评分')) else 0,
                        int(row.get('评分人数', 0)) if pd.notna(row.get('评分人数')) else 0,
                        int(row.get('收藏数', 0)) if pd.notna(row.get('收藏数')) else 0,
                        int(row.get('看过人数', 0)) if pd.notna(row.get('看过人数')) else 0,
                        float(row.get('完成率', 0)) if pd.notna(row.get('完成率')) else 0,
                        row.get('图片链接', '')
                    ))
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    continue

            # 批量插入数据
            cursor.executemany("""
                INSERT INTO anime (title, year, average_rating, rating_count, collections, watched, completion_rate, img_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, anime_data)

            print(f"Successfully imported {len(anime_data)} anime records")

        # 提交事务
        conn.commit()
        print("Data import completed successfully")

        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM anime")
        count = cursor.fetchone()[0]
        print(f"Total records in database: {count}")

    except Exception as e:
        print(f"Error during data import: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import_csv_to_prisma_postgres()