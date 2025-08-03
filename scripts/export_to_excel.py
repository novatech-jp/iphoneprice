"""
将分析结果导出为 Excel 报表
"""

import pandas as pd

def export():
    df = pd.read_csv("data/cleaned_prices.csv")
    df.to_excel("outputs/price_report.xlsx", index=False)
    print("导出完成")

if __name__ == "__main__":
    export()
