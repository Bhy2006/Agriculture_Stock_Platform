#!/bin/bash

# 上市公司信息表
hive -e "CREATE EXTERNAL TABLE IF NOT EXISTS stock_company_info (
    stock_code STRING COMMENT '股票代码',
    company_name STRING COMMENT '公司名称',
    industry STRING COMMENT '所属行业',
    sub_industry STRING COMMENT '细分行业',
    listing_date DATE COMMENT '上市日期',
    registered_address STRING COMMENT '注册地址',
    actual_controller STRING COMMENT '实际控制人'
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/data/agricultural/stock/company_info';"

# 股票日行情表
hive -e "CREATE EXTERNAL TABLE IF NOT EXISTS stock_daily_quote (
    stock_code STRING COMMENT '股票代码',
    trade_date DATE COMMENT '交易日期',
    opening_price DECIMAL(10,2) COMMENT '开盘价',
    closing_price DECIMAL(10,2) COMMENT '收盘价',
    highest_price DECIMAL(10,2) COMMENT '最高价',
    lowest_price DECIMAL(10,2) COMMENT '最低价',
    trading_volume BIGINT COMMENT '成交量(股)',
    trading_amount DECIMAL(10,2) COMMENT '成交额(元)',
    change_percent DECIMAL(10,4) COMMENT '涨跌幅',
    turnover_rate DECIMAL(10,4) COMMENT '换手率',
    pe_ratio DECIMAL(10,2) COMMENT '市盈率'
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/data/agricultural/stock/daily_quote';"

# 财务指标表
hive -e "CREATE EXTERNAL TABLE IF NOT EXISTS financial_indicators (
    stock_code STRING COMMENT '股票代码',
    report_period STRING COMMENT '报告期(季度/年度)',
    operating_revenue DECIMAL(10,2) COMMENT '营业收入(万元)',
    net_profit DECIMAL(10,2) COMMENT '净利润(万元)',
    eps DECIMAL(10,4) COMMENT '每股收益(元)',
    bps DECIMAL(10,4) COMMENT '每股净资产(元)',
    roe DECIMAL(10,4) COMMENT '净资产收益率',
    debt_ratio DECIMAL(10,4) COMMENT '资产负债率'
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/data/agricultural/stock/financial_indicators';"

# 行业指数表
hive -e "CREATE EXTERNAL TABLE IF NOT EXISTS industry_index (
    industry_code STRING COMMENT '行业代码',
    industry_name STRING COMMENT '行业名称',
    trade_date DATE COMMENT '交易日期',
    closing_index DECIMAL(10,2) COMMENT '收盘指数',
    change_percent DECIMAL(10,4) COMMENT '涨跌幅',
    trading_volume BIGINT COMMENT '成交量(手)',
    trading_amount DECIMAL(10,2) COMMENT '成交额(万元)'
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/data/agricultural/stock/industry_index';"

# 股东结构表
hive -e "CREATE EXTERNAL TABLE IF NOT EXISTS shareholder_structure (
    stock_code STRING COMMENT '股票代码',
    report_date DATE COMMENT '报告日期',
    shareholder_rank INT COMMENT '股东排名',
    shareholder_name STRING COMMENT '股东名称',
    shareholding_amount BIGINT COMMENT '持股数量(股)',
    shareholding_ratio DECIMAL(10,4) COMMENT '持股比例',
    shareholding_nature STRING COMMENT '股东性质'
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/data/agricultural/stock/shareholder_structure';"

echo "Hive tables created successfully"
