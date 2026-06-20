import sys
sys.path.insert(0, 'C:\\Users\\18613\\PycharmProjects\\485\\data_collector')
from spider import EastMoneyCollector

collector = EastMoneyCollector()
print('开始采集所有股票的历史数据...')
history = collector.get_all_history(days=30)
print(f'成功采集 {len(history)} 只股票的历史数据')

for code, data in history.items():
    print(f"  {data['stock_name']}({code}): {len(data['history'])} 天历史数据")

collector.save_history_to_csv(history)
print('历史数据采集完成！')