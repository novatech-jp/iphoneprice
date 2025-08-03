"""
可视化价格走势
"""

import pandas as pd
import matplotlib.pyplot as plt

def plot_prices(file):
    df = pd.read_csv(file)
    df.plot(x="date", y="price", title="Price Trend")
    plt.savefig("outputs/price_trend.png")

if __name__ == "__main__":
    plot_prices("data/cleaned_prices.csv")
