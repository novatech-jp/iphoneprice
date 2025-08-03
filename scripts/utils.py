"""
工具函数
"""

def normalize_price(price_str):
    try:
        return float(price_str.replace(",", "").replace("¥", ""))
    except:
        return None
