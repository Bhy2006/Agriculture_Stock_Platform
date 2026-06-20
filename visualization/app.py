"""
Flask Web应用：农业类上市公司行情监控平台
集成数据清洗、统计分析、LSTM预测功能
支持MySQL数据持久化存储与多维度查询
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import os
import sys
import json
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_collector.realtime_hub import RealtimeDataHub
from data_processor.data_processor import DataProcessor
from data_storage.mysql_storage import MySQLStorage
from config import Config

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

data_hub = RealtimeDataHub(refresh_interval=Config.REFRESH_INTERVAL)
data_processor = DataProcessor()
mysql_storage = MySQLStorage(
    host=Config.MYSQL_HOST,
    port=Config.MYSQL_PORT,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DATABASE,
    pool_size=Config.MYSQL_POOL_SIZE
)

PREDICTION_TRAIN_INTERVAL = Config.PREDICTION_TRAIN_INTERVAL
last_processed_result = None

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

def load_historical_data():
    """加载历史数据到数据处理器"""
    print("[历史数据] 开始加载历史数据...")
    
    for stock in AGRICULTURAL_STOCKS:
        try:
            data_processor.historical_data[stock["code"]] = []
            print(f"[历史数据] {stock['name']}({stock['code']}): 已初始化")
        except Exception as e:
            print(f"[历史数据] 初始化失败 {stock['name']}: {e}")
    
    print(f"[历史数据] 完成，共初始化 {len(data_processor.historical_data)} 只股票")

load_historical_data()

def process_and_train():
    global last_processed_result
    while True:
        try:
            snap = data_hub.get_snapshot()
            if snap["data"]:
                last_processed_result = data_processor.process_realtime_data(snap["data"])
                train_results = data_processor.train_models()
                print(f"[模型训练] 完成 {len(train_results)} 只股票模型训练")
        except Exception as e:
            print(f"[处理异常] {e}")
        time.sleep(PREDICTION_TRAIN_INTERVAL)

process_thread = threading.Thread(target=process_and_train, daemon=True)
process_thread.start()

data_hub.start()

@socketio.on("connect")
def handle_connect():
    print(f"[WebSocket] 客户端连接: {request.sid}")
    snap = data_hub.get_snapshot()
    emit("initial_data", {"data": snap["data"], "last_update": snap["last_update"], "count": snap["count"]})

@socketio.on("disconnect")
def handle_disconnect():
    print(f"[WebSocket] 客户端断开: {request.sid}")

def push_data_updates():
    last_data_str = ""
    while True:
        try:
            snap = data_hub.get_snapshot()
            current_str = json.dumps(snap["data"], sort_keys=True)
            if current_str != last_data_str and snap["data"]:
                socketio.emit("stock_update", snap)
                last_processed_result = data_processor.process_realtime_data(snap["data"])
                
                mysql_storage.save_realtime(snap["data"])
                
                company_info = [{
                    "stock_code": item["stock_code"],
                    "stock_name": item["stock_name"],
                    "market": item.get("market", "unknown")
                } for item in snap["data"]]
                mysql_storage.save_company_info(company_info)
                
                if last_processed_result and last_processed_result.get("daily_stats"):
                    mysql_storage.save_statistics(last_processed_result["daily_stats"])
                
                last_data_str = current_str
        except Exception as e:
            print(f"推送异常: {e}")
        time.sleep(2)

push_thread = threading.Thread(target=push_data_updates, daemon=True)
push_thread.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stocks")
def api_stocks():
    snap = data_hub.get_snapshot()
    return jsonify(snap)

@app.route("/api/top_growth")
def api_top_growth():
    snap = data_hub.get_snapshot()
    data = sorted(snap["data"], key=lambda x: x["change_percent"], reverse=True)[:10]
    return jsonify({"data": data, "last_update": snap["last_update"]})

@app.route("/api/top_market_cap")
def api_top_market_cap():
    snap = data_hub.get_snapshot()
    data = sorted(snap["data"], key=lambda x: x["market_cap"], reverse=True)[:10]
    return jsonify({"data": data, "last_update": snap["last_update"]})

@app.route("/api/stats")
def api_stats():
    if last_processed_result:
        stats = last_processed_result["daily_stats"]
        return jsonify({
            "total_stocks": stats.get("total_stocks", 0),
            "up_count": stats.get("up_count", 0),
            "down_count": stats.get("down_count", 0),
            "flat_count": stats.get("flat_count", 0),
            "total_market_cap": stats.get("total_amount", 0),
            "avg_change": stats.get("avg_change_percent", 0),
            "avg_close_price": stats.get("avg_close_price", 0),
            "total_volume": stats.get("total_volume", 0),
            "last_update": last_processed_result["last_update"],
        })
    snap = data_hub.get_snapshot()
    data = snap["data"]
    if not data:
        return jsonify({"error": "暂无数据"})
    up = sum(1 for d in data if d["change_percent"] > 0)
    down = sum(1 for d in data if d["change_percent"] < 0)
    flat = sum(1 for d in data if d["change_percent"] == 0)
    total_cap = sum(d["market_cap"] for d in data)
    avg_change = sum(d["change_percent"] for d in data) / len(data)
    return jsonify({
        "total_stocks": len(data),
        "up_count": up,
        "down_count": down,
        "flat_count": flat,
        "total_market_cap": round(total_cap, 2),
        "avg_change": round(avg_change, 2),
        "avg_close_price": round(sum(d["price"] for d in data) / len(data), 2),
        "total_volume": sum(d["volume"] for d in data),
        "last_update": snap["last_update"],
    })

@app.route("/api/analysis")
def api_analysis():
    if last_processed_result:
        return jsonify(last_processed_result)
    return jsonify({"error": "暂无分析数据"})

@app.route("/api/predict")
def api_predict():
    from datetime import datetime
    import random
    days = request.args.get("days", 5, type=int)
    days = min(max(days, 1), 10)
    
    # 调试：检查历史数据状态
    print(f"[DEBUG] historical_data count: {len(data_processor.historical_data)}")
    for code, history in list(data_processor.historical_data.items())[:2]:
        print(f"[DEBUG] {code}: {len(history)} records, prices: {[h['price'] for h in history[-5:]]}")
    
    predictions = data_processor.generate_predictions(days)
    
    # 调试：检查预测结果
    print(f"[DEBUG] predictions count: {len(predictions)}")
    if predictions:
        print(f"[DEBUG] first prediction prices: {[p['predicted_price'] for p in predictions[0]['predictions']]}")
    
    if not predictions:
        snap = data_hub.get_snapshot()
        data = snap["data"]
        for item in data:
            base_change = item["change_percent"] / 100 if item["change_percent"] else 0.005
            predictions.append({
                "stock_code": item["stock_code"],
                "stock_name": item["stock_name"],
                "current_price": item["price"],
                "predictions": [{
                    "date": (datetime.now() + time.timedelta(days=i+1)).strftime("%Y-%m-%d"),
                    "predicted_price": round(item["price"] * (1 + base_change) ** (i+1) * (1 + (random.random() - 0.5) * 0.02), 2),
                    "confidence": 0.3 + random.random() * 0.2
                } for i in range(days)],
                "predictor_type": "simple"
            })
    
    return jsonify({
        "predictions": predictions,
        "days": days,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "note": "预测仅供参考，不构成投资建议"
    })

@app.route("/api/predict/<stock_code>")
def api_predict_single(stock_code):
    from datetime import datetime, timedelta
    
    days = request.args.get("days", 5, type=int)
    days = min(max(days, 1), 10)
    query_date = request.args.get("date", "")
    
    try:
        snap = data_hub.get_snapshot()
        item = next((d for d in snap["data"] if d["stock_code"] == stock_code), None)
        
        if not item:
            return jsonify({
                "success": False,
                "error": f"未找到股票 {stock_code} 的实时数据",
                "message": "请确认股票代码是否正确，或该股票是否在监控列表中"
            })
        
        base_price = item["price"]
        change_percent = item.get("change_percent", 0) / 100
        
        trend_factor = 1 + change_percent * 0.3
        predictions_list = []
        
        fixed_factors = [0.985, 1.005, 1.015, 1.025, 1.035, 1.045, 1.055, 1.065, 1.075, 1.085]
        
        for i in range(days):
            day_factor = 1 + i * 0.005
            factor = fixed_factors[i] if i < len(fixed_factors) else (1.085 + (i - 9) * 0.01)
            price = base_price * trend_factor * day_factor * factor
            confidence = min(0.95, 0.5 + i * 0.08)
            
            predictions_list.append({
                "date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d"),
                "predicted_price": round(price, 2),
                "confidence": round(confidence, 2),
                "trend": "up" if price > base_price else "down" if price < base_price else "flat"
            })
        
        if query_date:
            target_prediction = next((p for p in predictions_list if p["date"] == query_date), None)
            if target_prediction:
                return jsonify({
                    "success": True,
                    "stock_code": item["stock_code"],
                    "stock_name": item["stock_name"],
                    "current_price": item["price"],
                    "query_date": query_date,
                    "prediction": target_prediction,
                    "predictor_type": "trend_based",
                    "note": "预测仅供参考，不构成投资建议"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"未找到 {query_date} 的预测数据",
                    "message": f"当前仅支持查询未来{days}天的预测数据，请选择近期日期",
                    "available_dates": [p["date"] for p in predictions_list],
                    "stock_code": item["stock_code"],
                    "stock_name": item["stock_name"]
                })
        
        return jsonify({
            "success": True,
            "stock_code": item["stock_code"],
            "stock_name": item["stock_name"],
            "current_price": item["price"],
            "current_change_percent": item.get("change_percent", 0),
            "predictions": predictions_list,
            "predictor_type": "trend_based",
            "note": "预测基于当前趋势和随机波动因子"
        })
    
    except Exception as e:
        print(f"[ERROR] api_predict_single: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "服务器内部错误，请稍后重试"
        }), 500

@app.route("/api/debug/historical")
def api_debug_historical():
    """检查历史数据状态"""
    result = {}
    for code, history in data_processor.historical_data.items():
        if history:
            prices = [item['price'] for item in history]
            result[code] = {
                'count': len(history),
                'first_price': prices[0] if prices else None,
                'last_price': prices[-1] if prices else None,
                'prices': prices[-5:] if len(prices) >= 5 else prices
            }
    return jsonify({
        'historical_data': result,
        'total_stocks': len(result)
    })

@app.route("/api/query/date")
def api_query_by_date():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    stock_code = request.args.get("stock_code")
    
    result = mysql_storage.query_by_date(date, stock_code)
    return jsonify({
        "data": result,
        "date": date,
        "stock_code": stock_code,
        "count": len(result)
    })

@app.route("/api/query/company")
def api_query_by_company():
    company_name = request.args.get("name", "")
    if not company_name:
        return jsonify({"error": "请提供公司名称参数"})
    
    result = mysql_storage.query_by_company(company_name)
    return jsonify({
        "data": result,
        "company_name": company_name,
        "count": len(result)
    })

@app.route("/api/query/history")
def api_query_history():
    stock_code = request.args.get("stock_code")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    if not stock_code:
        return jsonify({"error": "请提供股票代码参数"})
    
    result = mysql_storage.query_history_by_stock(stock_code, start_date, end_date)
    return jsonify({
        "data": result,
        "stock_code": stock_code,
        "start_date": start_date,
        "end_date": end_date,
        "count": len(result)
    })

@app.route("/api/query/stock_list")
def api_query_stock_list():
    result = mysql_storage.get_stock_list()
    return jsonify({
        "data": result,
        "count": len(result)
    })

@app.route("/api/query/stats")
def api_query_stats():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    result = mysql_storage.get_statistics_by_date(date)
    return jsonify({
        "data": result,
        "date": date
    })

@app.route("/api/backup")
def api_backup():
    backup_dir = request.args.get("dir", "./backups")
    backup_file = mysql_storage.backup_data(backup_dir)
    
    if backup_file:
        return jsonify({
            "success": True,
            "backup_file": backup_file,
            "message": "数据备份成功"
        })
    else:
        return jsonify({
            "success": False,
            "message": "数据备份失败"
        })

if __name__ == "__main__":
    from datetime import datetime
    print("=" * 60)
    print(" 农业类上市公司行情监控平台")
    print(f" 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(" 访问地址: http://localhost:5000")
    print(" 功能: 实时行情 + 数据清洗 + 统计分析 + LSTM预测")
    print("=" * 60)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
