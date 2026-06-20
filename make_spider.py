import requests
import json
import time
import random
from datetime import datetime
import os
import pandas as pd

class EastMoneyCollector:
    AGRICULTURAL_STOCKS = [
        {"code": "000860", "market": "sz", "name": "顺鑫农业", "secid": "0.000860"},
        {"code": "002041", "market": "sz", "name": "登海种业", "secid": "0.002041"},
        {"code": "002299", "market": "sz", "name": "圣农发展", "secid": "0.002299"},
        {"code": "002385", "market": "sz", "name": "大北农", "secid": "0.002385"},
        {"code": "000998", "market": "sz", "name": "隆平高科", "secid": "0.000998"},
        {"code": "600598", "market": "sh", "name": "北大荒", "secid": "1.600598"},
        {"code": "600354", "market": "sh", "name": "敦煌种业", "secid": "1.600354"},
        {"code": "600108", "market": "sh", "name": "亚盛集团", "secid": "1.600108"},
        {"code": "600127", "market": "sh", "name": "金健米业", "secid": "1.600127"},
        {"code": "000061", "market": "sz", "name": "农产品", "secid": "0.000061"},
        {"code": "600540", "market": "sh", "name": "新赛股份", "secid": "1.600540"},
        {"code": "600962", "market": "sh", "name": "国投中鲁", "secid": "1.600962"},
    ]

    def __init__(self):
        self.session = requests.Session()

    def get_realtime_quote(self, secid):
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {"secid": secid, "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170,f171,f173,f191,f192"}
        try:
            resp = self.session.get(url, params=params, timeout=10)
            return resp.json().get("data", {})
        except:
            return {}

    def get_all_realtime(self):
        results = []
        for stock in self.AGRICULTURAL_STOCKS:
            data = self.get_realtime_quote(stock["secid"])
            if data:
                price = data.get("f43", 0) / 100 if data.get("f43") else 0
                if price > 0:
                    results.append({"stock_code": stock["code"], "stock_name": stock["name"], "price": round(price, 2)})
            time.sleep(random.uniform(0.3, 0.8))
        return results