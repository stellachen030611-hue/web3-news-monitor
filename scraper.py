import requests
import json
import os
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime

# 量化因子矩阵：定义不同信号的关键词和权重
STRATEGY_FACTORS = {
    "交易所信号": {"weight": 10, "keys": ["listing", "上架", "上线", "announcement", "trading pair"]},
    "安全风险": {"weight": 9, "keys": ["hack", "attack", "vulnerability", "漏洞", "攻击", "警报"]},
    "治理套利": {"weight": 7, "keys": ["proposal", "vote", "提案", "投票", "snapshot"]},
    "融资情绪": {"weight": 6, "keys": ["raised", "financing", "融资", "million", "seed"]},
    "宏观解读": {"weight": 5, "keys": ["etf", "sec", "fed", "加息", "降息"]}
}

SOURCES = {
    "交易所信号": "https://rsshub.app/binance/announcement",
    "安全风险": "https://rsshub.app/slowmist/fort",
    "治理套利": "https://rsshub.app/snapshot/proposals/active",
    "融资情绪": "https://rsshub.app/rootdata/recent",
    "深度投研": "https://rsshub.app/chaincatcher/news",
    "宏观资讯": "https://rsshub.app/foresightnews/news",
    "全球视野": "https://www.coindesk.com/arc/outboundfeeds/rss/"
}

def get_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def analyze_signal(title, summary):
    text = (title + summary).lower()
    tag = "其它"
    score = 0
    for factor, config in STRATEGY_FACTORS.items():
        if any(key in text for key in config["keys"]):
            tag = factor
            score = config["weight"]
            break
    return tag, score

def fetch_rss(category, url):
    print(f"📡 正在扫描 [{category}]...")
    items = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Web3Quant/2.0'}
        response = requests.get(url, timeout=20, headers=headers)
        response.encoding = 'utf-8'
        root = ET.fromstring(response.text)
        
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            date = item.find('pubDate').text if item.find('pubDate') is not None else str(datetime.now())
            desc = item.find('description').text if item.find('description') is not None else ""
            summary = desc[:150].replace('<', '').replace('>', '')

            # 信号识别逻辑
            signal_tag, score = analyze_signal(title, summary)
            
            if title:
                items.append({
                    "id": get_md5(title + link),
                    "category": signal_tag, # 覆盖原始分类为信号分类
                    "score": score,
                    "title": title,
                    "link": link,
                    "date": date,
                    "summary": summary
                })
    except Exception as e:
        print(f"❌ {category} 同步失败: {e}")
    return items

def main():
    all_data = []
    for cat, url in SOURCES.items():
        all_data.extend(fetch_rss(cat, url))
    
    # 增量更新与去重
    file_path = 'web3_news.json'
    old_data = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    existing_ids = {i['id'] for i in old_data}
    new_items = [i for i in all_data if i['id'] not in existing_ids]
    
    # 按得分和时间排序，保留前200条
    final_output = (new_items + old_data)[:200]
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    print(f"✅ 同步完成，库中现有 {len(final_output)} 条因子信号。")

if __name__ == "__main__":
    main()
