import requests
import json
import os
import hashlib

# Odaily 的 RSS 地址（这是最稳定的白嫖接口）
RSS_URL = "https://rss.odaily.news/rss/newsflash"

def get_md5(text):
    """为每条新闻生成唯一ID，用于去重"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def scrape_odaily():
    print("开始抓取 Odaily 快讯...")
    try:
        # 使用 XML 解析或者简单的字符串处理，RSS本质是XML
        # 为了不增加依赖包，我们直接用 requests 拿到内容
        response = requests.get(RSS_URL, timeout=10)
        response.encoding = 'utf-8'
        
        # 极简解析逻辑：寻找 <item> 标签
        # 实际开发中如果追求极致稳定，建议用 feedparser 库
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.text)
        
        new_items = []
        for item in root.findall('.//item'):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            description = item.find('description').text if item.find('description') is not None else ""
            
            news_id = get_md5(title) # 以标题生成唯一标识
            
            new_items.append({
                "id": news_id,
                "title": title,
                "link": link,
                "date": pub_date,
                "summary": description[:100] + "..." # 截取前100字作为摘要
            })
        
        return new_items
    except Exception as e:
        print(f"抓取失败: {e}")
        return []

def save_data(new_news):
    file_name = 'web3_news.json'
    
    # 1. 读取旧数据（如果存在）
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                old_data = json.load(f)
            except:
                old_data = []
    else:
        old_data = []

    # 2. 去重并合并
    existing_ids = {item['id'] for item in old_data}
    added_count = 0
    
    for item in new_news:
        if item['id'] not in existing_ids:
            old_data.insert(0, item) # 新闻插到最前面
            added_count += 1
    
    # 3. 只保留最近的 100 条，防止文件无限增大
    final_data = old_data[:100]

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成！新增 {added_count} 条，总计保留 {len(final_data)} 条。")

if __name__ == "__main__":
    news = scrape_odaily()
    if news:
        save_data(news)