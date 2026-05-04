import requests
import json
import re
from datetime import datetime

# 分类必须与 popup.js 中的 categories 数组严格对应
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
    return "其它" # 默认归类为“其它”

def scrape_quant_signals():
    # 仍以快讯为基础数据源
    url = "https://www.odaily.news/api/pp/api/info-flow/newsflash_columns/newsflash_list?limit=50" # 增加抓取量确保有信号
    headers = {"User-Agent": "Mozilla/5.0"}
    
    signals = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json().get('data', {}).get('items', [])
        
        for item in data:
            title = item.get('title', '')
            content = item.get('description', '')
            full_text = f"{title} {content}"
            
            category = classify_signal(full_text)
            
            # 强化数值提取，这对后续构建因子策略至关重要
            value_match = re.search(r'(\d+(\.\d+)?%|\$\d+(,\d+)*(\.\d+)?[MBK]?)', full_text)
            key_value = value_match.group(0) if value_match else ""

            signals.append({
                "title": title,
                "summary": content[:120],
                "category": category,
                "key_value": key_value,
                "link": f"https://www.odaily.news/newsflash/{item.get('id')}",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    except Exception as e:
        print(f"抓取异常: {e}")
    
    return signals

if __name__ == "__main__":
    data = scrape_quant_signals()
    # 强制覆盖保存
    with open('web3_news.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"成功导出 {len(data)} 条量化信号")
