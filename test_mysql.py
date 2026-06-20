"""测试MySQL连接并查看数据"""
import pymysql

try:
    # 连接数据库
    connection = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='agricultural_stock',
        charset='utf8mb4'
    )
    print("[成功] 连接到MySQL数据库！\n")

    with connection.cursor() as cursor:
        # 查看所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"[信息] 数据库中有 {len(tables)} 张表：")
        for table in tables:
            print(f"  - {table[0]}")
        print()

        # 查看每张表的数据量
        print("[信息] 各表数据量：")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} 条记录")
        print()

        # 查看每张表的前5条数据
        for table in tables:
            table_name = table[0]
            print(f"[数据] 表 {table_name} 的前5条记录：")
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
            rows = cursor.fetchall()

            # 获取列名
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"  列名: {columns}")

            for row in rows:
                print(f"  {row}")
            print()

    connection.close()
    print("[完成] 数据库连接已关闭")

except pymysql.OperationalError as e:
    print(f"[错误] 连接失败: {e}")
    print("[提示] 请检查：")
    print("  1. MySQL服务是否已启动")
    print("  2. 用户名密码是否正确（默认 root/123456）")
    print("  3. 数据库 agricultural_stock 是否存在")
except Exception as e:
    print(f"[错误] {e}")
