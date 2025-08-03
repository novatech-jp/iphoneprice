"""
专注日本市场，分析iPhone销售走势与定价行为
"""

import pandas as pd

def analyze_japan():
    df = pd.read_csv("data/japan_prices.csv")
    print(df.describe())

if __name__ == "__main__":
    analyze_japan()
