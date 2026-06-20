from kafka import KafkaConsumer
import json

KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPIC = 'agricultural_stock_topic'

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='agricultural_stock_group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print(f"开始监听Kafka主题 {KAFKA_TOPIC}...")

for message in consumer:
    stock_data = message.value
    print(f"收到消息 - 股票代码: {stock_data['stock_code']}, 股票名称: {stock_data['stock_name']}, 价格: {stock_data['price']}, 涨幅: {stock_data['change']}%, 时间: {stock_data['timestamp']}")
