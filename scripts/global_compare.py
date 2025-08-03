"""
不同国家/地区价格对比分析
"""

import pandas as pd

def compare_global_prices():
    df = pd.read_csv("data/global_prices.csv")
    summary = df.groupby("country")["price"].mean().sort_values()
    print(summary)

if __name__ == "__main__":
    compare_global_prices()
