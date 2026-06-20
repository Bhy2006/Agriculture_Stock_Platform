"""
MySQL数据库存储模块
包含：数据库连接、数据存储、查询、备份功能
"""
import pymysql
from dbutils.pooled_db import PooledDB
import os
from datetime import datetime
import csv
import gzip

class MySQLStorage:
    """MySQL数据存储类"""
    
    def __init__(self, host='localhost', port=3306, user='root', password='123456', database='agricultural_stock', pool_size=10):
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=pool_size,
            mincached=2,
            maxcached=5,
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        self._init_tables()
    
    def _get_connection(self):
        """获取数据库连接"""
        return self.pool.connection()
    
    def _init_tables(self):
        """初始化数据库表结构"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 股票基础信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_company_info (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stock_code VARCHAR(10) NOT NULL UNIQUE,
                    stock_name VARCHAR(50) NOT NULL,
                    market VARCHAR(10),
                    industry VARCHAR(100),
                    listing_date DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_stock_code (stock_code),
                    INDEX idx_stock_name (stock_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 股票日行情表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_daily_quote (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    stock_code VARCHAR(10) NOT NULL,
                    trade_date DATE NOT NULL,
                    opening_price DECIMAL(10,2),
                    closing_price DECIMAL(10,2),
                    highest_price DECIMAL(10,2),
                    lowest_price DECIMAL(10,2),
                    prev_close DECIMAL(10,2),
                    `change` DECIMAL(10,2),
                    change_percent DECIMAL(10,4),
                    volume BIGINT,
                    amount DECIMAL(18,2),
                    turnover_rate DECIMAL(10,4),
                    market_cap DECIMAL(18,2),
                    pe_ratio DECIMAL(10,4),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_stock_date (stock_code, trade_date),
                    INDEX idx_trade_date (trade_date),
                    UNIQUE KEY uk_stock_date (stock_code, trade_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 股票实时行情表（最新快照）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_realtime (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stock_code VARCHAR(10) NOT NULL UNIQUE,
                    stock_name VARCHAR(50) NOT NULL,
                    price DECIMAL(10,2),
                    open_price DECIMAL(10,2),
                    high_price DECIMAL(10,2),
                    low_price DECIMAL(10,2),
                    prev_close DECIMAL(10,2),
                    `change` DECIMAL(10,2),
                    change_percent DECIMAL(10,4),
                    volume BIGINT,
                    amount DECIMAL(18,2),
                    turnover_rate DECIMAL(10,4),
                    market_cap DECIMAL(18,2),
                    pe_ratio DECIMAL(10,4),
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_stock_code (stock_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 预测数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_prediction (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    stock_code VARCHAR(10) NOT NULL,
                    predict_date DATE NOT NULL,
                    predicted_price DECIMAL(10,2),
                    confidence DECIMAL(5,4),
                    predictor_type VARCHAR(20),
                    current_price DECIMAL(10,2),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_stock_predict_date (stock_code, predict_date),
                    UNIQUE KEY uk_stock_predict_date (stock_code, predict_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 统计分析表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_statistics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stat_date DATE NOT NULL UNIQUE,
                    total_stocks INT,
                    avg_close_price DECIMAL(10,2),
                    total_volume BIGINT,
                    total_amount DECIMAL(18,2),
                    avg_change_percent DECIMAL(10,4),
                    max_price DECIMAL(10,2),
                    min_price DECIMAL(10,2),
                    up_count INT,
                    down_count INT,
                    flat_count INT,
                    top_growth_stock VARCHAR(50),
                    top_growth_value DECIMAL(10,4),
                    bottom_growth_stock VARCHAR(50),
                    bottom_growth_value DECIMAL(10,4),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_stat_date (stat_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            print("MySQL表结构初始化完成")
        except Exception as e:
            print(f"初始化表结构失败: {e}")
    
    def save_company_info(self, data):
        """保存股票公司信息"""
        if not data:
            return False
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for item in data:
                cursor.execute("""
                    INSERT INTO stock_company_info (stock_code, stock_name, market)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE stock_name=VALUES(stock_name), market=VALUES(market), updated_at=NOW()
                """, (item['stock_code'], item['stock_name'], item['market']))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"保存公司信息失败: {e}")
            return False
    
    def save_daily_quote(self, data):
        """保存日行情数据"""
        if not data:
            return False
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for item in data:
                cursor.execute("""
                    INSERT INTO stock_daily_quote (
                        stock_code, trade_date, opening_price, closing_price, highest_price,
                        lowest_price, prev_close, `change`, change_percent, volume, amount,
                        turnover_rate, market_cap, pe_ratio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        opening_price=VALUES(opening_price), closing_price=VALUES(closing_price),
                        highest_price=VALUES(highest_price), lowest_price=VALUES(lowest_price),
                        prev_close=VALUES(prev_close), `change`=VALUES(`change`),
                        change_percent=VALUES(change_percent), volume=VALUES(volume),
                        amount=VALUES(amount), turnover_rate=VALUES(turnover_rate),
                        market_cap=VALUES(market_cap), pe_ratio=VALUES(pe_ratio)
                """, (
                    item['stock_code'], item.get('timestamp', datetime.now()).split(' ')[0],
                    item.get('open'), item.get('price'), item.get('high'),
                    item.get('low'), item.get('prev_close'), item.get('change'),
                    item.get('change_percent'), item.get('volume'), item.get('amount'),
                    item.get('turnover_rate'), item.get('market_cap'), item.get('pe_ratio')
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"保存日行情失败: {e}")
            return False
    
    def save_realtime(self, data):
        """保存实时行情快照"""
        if not data:
            return False
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for item in data:
                cursor.execute("""
                    INSERT INTO stock_realtime (
                        stock_code, stock_name, price, open_price, high_price, low_price,
                        prev_close, `change`, change_percent, volume, amount, turnover_rate, market_cap, pe_ratio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        stock_name=VALUES(stock_name), price=VALUES(price),
                        open_price=VALUES(open_price), high_price=VALUES(high_price),
                        low_price=VALUES(low_price), prev_close=VALUES(prev_close),
                        `change`=VALUES(`change`), change_percent=VALUES(change_percent),
                        volume=VALUES(volume), amount=VALUES(amount),
                        turnover_rate=VALUES(turnover_rate), market_cap=VALUES(market_cap),
                        pe_ratio=VALUES(pe_ratio), update_time=NOW()
                """, (
                    item['stock_code'], item['stock_name'], item.get('price'),
                    item.get('open'), item.get('high'), item.get('low'),
                    item.get('prev_close'), item.get('change'), item.get('change_percent'),
                    item.get('volume'), item.get('amount'), item.get('turnover_rate'),
                    item.get('market_cap'), item.get('pe_ratio')
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"保存实时行情失败: {e}")
            return False
    
    def save_prediction(self, data):
        """保存预测数据"""
        if not data:
            return False
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for item in data:
                for pred in item.get('predictions', []):
                    cursor.execute("""
                        INSERT INTO stock_prediction (
                            stock_code, predict_date, predicted_price, confidence, predictor_type, current_price
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            predicted_price=VALUES(predicted_price), confidence=VALUES(confidence),
                            predictor_type=VALUES(predictor_type), current_price=VALUES(current_price)
                    """, (
                        item['stock_code'], pred['date'], pred['predicted_price'],
                        pred['confidence'], item.get('predictor_type', 'simple'), item.get('current_price')
                    ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"保存预测数据失败: {e}")
            return False
    
    def save_statistics(self, stats, date=None):
        """保存每日统计数据"""
        if not stats:
            return False
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            stat_date = date or datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO daily_statistics (
                    stat_date, total_stocks, avg_close_price, total_volume, total_amount,
                    avg_change_percent, max_price, min_price, up_count, down_count, flat_count,
                    top_growth_stock, top_growth_value, bottom_growth_stock, bottom_growth_value
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    total_stocks=VALUES(total_stocks), avg_close_price=VALUES(avg_close_price),
                    total_volume=VALUES(total_volume), total_amount=VALUES(total_amount),
                    avg_change_percent=VALUES(avg_change_percent), max_price=VALUES(max_price),
                    min_price=VALUES(min_price), up_count=VALUES(up_count),
                    down_count=VALUES(down_count), flat_count=VALUES(flat_count),
                    top_growth_stock=VALUES(top_growth_stock), top_growth_value=VALUES(top_growth_value),
                    bottom_growth_stock=VALUES(bottom_growth_stock), bottom_growth_value=VALUES(bottom_growth_value)
            """, (
                stat_date, stats.get('total_stocks'), stats.get('avg_close_price'),
                stats.get('total_volume'), stats.get('total_amount'), stats.get('avg_change_percent'),
                stats.get('max_price'), stats.get('min_price'), stats.get('up_count'),
                stats.get('down_count'), stats.get('flat_count'), stats.get('top_growth_stock'),
                stats.get('top_growth_value'), stats.get('bottom_growth_stock'), stats.get('bottom_growth_value')
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"保存统计数据失败: {e}")
            return False
    
    def query_by_date(self, date, stock_code=None):
        """按日期查询"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            if stock_code:
                cursor.execute("""
                    SELECT * FROM stock_daily_quote WHERE trade_date = %s AND stock_code = %s
                """, (date, stock_code))
            else:
                cursor.execute("""
                    SELECT * FROM stock_daily_quote WHERE trade_date = %s
                """, (date,))
            
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"按日期查询失败: {e}")
            return []
    
    def query_by_company(self, company_name):
        """按公司名称查询"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            cursor.execute("""
                SELECT r.* FROM stock_realtime r
                JOIN stock_company_info c ON r.stock_code = c.stock_code
                WHERE c.stock_name LIKE %s
            """, (f'%{company_name}%',))
            
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"按公司名称查询失败: {e}")
            return []
    
    def query_history_by_stock(self, stock_code, start_date=None, end_date=None):
        """查询股票历史行情"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            if start_date and end_date:
                cursor.execute("""
                    SELECT * FROM stock_daily_quote 
                    WHERE stock_code = %s AND trade_date BETWEEN %s AND %s
                    ORDER BY trade_date DESC
                """, (stock_code, start_date, end_date))
            else:
                cursor.execute("""
                    SELECT * FROM stock_daily_quote WHERE stock_code = %s ORDER BY trade_date DESC LIMIT 100
                """, (stock_code,))
            
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"查询历史行情失败: {e}")
            return []
    
    def query_realtime_all(self):
        """查询所有实时行情"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM stock_realtime")
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"查询实时行情失败: {e}")
            return []
    
    def backup_data(self, backup_dir='./backups'):
        """备份数据库数据"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'backup_{timestamp}.csv.gz')
            
            conn = self._get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            tables = ['stock_company_info', 'stock_daily_quote', 'stock_realtime', 'stock_prediction', 'daily_statistics']
            
            with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    if rows:
                        f.write(f"-- TABLE: {table}\n")
                        writer = csv.writer(f)
                        writer.writerow(rows[0].keys())
                        for row in rows:
                            writer.writerow(row.values())
                        f.write("\n")
            
            cursor.close()
            conn.close()
            return backup_file
        except Exception as e:
            print(f"备份数据失败: {e}")
            return None
    
    def get_statistics_by_date(self, date):
        """获取指定日期的统计数据"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM daily_statistics WHERE stat_date = %s", (date,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"查询统计数据失败: {e}")
            return None
    
    def get_stock_list(self):
        """获取股票列表"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT stock_code, stock_name, market FROM stock_company_info ORDER BY stock_code")
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return []


if __name__ == "__main__":
    print("测试MySQL存储模块...")
    
    storage = MySQLStorage()
    
    test_company = [{
        'stock_code': '000860',
        'stock_name': '顺鑫农业',
        'market': 'sz'
    }]
    
    print("保存公司信息:", storage.save_company_info(test_company))
    
    test_realtime = [{
        'stock_code': '000860',
        'stock_name': '顺鑫农业',
        'price': 10.15,
        'open': 10.20,
        'high': 10.30,
        'low': 10.05,
        'prev_close': 10.18,
        'change': -0.03,
        'change_percent': -0.29,
        'volume': 12500000,
        'amount': 126875000.0,
        'turnover_rate': 2.35,
        'market_cap': 128.56,
        'pe_ratio': 28.50
    }]
    
    print("保存实时行情:", storage.save_realtime(test_realtime))
    
    stocks = storage.get_stock_list()
    print(f"股票列表: {len(stocks)} 条")
    
    realtime = storage.query_realtime_all()
    print(f"实时行情: {len(realtime)} 条")
    
    backup_file = storage.backup_data()
    print(f"备份文件: {backup_file}")
    
    print("测试完成!")
