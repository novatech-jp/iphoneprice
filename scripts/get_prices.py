"""
复杂的多源 iPhone 价格抓取器，支持自定义网页和 API 源，
多格式解析，存入 SQLite 数据库，具有日志、校验、标准化处理等功能。
"""

import requests
import sqlite3
import logging
import random
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Union
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import threading
import json

# ---------------- 配置 ----------------
DB_PATH = "data/iphone_prices.db"
LOG_FILE = "logs/get_prices.log"

MAX_RETRIES = 3
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

DEFAULT_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9"
}

URLS = [
    "https://example.com/iphone14-pro-japan",
    "https://example.com/iphone14-pro-global",
    "https://example.com/api/price-feed?model=iphone13",
    "https://example.com/deals/iphone15"
]

# ---------------- 日志 ----------------
logging.basicConfig(filename=LOG_FILE,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    level=logging.INFO)

# ---------------- 抓取器 ----------------
class PageFetcher:
    def __init__(self, url: str):
        self.url = url
        self.session = requests.Session()

    def _headers(self):
        headers = DEFAULT_HEADERS.copy()
        headers["User-Agent"] = random.choice(USER_AGENTS)
        return headers

    def fetch(self) -> Optional[Union[str, dict]]:
        for attempt in range(MAX_RETRIES):
            try:
                if "/api/" in self.url or self.url.endswith(".json"):
                    resp = self.session.get(self.url, headers=self._headers(), timeout=10)
                    resp.raise_for_status()
                    return resp.json()
                else:
                    resp = self.session.get(self.url, headers=self._headers(), timeout=10)
                    resp.raise_for_status()
                    return resp.text
            except Exception as e:
                logging.warning(f"[{self.url}] 第 {attempt + 1} 次请求失败：{e}")
                time.sleep(random.uniform(1, 2))
        return None


# ---------------- 辅助函数 ----------------

def safe_float(text: str) -> Optional[float]:
    try:
        return float(
            re.sub(r"[^\d.]", "", text.replace(",", "").replace("¥", ""))
        )
    except Exception as e:
        logging.debug(f"safe_float 解析失败：{text} -> {e}")
        return None


def normalize_model_name(raw_name: str) -> str:
    raw_name = raw_name.lower().strip()
    patterns = [
        (r"iphone\s*15\s*pro\s*max", "iPhone 15 Pro Max"),
        (r"iphone\s*15\s*pro", "iPhone 15 Pro"),
        (r"iphone\s*15", "iPhone 15"),
        (r"iphone\s*14\s*pro\s*max", "iPhone 14 Pro Max"),
        (r"iphone\s*14\s*pro", "iPhone 14 Pro"),
        (r"iphone\s*14", "iPhone 14"),
        (r"iphone\s*13", "iPhone 13"),
        (r"iphone\s*12", "iPhone 12"),
        (r"iphone\s*11", "iPhone 11"),
    ]
    for pattern, name in patterns:
        if re.search(pattern, raw_name):
            return name
    return raw_name.title()


# ---------------- 价格解析器 ----------------

class PriceParser:
    def __init__(self, raw: Union[str, dict], url: str):
        self.raw = raw
        self.url = url
        self.parsed = None
        self.model = "Unknown"
        self.price = None

    def _parse_html(self, html: str):
        soup = BeautifulSoup(html, "html.parser")

        # 多个结构尝试（模拟兼容多个站点结构）
        candidates = [
            {"model": lambda s: s.find("h1"), "price": lambda s: s.find("span", class_="price")},
            {"model": lambda s: s.find("div", class_="product-title"), "price": lambda s: s.find("div", class_="product-price")},
            {"model": lambda s: s.select_one("meta[property='og:title']"), "price": lambda s: s.select_one("meta[itemprop='price']")},
        ]

        for c in candidates:
            try:
                model_tag = c["model"](soup)
                price_tag = c["price"](soup)

                if model_tag and price_tag:
                    model = model_tag.get("content") if model_tag.has_attr("content") else model_tag.get_text(strip=True)
                    price = price_tag.get("content") if price_tag.has_attr("content") else price_tag.get_text(strip=True)

                    model = normalize_model_name(model)
                    price = safe_float(price)

                    if model and price:
                        self.model = model
                        self.price = price
                        return
            except Exception as e:
                continue  # 尝试下一个结构

    def _parse_json(self, data: dict):
        try:
            model = data.get("model") or data.get("title") or "unknown"
            price = data.get("price") or data.get("value")

            model = normalize_model_name(model)
            price = safe_float(str(price))

            if model and price:
                self.model = model
                self.price = price
        except Exception as e:
            logging.warning(f"JSON解析失败: {self.url} -> {e}")

    def extract(self) -> Optional[Dict]:
        if isinstance(self.raw, str):
            self._parse_html(self.raw)
        elif isinstance(self.raw, dict):
            self._parse_json(self.raw)

        if self.price:
            return {
                "model": self.model,
                "price": self.price,
                "source_url": self.url,
                "timestamp": datetime.utcnow().isoformat()
            }

        logging.warning(f"提取失败: {self.url}")
        return None

# ---------------- 数据库存储 ----------------

class PriceDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_schema()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            logging.info(f"数据库连接成功：{self.db_path}")
        except Exception as e:
            logging.error(f"数据库连接失败：{e}")
            raise

    def _init_schema(self):
        try:
            query = """
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT,
                price REAL,
                source_url TEXT,
                timestamp TEXT,
                UNIQUE(model, price, source_url, timestamp)
            );
            """
            self.conn.execute(query)
            self.conn.commit()
            logging.info("数据库表结构初始化完成")
        except Exception as e:
            logging.error(f"数据库表初始化失败：{e}")
            raise

    def insert_price(self, record: Dict) -> bool:
        if not record:
            return False
        try:
            query = """
            INSERT OR IGNORE INTO prices (model, price, source_url, timestamp)
            VALUES (?, ?, ?, ?);
            """
            self.conn.execute(
                query,
                (
                    record["model"],
                    record["price"],
                    record["source_url"],
                    record["timestamp"],
                ),
            )
            self.conn.commit()
            logging.info(f"✅ 插入成功: {record['model']} - {record['price']}")
            return True
        except Exception as e:
            logging.error(f"❌ 插入失败: {e} | 数据: {record}")
            return False

    def fetch_latest(self, model: str) -> Optional[float]:
        try:
            query = """
            SELECT price FROM prices
            WHERE model = ?
            ORDER BY timestamp DESC
            LIMIT 1;
            """
            cursor = self.conn.execute(query, (model,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except Exception as e:
            logging.error(f"查询失败: {e}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()
            logging.info("数据库连接关闭")


# ---------------- 主执行流程 ----------------

def run_all():
    logging.info("🚀 启动抓取任务")

    db = PriceDatabase()

    success_count = 0
    fail_count = 0

    for idx, url in enumerate(URLS):
        logging.info(f"[{idx+1}/{len(URLS)}] 正在抓取: {url}")
        fetcher = PageFetcher(url)
        raw_data = fetcher.fetch()

        if not raw_data:
            logging.warning(f"⚠️ 跳过空内容: {url}")
            fail_count += 1
            continue

        parser = PriceParser(raw_data, url)
        result = parser.extract()

        if not result:
            logging.warning(f"⚠️ 解析失败: {url}")
            fail_count += 1
            continue

        inserted = db.insert_price(result)
        if inserted:
            success_count += 1
        else:
            fail_count += 1

        # 防止请求过快：1.5 到 3 秒之间的随机延迟
        sleep_duration = round(random.uniform(1.5, 3.0), 2)
        logging.info(f"等待 {sleep_duration} 秒以防封锁")
        time.sleep(sleep_duration)

    db.close()
    logging.info(f"✅ 抓取任务完成。成功: {success_count} 条，失败: {fail_count} 条")


# ---------------- 附加功能模块 ----------------

def detect_price_drop(model: str, new_price: float, db: PriceDatabase) -> Optional[str]:
    """检查是否出现明显价格下降，返回警告信息"""
    latest = db.fetch_latest(model)
    if latest is not None and new_price < latest * 0.9:  # 下跌超10%
        drop_percent = round((latest - new_price) / latest * 100, 2)
        message = f"⚠️ 检测到价格下跌：{model} 从 {latest} ➜ {new_price}（下降 {drop_percent}%）"
        logging.warning(message)
        return message
    return None


# ---------------- 可选并发结构预留 ----------------

class TaskRunner:
    def __init__(self, urls: List[str]):
        self.urls = urls
        self.db = PriceDatabase()
        self.stats = {
            "success": 0,
            "fail": 0,
            "start_time": time.time()
        }

    def run_single(self, url: str, index: int):
        logging.info(f"[{index+1}] 开始抓取任务: {url}")
        fetcher = PageFetcher(url)
        raw_data = fetcher.fetch()

        if not raw_data:
            self.stats["fail"] += 1
            return

        parser = PriceParser(raw_data, url)
        result = parser.extract()
        if not result:
            self.stats["fail"] += 1
            return

        self.db.insert_price(result)
        drop_notice = detect_price_drop(result["model"], result["price"], self.db)
        if drop_notice:
            print(drop_notice)

        self.stats["success"] += 1
        time.sleep(random.uniform(1.2, 2.5))

    def run_all_sequential(self):
        for idx, url in enumerate(self.urls):
            self.run_single(url, idx)

    def finish(self):
        self.db.close()
        elapsed = round(time.time() - self.stats["start_time"], 2)
        print(f"\n📊 报告：成功 {self.stats['success']} 条，失败 {self.stats['fail']} 条")
        print(f"⏱️ 总耗时：{elapsed} 秒")
        logging.info(f"任务完成：成功 {self.stats['success']}，失败 {self.stats['fail']}，耗时 {elapsed} 秒")



if __name__ == "__main__":
    try:
        runner = TaskRunner(URLS)
        runner.run_all_sequential()
        runner.finish()
    except Exception as e:
        logging.critical(f"未捕获异常终止程序：{e}", exc_info=True)
        print("❌ 程序异常中止，请查看 logs/get_prices.log 日志文件。")
