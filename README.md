# 农业类上市公司行情监控平台

基于 Python Flask + ECharts 构建的农业类上市公司实时行情监控与预测系统。

## 功能特性

- **实时行情监控**：从腾讯财经接口实时采集16只农业类股票行情数据
- **数据清洗分析**：支持缺失值处理、异常值过滤（3σ原则）、统计分析
- **LSTM价格预测**：基于深度学习模型的股票价格趋势预测
- **数据可视化**：ECharts图表展示涨幅TOP10、市值TOP10等
- **MySQL持久化**：支持数据存储、多维度查询、数据备份
- **WebSocket推送**：实时数据推送至前端，低延迟更新

## 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Flask | 2.0+ |
| 实时通信 | Flask-SocketIO | 5.0+ |
| 数据库 | MySQL | 5.7+ |
| 数据处理 | Pandas / NumPy | 1.0+ |
| 可视化 | ECharts | 5.4+ |
| 爬虫 | Requests | 2.20+ |

## 项目结构

```
├── config.py                    # 配置管理
├── README.md                    # 项目说明文档
├── create_spider.py             # 爬虫文件生成器
├── get_history.py               # 历史数据采集脚本
├── make_spider.py               # 东方财富爬虫实现
├── test_mysql.py                # MySQL连接测试
├── test_predict.py              # 预测算法测试
├── visualization/
│   ├── app.py                   # Flask Web应用主入口
│   └── templates/
│       └── index.html           # 前端可视化页面
├── data_collector/
│   ├── __init__.py
│   ├── realtime_hub.py          # 实时数据采集中心（腾讯财经）
│   └── spider.py                # 东方财富爬虫（备用）
├── data_processor/
│   ├── data_processor.py        # 数据处理与预测模块
│   └── spark_analysis.py        # Spark分析模块
└── data_storage/
    └── mysql_storage.py         # MySQL数据库存储模块
```

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- 依赖包：见 `requirements.txt`

### 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install flask flask-socketio flask-cors requests pymysql dbutils pandas numpy
```

### 数据库配置

1. 创建数据库：
```sql
CREATE DATABASE agricultural_stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 修改配置文件 `config.py`：
```python
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DATABASE = 'agricultural_stock'
```

### 启动服务

```bash
cd visualization
python app.py
```

访问地址：http://localhost:5000

## API接口

### 实时行情接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/stocks` | GET | 获取所有股票实时行情 |
| `/api/top_growth` | GET | 获取涨幅TOP10股票 |
| `/api/top_market_cap` | GET | 获取市值TOP10股票 |
| `/api/stats` | GET | 获取市场统计数据 |

### 预测接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/predict` | GET | 获取所有股票预测数据 |
| `/api/predict/<stock_code>` | GET | 获取单只股票预测 |

### 查询接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/query/date` | GET | 按日期查询 |
| `/api/query/company` | GET | 按公司名称查询 |
| `/api/query/history` | GET | 查询股票历史行情 |
| `/api/query/stock_list` | GET | 获取股票列表 |
| `/api/query/stats` | GET | 获取统计数据 |

### 示例请求

```bash
# 获取实时行情
curl http://localhost:5000/api/stocks

# 获取涨幅TOP10
curl http://localhost:5000/api/top_growth

# 获取单只股票预测（顺鑫农业）
curl http://localhost:5000/api/predict/000860

# 查询历史数据
curl "http://localhost:5000/api/query/history?stock_code=000860&start_date=2026-06-01&end_date=2026-06-18"
```

## 监控股票列表

| 股票代码 | 股票名称 | 市场 |
|---------|---------|------|
| 000860 | 顺鑫农业 | 深市 |
| 002041 | 登海种业 | 深市 |
| 002299 | 圣农发展 | 深市 |
| 002385 | 大北农 | 深市 |
| 000998 | 隆平高科 | 深市 |
| 600598 | 北大荒 | 沪市 |
| 600354 | 敦煌种业 | 沪市 |
| 600108 | 亚盛集团 | 沪市 |
| 600127 | 金健米业 | 沪市 |
| 000061 | 农产品 | 深市 |
| 600540 | 新赛股份 | 沪市 |
| 600962 | 国投中鲁 | 沪市 |
| 000876 | 新希望 | 深市 |
| 002714 | 牧原股份 | 深市 |
| 300498 | 温氏股份 | 深市 |
| 002311 | 海大集团 | 深市 |

## 数据存储结构

### 数据库表

| 表名 | 功能 |
|------|------|
| `stock_company_info` | 股票基础信息 |
| `stock_daily_quote` | 日行情数据 |
| `stock_realtime` | 实时行情快照 |
| `stock_prediction` | 预测数据 |
| `daily_statistics` | 每日统计数据 |

## 核心模块说明

### 1. 数据采集模块 (`data_collector/`)

- **RealtimeDataHub**：定时从腾讯财经拉取实时行情数据
- **TencentStockCollector**：解析腾讯接口返回的数据格式

### 2. 数据处理模块 (`data_processor/`)

- **DataCleaner**：数据清洗（缺失值、异常值处理）
- **StockAnalyzer**：统计分析（涨跌幅、成交量等）
- **LSTMPredictor**：LSTM深度学习预测器
- **SimplePredictor**：简单趋势预测器（备用）

### 3. 数据存储模块 (`data_storage/`)

- **MySQLStorage**：数据库连接池、数据CRUD操作、数据备份

### 4. 可视化模块 (`visualization/`)

- **Flask应用**：RESTful API、WebSocket实时推送
- **前端页面**：ECharts图表、响应式布局

## 配置说明

配置文件 `config.py` 支持以下环境变量：

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `MYSQL_HOST` | localhost | 数据库主机 |
| `MYSQL_PORT` | 3306 | 数据库端口 |
| `MYSQL_USER` | root | 数据库用户名 |
| `MYSQL_PASSWORD` | 123456 | 数据库密码 |
| `MYSQL_DATABASE` | agricultural_stock | 数据库名 |
| `REFRESH_INTERVAL` | 5 | 数据刷新间隔（秒） |
| `SECRET_KEY` | agricultural_stock_monitor | 应用密钥 |

## 运行测试

```bash
# 测试MySQL连接
python test_mysql.py

# 测试预测算法
python test_predict.py

# 测试数据采集
python -m data_collector.realtime_hub
```

## 安全注意事项

1. **生产环境**：设置 `DEBUG = False`
2. **数据库密码**：使用强密码，通过环境变量配置
3. **CORS配置**：限制允许访问的域名
4. **SECRET_KEY**：使用至少32位的随机字符串

## License

MIT License

## 数据来源

数据来源于腾讯财经公开接口，仅供学习研究使用。投资有风险，预测结果仅供参考，不构成投资建议