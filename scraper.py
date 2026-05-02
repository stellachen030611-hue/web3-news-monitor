import requests
import json
import os
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime

# 1. 扩充源矩阵：参考 Chainfeeds 逻辑进行分类
# 包含：公链官推、头部安全、投研机构、治理提案
SOURCES = {
    "主流快讯": "https://rsshub.app/foresightnews/news",
    "深度分析": "https://rsshub.app/chaincatcher/news",
    "全球视野": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "公链生态": "https://rsshub.app/ethereum/blogs",
    "安全监控": "https://rsshub.app/slowmist/fort",
    "融资动态": "https://rsshub.app/rootdata/recent",
    "治理提案": "https://rsshub.app/snapshot/proposals/active",
    "投研机构": "https://rsshub.app/messari/blog",
    "技术前沿": "https://vitalik.ca/feed.xml",
    "交易所": "https://rsshub.app/binance/announcement"
}

def get_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def fetch_source(category, url):
    print(f"📡 正在同步 [{category}] 数据...")
    items = []
    try:
        # 模拟浏览器请求，防止被屏蔽
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Web3Dashboard/1.0'}
        response = requests.get(url, timeout=20, headers=headers)
        response.encoding = 'utf-8'
        
        # 适配 XML (RSS) 格式
        root = ET.fromstring(response.text)
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else str(datetime.now())
            # 提取简短摘要
            desc = item.find('description').text if item.find('description') is not None else ""
            summary = desc[:150].replace('<', '').replace('>', '') # 简单去标签
            
            if title:
                items.append({
                    "id": get_md5(title + link),
                    "category": category,
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "summary": f"{summary}..."
                })
    except Exception as e:
        print(f"❌ {category} 同步失败: {str(e)}")
    return items

def main():
    all_data = []
    for cat, url in SOURCES.items():
        all_data.extend(fetch_source(cat, url))
    
    # 按照抓取顺序（最新）排序，并保留 200 条以确保内容丰富度
    file_name = 'web3_news.json'
    
    # 读取旧数据实现增量更新
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                old_data = json.load(f)
            except:
                old_data = []
    else:
        old_data = []

    existing_ids = {item['id'] for item in old_data}
    new_items = [i for i in all_data if i['id'] not in existing_ids]
    
    # 合并：新数据在前
    final_output = (new_items + old_data)[:200]

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 全域同步完成！库中现有 {len(final_output)} 条情报。")

if __name__ == "__main__":
    main()