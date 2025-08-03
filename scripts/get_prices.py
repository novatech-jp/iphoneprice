"""
获取 iPhone 不同来源价格的脚本，可自定义 URL，并写入 SQLite 数据库。
"""

import requests
import sqlite3
from datetime import datetime

def fetch_price(url):
    # 模拟抓取
    print(f"Fetching price from: {url}")
    return {"model": "iPhone 14", "price": 999, "timestamp": datetime.utcnow()}

def save_to_db(data):
    conn = sqlite3.connect("data/iphone_prices.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prices (model TEXT, price REAL, timestamp TEXT)''')
    c.execute("INSERT INTO prices VALUES (?, ?, ?)", (data["model"], data["price"], data["timestamp"]))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    urls = ["https://example.com/iphone1", "https://example.com/iphone2"]
    for url in urls:
        data = fetch_price(url)
        save_to_db(data)
