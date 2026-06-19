import psycopg2

try:

    conn = psycopg2.connect(
        database="smart_fish_db",
        user="postgres",
        password="Zyl104869",
        port="5432"
    )
    print("✅ 恭喜！硬编码连接成功了！")
    conn.close()
except Exception as e:
    print(f"❌ 依然失败: {e}")