"""
分析日本媒体和社交平台上的iPhone讨论热度
"""

from collections import Counter

def analyze_media():
    keywords = ["iPhone", "安い", "高い", "買い時"]
    sample_posts = ["今のiPhone安い", "買い時じゃない？", "新型高いな"]
    word_count = Counter()
    for post in sample_posts:
        for word in keywords:
            if word in post:
                word_count[word] += 1
    print(word_count)

if __name__ == "__main__":
    analyze_media()
