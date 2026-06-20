"""
腾讯股票实时行情数据采集器（东方财富接口被屏蔽，使用腾讯备用数据源）
接口: https://qt.gtimg.cn/q=sh600598,sz000860
格式: v_sh600598="1~股票名~代码~当前价~昨收~今开~成交量(手)~外盘~内盘~买一价~买一量~..."
"""
import requests
import time
import random
import re
import json
import threading
from datetime import datetime
import os
import sys


class TencentStockCollector:
    """腾讯股票数据采集器"""

    AGRICULTURAL_STOCKS = [
        {"code": "000860", "market": "sz", "name": "顺鑫农业", "symbol": "sz000860"},
        {"code": "002041", "market": "sz", "name": "登海种业", "symbol": "sz002041"},
        {"code": "002299", "market": "sz", "name": "圣农发展", "symbol": "sz002299"},
        {"code": "002385", "market": "sz", "name": "大北农", "symbol": "sz002385"},
        {"code": "000998", "market": "sz", "name": "隆平高科", "symbol": "sz000998"},
        {"code": "600598", "market": "sh", "name": "北大荒", "symbol": "sh600598"},
        {"code": "600354", "market": "sh", "name": "敦煌种业", "symbol": "sh600354"},
        {"code": "600108", "market": "sh", "name": "亚盛集团", "symbol": "sh600108"},
        {"code": "600127", "market": "sh", "name": "金健米业", "symbol": "sh600127"},
        {"code": "000061", "market": "sz", "name": "农产品", "symbol": "sz000061"},
        {"code": "600540", "market": "sh", "name": "新赛股份", "symbol": "sh600540"},
        {"code": "600962", "market": "sh", "name": "国投中鲁", "symbol": "sh600962"},
        {"code": "000876", "market": "sz", "name": "新希望", "symbol": "sz000876"},
        {"code": "002714", "market": "sz", "name": "牧原股份", "symbol": "sz002714"},
        {"code": "300498", "market": "sz", "name": "温氏股份", "symbol": "sz300498"},
        {"code": "002311", "market": "sz", "name": "海大集团", "symbol": "sz002311"},
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://gu.qq.com/",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })

    def fetch_quotes(self, symbols=None):
        """批量获取股票行情"""
        if symbols is None:
            symbols = [s["symbol"] for s in self.AGRICULTURAL_STOCKS]

        # 腾讯接口支持批量查询，用逗号分隔
        url = "https://qt.gtimg.cn/q=" + ",".join(symbols)
        try:
            resp = self.session.get(url, timeout=10)
            resp.encoding = "gbk"
            return self._parse_response(resp.text)
        except Exception as e:
            print(f"[采集失败] {e}")
            return []

    def _parse_response(self, text):
        """解析腾讯股票返回的数据"""
        results = []
        # 格式: v_sh600598="1~股票名~代码~当前价~昨收~今开~..."
        pattern = r'v_(\w+)="([^"]+)"'
        matches = re.findall(pattern, text)

        for symbol, content in matches:
            parts = content.split("~")
            if len(parts) < 40:
                continue
            try:
                # 关键字段（根据腾讯接口顺序）:
                # [0] 1 [1] 名称 [2] 代码 [3] 当前价 [4] 昨收 [5] 今开
                # [6] 成交量(手) [7] 外盘 [8] 内盘
                # [9-18] 买一~买五价格/量
                # [19-28] 卖一~卖五价格/量
                # [29] 日期 [30] 时间
                # [31] 涨跌额 [32] 涨跌幅
                # [33] 最高 [34] 最低
                # [35-37] 价格/成交量/成交额
                # [38] 换手率 [39] 市盈率
                # [44] 最高 [45] 最低 [46] 振幅
                # [47] 流通市值(亿) [48] 总市值(亿) [49] 市净率
                # [50] 涨停价 [51] 跌停价

                name = parts[1]
                code = parts[2]
                price = float(parts[3]) if parts[3] else 0
                prev_close = float(parts[4]) if parts[4] else 0
                open_price = float(parts[5]) if parts[5] else 0
                volume_hand = float(parts[6]) if parts[6] else 0
                change = float(parts[31]) if parts[31] else 0
                change_pct = float(parts[32]) if parts[32] else 0
                high = float(parts[33]) if parts[33] else 0
                low = float(parts[34]) if parts[34] else 0
                amount = float(parts[37]) if len(parts) > 37 and parts[37] else 0
                turnover = float(parts[38]) if len(parts) > 38 and parts[38] else 0
                pe = float(parts[39]) if len(parts) > 39 and parts[39] else 0
                amplitude = float(parts[46]) if len(parts) > 46 and parts[46] else 0
                circulation_cap = float(parts[47]) if len(parts) > 47 and parts[47] else 0
                market_cap = float(parts[48]) if len(parts) > 48 and parts[48] else 0

                if price <= 0:
                    continue

                # 验证股票名称是否在列表中
                expected_name = next((s["name"] for s in self.AGRICULTURAL_STOCKS if s["symbol"] == symbol), None)

                results.append({
                    "stock_code": code,
                    "stock_name": name,
                    "market": "sz" if symbol.startswith("sz") else "sh",
                    "symbol": symbol,
                    "price": round(price, 2),
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "prev_close": round(prev_close, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                    "amplitude": round(amplitude, 2),
                    "volume": int(volume_hand * 100),  # 手转股
                    "amount": round(amount * 10000, 2),  # 万元转元
                    "turnover_rate": round(turnover, 2),
                    "pe_ratio": round(pe, 2),
                    "market_cap": round(market_cap, 2),  # 亿元
                    "circulation_cap": round(circulation_cap, 2),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            except (ValueError, IndexError) as e:
                continue

        return results


class RealtimeDataHub:
    """实时数据中枢：定时拉取并缓存数据"""

    def __init__(self, refresh_interval=5):
        self.collector = TencentStockCollector()
        self.refresh_interval = refresh_interval
        self.data = []
        self.last_update = None
        self.is_running = False
        self.thread = None
        self._lock = threading.Lock()

    def update_data(self):
        """执行一次数据更新"""
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] 正在从腾讯财经更新行情数据...")
            new_data = self.collector.fetch_quotes()
            if new_data:
                with self._lock:
                    self.data = new_data
                    self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[更新成功] 获取 {len(new_data)} 只股票行情, 时间: {self.last_update}")
                return True
            else:
                print("[更新失败] 未获取到数据")
        except Exception as e:
            print(f"更新数据异常: {e}")
        return False

    def _background_loop(self):
        while self.is_running:
            self.update_data()
            time.sleep(self.refresh_interval)

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._background_loop, daemon=True)
        self.thread.start()
        # 立即执行一次
        self.update_data()
        print("后台数据采集服务已启动")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)

    def get_snapshot(self):
        with self._lock:
            return {
                "data": list(self.data),
                "last_update": self.last_update,
                "count": len(self.data),
            }


if __name__ == "__main__":
    hub = RealtimeDataHub(refresh_interval=5)
    hub.start()
    time.sleep(8)
    snap = hub.get_snapshot()
    print(f"\n=== 实时行情快照 ({snap['count']} 只) ===")
    print(f"更新时间: {snap['last_update']}")
    for item in snap["data"][:8]:
        print(f"  {item['stock_name']}({item['stock_code']}): {item['price']}元  涨跌幅 {item['change_percent']:+.2f}%")
    hub.stop()
