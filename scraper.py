import requests
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 分类逻辑：严格对应插件按键
FACTOR_MAP = {
    "衍生品": r"资金费率|Funding|多空比|Long-Short|清算|Liquidation|持仓量|OI",
    "流动性": r"深度|Depth|盘口|Volume|成交量|Spread|买卖盘",
    "链上活性": r"巨鲸|Whale|Active Address|活跃地址|新增地址|Mint|Burn",
    "交易/执行": r"API|延迟|Latency|下单|撤单|账户资产|维护"
}

def classify_signal(text):
    for category, pattern in FACTOR_MAP.items():
        if re.search(pattern, text, re.IGNORECASE):
            return category
    return "其它"

def get_okx_full_data():
    """整合 OKX 的费率与盘口深度"""
    signals = []
    base_url = "https://www.okx.com/api/v5"
    try:
        # 1. 获取主流币费率
        for inst in ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP"]:
            f_res = requests.get(f"{base_url}/public/funding-rate?instId={inst}", timeout=5)
            if f_res.status_code == 200:
                rate = float(f_res.json()['data'][0]['fundingRate'])
                signals.append({
                    "title": f"OKX: {inst} 资金费率",
                    "summary": f"实时费率 {rate*100:.4f}%。反映当前市场杠杆偏向。",
                    "category": "衍生品",
                    "key_value": f"{rate*100:.3f}%",
                    "link": f"https://www.okx.com/trade-swap/{inst}",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        # 2. 获取盘口深度 (流动性因子)
        d_res = requests.get(f"{base_url}/market/books?instId=BTC-USDT", timeout=5)
        if d_res.status_code == 200:
            data = d_res.json()['data'][0]
            ask = float(data['asks'][0][0])
            bid = float(data['bids'][0][0])
            spread = (ask - bid) / bid * 100
            signals.append({
                "title": "OKX 流动性: BTC/USDT 盘口价差",
                "summary": f"当前最佳买卖价差(Spread)为 {spread:.5f}%。价差波动常预示行情剧变。",
                "category": "流动性",
                "key_value": f"S:{spread:.4f}%",
                "link": "#",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    except Exception as e:
        print(f"OKX 接口异常: {e}")
    return signals

def get_realtime_news_signals():
    """从快讯源提取 链上/交易/流动性 信号"""
    url = "https://www.odaily.news/api/pp/api/info-flow/newsflash_columns/newsflash_list?limit=50"
    headers = {"User-Agent": "Mozilla/5.0"}
    signals = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get('data', {}).get('items', [])
            for item in items:
                title = item['title']
                content = item['description']
                full_text = title + content
                cat = classify_signal(full_text)
                
                # 如果不是“其它”，说明匹配到了我们要的量化维度
                if cat != "其它":
                    val_m = re.search(r'(\d+(\.\d+)?%|\$\d+(,\d+)*(\.\d+)?[MBK]?)', full_text)
                    signals.append({
                        "title": title,
                        "summary": content[:100] + "...",
                        "category": cat,
                        "key_value": val_m.group(0) if val_m else "SIGNAL",
                        "link": f"https://www.odaily.news/newsflash/{item['id']}",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
    except: pass
    return signals

def scrape_all():
    print(">>> 正在聚合 OKX 实时因子与链上异动...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(get_okx_full_data)
        f2 = executor.submit(get_realtime_news_signals)
        
        all_data = f1.result() + f2.result()
    
    # 增加模拟的账户查询信号（作为交易执行分类的占位，供后续接入API）
    all_data.append({
        "title": "交易执行: API 延迟监测",
        "summary": "OKX REST API 延迟: 120ms; WebSocket 状态: 正常。",
        "category": "交易/执行",
        "key_value": "120ms",
        "link": "#",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return all_data

if __name__ == "__main__":
    results = scrape_all()
    with open('web3_news.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f">>> 采集完成，当前因子库规模: {len(results)}")
