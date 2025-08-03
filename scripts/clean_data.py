"""
清洗抓取后的原始价格数据
"""

import pandas as pd

def clean_price_data(filepath):
    df = pd.read_csv(filepath)
    df = df.dropna()
    df = df[df['price'] > 100]
    return df

if __name__ == "__main__":
    cleaned = clean_price_data("data/raw_prices.csv")
    cleaned.to_csv("data/cleaned_prices.csv", index=False)
