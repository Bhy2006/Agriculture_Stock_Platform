"""
配置文件：农业类上市公司行情监控平台
"""
import os

class Config:
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'agricultural_stock_monitor')
    
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '123456')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'agricultural_stock')
    MYSQL_POOL_SIZE = int(os.environ.get('MYSQL_POOL_SIZE', 10))
    
    REFRESH_INTERVAL = int(os.environ.get('REFRESH_INTERVAL', 5))
    
    PREDICTION_TRAIN_INTERVAL = int(os.environ.get('PREDICTION_TRAIN_INTERVAL', 300))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}