"""
农业股票数据处理模块
包含：数据清洗、统计分析、LSTM价格预测（可选）
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

class DataCleaner:
    """数据清洗器：剔除缺失值和异常值"""
    
    @staticmethod
    def clean_data(data):
        """清洗股票数据"""
        df = pd.DataFrame(data)
        
        # 删除缺失值
        initial_count = len(df)
        df = df.dropna(subset=['price', 'volume', 'amount', 'change_percent'])
        missing_removed = initial_count - len(df)
        
        # 删除异常值：收盘价<=0
        df = df[df['price'] > 0]
        price_removed = initial_count - len(df) - missing_removed
        
        # 删除异常值：成交量<=0
        df = df[df['volume'] > 0]
        volume_removed = initial_count - len(df) - missing_removed - price_removed
        
        # 3σ原则处理极端价格波动
        if len(df) > 3:
            price_mean = df['change_percent'].mean()
            price_std = df['change_percent'].std()
            lower_bound = price_mean - 3 * price_std
            upper_bound = price_mean + 3 * price_std
            df = df[(df['change_percent'] >= lower_bound) & (df['change_percent'] <= upper_bound)]
            sigma_removed = initial_count - len(df) - missing_removed - price_removed - volume_removed
        else:
            sigma_removed = 0
        
        print(f"数据清洗完成: 原始{initial_count}条 -> 清洗后{len(df)}条")
        print(f"  - 删除缺失值: {missing_removed}条")
        print(f"  - 删除无效价格: {price_removed}条")
        print(f"  - 删除无效成交量: {volume_removed}条")
        print(f"  - 3σ过滤极端值: {sigma_removed}条")
        
        return df.to_dict('records')


class StockAnalyzer:
    """股票数据分析器：统计分析功能"""
    
    @staticmethod
    def daily_statistics(data, date=None):
        """计算每日统计指标"""
        if not data:
            return {}
            
        df = pd.DataFrame(data)
        
        stats = {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'total_stocks': len(df),
            'avg_close_price': round(df['price'].mean(), 2),
            'total_volume': int(df['volume'].sum()),
            'total_amount': round(df['amount'].sum(), 2),
            'avg_change_percent': round(df['change_percent'].mean(), 2),
            'max_price': round(df['price'].max(), 2),
            'min_price': round(df['price'].min(), 2),
            'max_high': round(df['high'].max(), 2),
            'min_low': round(df['low'].min(), 2),
            'up_count': len(df[df['change_percent'] > 0]),
            'down_count': len(df[df['change_percent'] < 0]),
            'flat_count': len(df[df['change_percent'] == 0]),
            'top_growth_stock': df.loc[df['change_percent'].idxmax()]['stock_name'] if len(df) > 0 else None,
            'top_growth_value': round(df['change_percent'].max(), 2) if len(df) > 0 else 0,
            'bottom_growth_stock': df.loc[df['change_percent'].idxmin()]['stock_name'] if len(df) > 0 else None,
            'bottom_growth_value': round(df['change_percent'].min(), 2) if len(df) > 0 else 0,
        }
        
        return stats
    
    @staticmethod
    def sector_analysis(data):
        """按行业分类统计"""
        if not data:
            return []
            
        df = pd.DataFrame(data)
        if 'market' not in df.columns:
            return []
            
        result = []
        markets = df['market'].unique()
        
        for market_code in markets:
            market_df = df[df['market'] == market_code]
            result.append({
                'sector': '深市' if market_code == 'sz' else '沪市',
                'market_code': market_code,
                'stock_count': len(market_df),
                'avg_price': round(market_df['price'].mean(), 2),
                'max_price': round(market_df['price'].max(), 2),
                'min_price': round(market_df['price'].min(), 2),
                'avg_change': round(market_df['change_percent'].mean(), 2),
                'max_change': round(market_df['change_percent'].max(), 2),
                'min_change': round(market_df['change_percent'].min(), 2),
                'total_volume': int(market_df['volume'].sum()),
                'total_amount': round(market_df['amount'].sum(), 2),
                'total_market_cap': round(market_df['market_cap'].sum(), 2),
            })
        
        return result


class LSTMPredictor:
    """LSTM价格预测器（可选）"""
    
    def __init__(self, time_steps=60, epochs=50, batch_size=32):
        self.time_steps = time_steps
        self.epochs = epochs
        self.batch_size = batch_size
        self.models = {}
        self.scalers = {}
        self.tensorflow_available = False
        
        try:
            import tensorflow
            from sklearn.preprocessing import MinMaxScaler
            self.tensorflow_available = True
            print("LSTM预测器: TensorFlow可用")
        except ImportError:
            print("LSTM预测器: TensorFlow不可用，预测功能将被禁用")
    
    def _create_model(self, input_shape):
        """创建LSTM模型"""
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model
    
    def _scale_data(self, data):
        """标准化数据"""
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data.reshape(-1, 1))
        return scaled_data, scaler
    
    def _create_sequences(self, data):
        """创建时间序列数据"""
        X, y = [], []
        for i in range(self.time_steps, len(data)):
            X.append(data[i-self.time_steps:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)
    
    def train(self, stock_code, price_data):
        """训练LSTM模型"""
        if not self.tensorflow_available:
            return False, "TensorFlow不可用"
            
        try:
            if len(price_data) < self.time_steps + 1:
                return False, f"数据不足，需要至少{self.time_steps+1}条数据"
            
            scaled_data, scaler = self._scale_data(np.array(price_data))
            self.scalers[stock_code] = scaler
            
            X, y = self._create_sequences(scaled_data)
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))
            
            model = self._create_model((X.shape[1], 1))
            model.fit(X, y, epochs=self.epochs, batch_size=self.batch_size, verbose=0)
            self.models[stock_code] = model
            
            return True, f"模型训练成功，使用{len(price_data)}条数据"
            
        except Exception as e:
            return False, f"训练失败: {str(e)}"
    
    def predict(self, stock_code, price_data, days=5):
        """预测未来N天价格"""
        if not self.tensorflow_available:
            return None, "TensorFlow不可用"
        
        try:
            if stock_code not in self.models or stock_code not in self.scalers:
                return None, "模型未训练"
            
            model = self.models[stock_code]
            scaler = self.scalers[stock_code]
            
            last_data = np.array(price_data[-self.time_steps:])
            scaled_data = scaler.transform(last_data.reshape(-1, 1))
            
            predictions = []
            current_sequence = scaled_data[-self.time_steps:]
            
            for _ in range(days):
                input_seq = np.reshape(current_sequence, (1, self.time_steps, 1))
                pred = model.predict(input_seq, verbose=0)
                predictions.append(pred[0][0])
                current_sequence = np.append(current_sequence[1:], pred[0])
            
            predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))
            
            base_date = datetime.now()
            dates = [(base_date + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(days)]
            
            result = [{
                'date': dates[i],
                'predicted_price': round(float(predictions[i][0]), 2),
                'confidence': self._calculate_confidence(price_data)
            } for i in range(days)]
            
            return result, None
            
        except Exception as e:
            return None, f"预测失败: {str(e)}"
    
    def _calculate_confidence(self, price_data):
        """计算预测置信度"""
        if len(price_data) < 10:
            return 0.5
        
        returns = np.diff(price_data) / price_data[:-1]
        volatility = np.std(returns)
        
        confidence = max(0.3, min(0.95, 1 - volatility * 5))
        return round(confidence, 2)


class SimplePredictor:
    """简单预测器（当TensorFlow不可用时使用）"""
    
    @staticmethod
    def predict(price_data, days=5):
        """基于趋势和随机因子的预测"""
        import random
        if len(price_data) < 2:
            return None, "数据不足"
        
        try:
            last_price = price_data[-1]
            
            if len(price_data) >= 3:
                recent_prices = np.array(price_data[-3:])
                changes = np.diff(recent_prices)
                avg_change = changes.mean()
                trend_factor = avg_change / last_price if last_price != 0 else 0
            else:
                trend_factor = random.uniform(-0.01, 0.01)
            
            predictions = []
            base_date = datetime.now()
            current_price = last_price
            
            for i in range(days):
                noise = random.uniform(-0.01, 0.01)
                current_price = current_price * (1 + trend_factor + noise)
                predictions.append({
                    'date': (base_date + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                    'predicted_price': round(max(current_price, 0.01), 2),
                    'confidence': round(max(0.3, min(0.7, 0.5 + trend_factor * 10 + random.uniform(-0.1, 0.1))), 2)
                })
            
            return predictions, None
        except Exception as e:
            return None, f"预测失败: {str(e)}"


class DataProcessor:
    """数据处理器：整合清洗、分析、预测"""
    
    def __init__(self):
        self.cleaner = DataCleaner()
        self.analyzer = StockAnalyzer()
        self.predictor = LSTMPredictor()
        self.simple_predictor = SimplePredictor()
        self.historical_data = {}
    
    def process_realtime_data(self, realtime_data):
        """处理实时数据：清洗 + 分析"""
        cleaned_data = self.cleaner.clean_data(realtime_data)
        
        for item in cleaned_data:
            code = item['stock_code']
            if code not in self.historical_data:
                self.historical_data[code] = []
            self.historical_data[code].append({
                'price': item['price'],
                'timestamp': item['timestamp']
            })
            if len(self.historical_data[code]) > 200:
                self.historical_data[code] = self.historical_data[code][-200:]
        
        daily_stats = self.analyzer.daily_statistics(cleaned_data)
        sector_stats = self.analyzer.sector_analysis(cleaned_data)
        
        return {
            'cleaned_data': cleaned_data,
            'daily_stats': daily_stats,
            'sector_stats': sector_stats,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def train_models(self):
        """训练所有股票的预测模型"""
        results = []
        for code, history in self.historical_data.items():
            prices = [item['price'] for item in history]
            success, message = self.predictor.train(code, prices)
            results.append({
                'stock_code': code,
                'success': success,
                'message': message,
                'data_points': len(prices)
            })
        return results
    
    def generate_predictions(self, days=5):
        """生成所有股票的预测"""
        predictions = []
        use_simple = not self.predictor.tensorflow_available
        
        for code, history in self.historical_data.items():
            prices = [item['price'] for item in history]
            
            if use_simple:
                pred, error = self.simple_predictor.predict(prices, days)
            else:
                pred, error = self.predictor.predict(code, prices, days)
            
            if pred:
                predictions.append({
                    'stock_code': code,
                    'stock_name': self._get_stock_name(code),
                    'predictions': pred,
                    'current_price': prices[-1] if prices else None,
                    'predictor_type': 'simple' if use_simple else 'lstm'
                })
        return predictions
    
    def _get_stock_name(self, code):
        """获取股票名称"""
        from data_collector.realtime_hub import TencentStockCollector
        stocks = TencentStockCollector.AGRICULTURAL_STOCKS
        stock = next((s for s in stocks if s['code'] == code), None)
        return stock['name'] if stock else code


if __name__ == "__main__":
    from data_collector.realtime_hub import TencentStockCollector
    
    print("=" * 60)
    print("数据处理模块测试")
    print("=" * 60)
    
    collector = TencentStockCollector()
    data = collector.fetch_quotes()
    print(f"原始数据: {len(data)} 条")
    
    processor = DataProcessor()
    result = processor.process_realtime_data(data)
    print(f"\n清洗后数据: {len(result['cleaned_data'])} 条")
    
    print("\n每日统计:")
    for k, v in result['daily_stats'].items():
        print(f"  {k}: {v}")
    
    print("\n训练模型...")
    train_results = processor.train_models()
    for r in train_results[:3]:
        print(f"  {r['stock_code']}: {r['message']}")
    
    print("\n生成预测...")
    predictions = processor.generate_predictions(days=3)
    for pred in predictions[:3]:
        print(f"\n  {pred['stock_name']}({pred['stock_code']}):")
        print(f"    当前价格: {pred['current_price']}")
        print(f"    预测类型: {pred.get('predictor_type', 'lstm')}")
        for p in pred['predictions']:
            print(f"    {p['date']}: {p['predicted_price']} (置信度: {p['confidence']*100}%)")

