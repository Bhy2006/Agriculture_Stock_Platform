from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPIC = 'agricultural_stock_topic'

STOCK_CODES = [
    '000860.SZ', '002041.SZ', '002299.SZ', '600598.SH',
    '600354.SH', '000998.SZ', '002556.SZ', '600108.SH'
]

STOCK_NAMES = {
    '000860.SZ': '顺鑫农业',
    '002041.SZ': '登海种业',
    '002299.SZ': '圣农发展',
    '600598.SH': '北大荒',
    '600354.SH': '敦煌种业',
    '000998.SZ': '隆平高科',
    '002556.SZ': '辉隆股份',
    '600108.SH': '亚盛集团'
}

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: str(k).encode('utf-8'),
    retries=3
)

def generate_stock_data(stock_code):
    now = datetime.now()
    base_price = random.uniform(5, 50)
    return {
        "stock_code": stock_code,
        "stock_name": STOCK_NAMES.get(stock_code, "未知"),
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "price": round(base_price, 2),
        "change": round(random.uniform(-2, 2), 2),
        "volume": random.randint(10000, 1000000),
        "amount": round(base_price * random.randint(10000, 1000000), 2),
        "market_cap": round(random.uniform(1000, 100000), 2)
    }

if __name__ == "__main__":
    try:
        print(f"开始向Kafka主题 {KAFKA_TOPIC} 发送数据...")
        
        while True:
            for stock_code in STOCK_CODES:
                stock_data = generate_stock_data(stock_code)
                future = producer.send(
                    topic=KAFKA_TOPIC,
                    key=stock_code,
                    value=stock_data
                )
                record_metadata = future.get(timeout=10)
                print(f"已发送 {stock_data['stock_name']} 到分区: {record_metadata.partition}, 偏移量: {record_metadata.offset}")
            
            time.sleep(5)
            
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        producer.flush()
        producer.close()
        print("Kafka生产者已关闭")
