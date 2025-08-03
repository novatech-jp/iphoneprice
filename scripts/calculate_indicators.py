"""
计算价格统计指标（平均值、标准差、涨跌幅）
"""

import pandas as pd

def compute_metrics(file):
    df = pd.read_csv(file)
    result = {
        "mean": df['price'].mean(),
        "std": df['price'].std(),
        "min": df['price'].min(),
        "max": df['price'].max()
    }
    print(result)
    return result

if __name__ == "__main__":
    compute_metrics("data/cleaned_prices.csv")
