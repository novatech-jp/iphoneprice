"""
使用简单机器学习模型预测价格趋势
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def forecast(filepath):
    df = pd.read_csv(filepath)
    df['day'] = np.arange(len(df))
    model = LinearRegression()
    model.fit(df[['day']], df['price'])
    pred = model.predict([[len(df) + 1]])
    print(f"Tomorrow's prediction: {pred[0]}")
    return pred[0]

if __name__ == "__main__":
    forecast("data/cleaned_prices.csv")
