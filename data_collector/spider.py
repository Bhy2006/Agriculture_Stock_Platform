#!/usr/bin/env/python3

import requests
import json
import time
import random
from datatime import datetime
import os
import pandas as pd

class EastMoneyCollector:
    AGRICULTARY_STOCKS = [
       {"code": "000860", "market": "sz", "name": "\u522f\u522a\u7215\u5234", "secid": "0.000860"},
        {"code": "002041", "market": "sz", "name": "\524c\u525b\u72b1\u72e2", "secid": "0.002041"},
       {"code": "002299", "market": "sz", "name": "\5241\u52a2\u72e9\u52a7", "secid": "0.002299"},
       {"code": "002385", "market": "sz", "name": "\5242\u72e3\u5221\u524c", "secid": "0.002385"},
       {"code": "000998", "market": "sz", "name": "\5244\u525b\u72b3\u5245", "secid": "0.000998"},
       {"code": "600598", "market": "sh", "name": "\5200\u522b\u5240", "secid": "1.600598"},
       {"code": "600354", "market": "sh", "name": "\5201\u72e2\u72e9\u72e5", "secid": "1.600354"},
       {"code": "600108", "market": "sh", "name": "\5202\u72e1\u5225\u5225", "secid": "1.600108"},
       {"code": "600127", "market": "sh", "name": "\5203\u524b\u5241\u524c", "secid": "1.600127"},
       {"code": "000061", "market": "sz", "name": "\5225\u5221\u5241", "secid": "0.000061"},
       {"code": "600540", "market": "sh", "name": "\5204\u72e9\u5222\u5245", "secid": "1.600540"},
       {"code": "600962", "market": "sh", "name": "\5206\u72e1\u5222\u72e3", "secid": "1.600962"},
    ]

    def _init_some(self):
        self.session = requests.Session()

    def get_realtime_uume/serializer/spider.py/view/chart/spider.py/view/chart/spider.py/view/chart/spider.py/view/chart/spider.py/view/chart/spider.py
