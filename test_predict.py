import random
from datetime import datetime, timedelta

base_change = -1.01 / 100
current_price = 2.95
days = 5

print("初始价格:", current_price)
print("涨跌幅:", base_change * 100, "%")
print()

predictions = []
for i in range(days):
    noise = random.uniform(-0.01, 0.01)
    current_price = current_price * (1 + base_change + noise)
    predictions.append({
        "date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d"),
        "predicted_price": round(max(current_price, 0.01), 2),
        "confidence": round(max(0.3, min(0.7, 0.5 + base_change * 10 + random.uniform(-0.1, 0.1))), 2)
    })

print("预测结果:")
for p in predictions:
    print(p)

prices = [p['predicted_price'] for p in predictions]
all_same = len(set(prices)) == 1
print()
print