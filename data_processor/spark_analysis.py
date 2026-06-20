from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder \
    .appName("AgriculturalStockAnalysis") \
    .config("spark.sql.shuffle.partitions", "20") \
    .getOrCreate()

quote_df = spark.read.parquet("/data/agricultural/stock/daily_quote/*")
company_df = spark.read.parquet("/data/agricultural/stock/company_info/*")

valid_quote_df = quote_df.filter(
    (col("closing_price") > 0) &
    (col("trading_volume") > 0)
)

joined_df = valid_quote_df.join(
    company_df,
    on="stock_code",
    how="inner"
)

industry_daily_change = joined_df.groupBy(
    "industry", "trade_date"
).agg(
    avg("change_percent").alias("avg_change_percent"),
    sum("trading_amount").alias("total_trading_amount")
)

window_spec = Window.partitionBy("stock_code").orderBy("trade_date")
price_change_df = joined_df.withColumn(
    "prev_close", lag("closing_price", 1).over(window_spec)
).withColumn(
    "is_up", when(col("closing_price") > col("prev_close"), 1).otherwise(0)
)

consecutive_up_days = price_change_df.withColumn(
    "grp", col("trade_date").cast("long") - row_number().over(window_spec)
).groupBy("stock_code", "grp").agg(
    max("is_up").alias("max_consecutive_up")
).groupBy("stock_code").agg(
    max("max_consecutive_up").alias("max_up_days")
)

top_stocks = joined_df.groupBy("industry", "stock_code").agg(
    avg("change_percent").alias("avg_change"),
    sum("trading_volume").alias("total_volume")
)

window_spec_top = Window.partitionBy("industry").orderBy(desc("avg_change"))
top3_stocks = top_stocks.withColumn(
    "rank", rank().over(window_spec_top)
).filter(col("rank") <= 3)

industry_daily_change.write.parquet(
    "/output/agricultural/industry_daily_change",
    mode="overwrite"
)

consecutive_up_days.write.parquet(
    "/output/agricultural/consecutive_up_days",
    mode="overwrite"
)

top3_stocks.write.parquet(
    "/output/agricultural/top3_stocks",
    mode="overwrite"
)

spark.stop()
