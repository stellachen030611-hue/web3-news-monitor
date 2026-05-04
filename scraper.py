import requests
import json
import re
from datetime import datetime

# 量化因子关键词映射
FACTOR_MAP = {
    "衍生品": r"资金费率|多空比|Funding Rate|Long-Short|清算|Liquidation|持仓量|OI",
    "流动性": r"深度|Depth|盘口|Volume|成交量|Market Maker|造市商|滑点",
    "链上活性": r"巨鲸|Whale|大额转账|Active Address|活跃地址|燃烧|Burn|TVL",
    "交易/执行": r"API|延迟|Latency|下单|撤单|账户资产|Listing|上币"
}

def classify_signal(text):
    for category, pattern in FACTOR_MAP.items():
        if re.search(pattern, text, re.IGNORECASE):
            return category
    return "其它"

def scrape_quant_signals():
    # 示例使用 Odaily 接口，实际可扩展至交易所公告 API 或 Whale Alert
    url = "https://www.odaily.news/api/pp/api/info-flow/newsflash_columns/newsflash_list?limit=20"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    signals = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json().get('data', {}).get('items', [])
        
        for item in data:
            title = item.get('title', '')
            content = item.get('description', '')
            full_text = title + content
            
            category = classify_signal(full_text)
            
            # 提取潜在数值 (如百分比或金额)
            value_match = re.search(r'(\d+(\.\d+)?%|\$\d+(,\d+)*(\.\d+)?[MBK]?)', full_text)
            key_value = value_match.group(0) if value_match else ""

            signals.append({
                "title": title,
                "summary": content[:120],
                "category": category,
                "key_value": key_value, # 关键数值提取
                "link": f"https://www.odaily.news/newsflash/{item.get('id')}",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    except Exception as e:
        print(f"抓取异常: {e}")
    
    return signals

if __name__ == "__main__":
    data = scrape_quant_signals()
    with open('web3_news.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"成功导出 {len(data)} 条量化信号")
