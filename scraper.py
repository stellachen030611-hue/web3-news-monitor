import requests
import json
import os
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime

# 1. 配置抓取源矩阵 (RSS 协议为主，稳定且免费)
# 提示：如果某个 RSSHub 链接失效，可以更换其他公共实例
SOURCES = {
    "快讯": "https://rss.odaily.news/rss/newsflash",
    "全球视野": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "安全监控": "https://rsshub.app/slowmist/fort",
    "融资动态": "https://rsshub.app/rootdata/recent",
    "深度分析": "https://rsshub.app/chaincatcher/news",
    "交易所": "https://rsshub.app/binance/announcement"
}

def get_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def fetch_rss_source(category, url):
    print(f"正在抓取 [{category}]...")
    items = []
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.encoding = 'utf-8'
        root = ET.fromstring(response.text)
        
        # 统一解析标准 RSS 格式
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else "无标题"
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else str(datetime.now())
            desc = item.find('description').text if item.find('description') is not None else ""
            
            items.append({
                "id": get_md5(title),
                "category": category,  # 关键字段：用于前端过滤
                "title": title,
                "link": link,
                "date": pub_date,
                "summary": desc[:120] + "..." # 摘要截取
            })
    except Exception as e:
        print(f"{category} 抓取失败: {e}")
    return items

def main():
    all_news = []
    for cat, url in SOURCES.items():
        all_news.extend(fetch_rss_source(cat, url))
    
    # 按时间降序排列 (简单处理，实际可根据 pubDate 转换时间戳排序)
    # 这里我们先把新抓到的放在前面
    
    file_name = 'web3_news.json'
    
    # 读取旧数据实现去重
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                old_data = json.load(f)
            except:
                old_data = []
    else:
        old_data = []

    existing_ids = {item['id'] for item in old_data}
    new_added = []
    for item in all_news:
        if item['id'] not in existing_ids:
            new_added.append(item)
    
    # 合并并保留最新的 150 条资讯
    final_data = (new_added + old_data)[:150]

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"聚合完成！新增 {len(new_added)} 条，总库共 {len(final_data)} 条。")

if __name__ == "__main__":
    main()
