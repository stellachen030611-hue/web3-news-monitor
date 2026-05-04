import requests
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 因子分类映射
FACTOR_MAP = {
    "衍生品": r"资金费率|Funding|多空比|Long-Short|清算|Liquidation|持仓量|OI",
    "流动性": r"深度|Depth|盘口|Volume|成交量|Market Maker",
    "链上活性": r"巨鲸|Whale|Active Address|活跃地址",
    "交易/执行": r"API|延迟|Latency|下单|撤单|Listing|上币"
}

def classify_signal(text):
    for category, pattern in FACTOR_MAP.items():
        if re.search(pattern, text, re.IGNORECASE):
            return category
    return "其它"

def get_binance_funding():
    """获取币安永续合约资金费率"""
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    signals = []
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            # 筛选前 30 个热门交易对
            for item in res.json()[:30]:
                symbol = item['symbol']
                rate = float(item['lastFundingRate'])
                if abs(rate) > 0.0001: # 过滤噪声
                    signals.append({
                        "title": f"Binance: {symbol} 资金费率报告",
                        "summary": f"实时费率: {rate*100:.4f}%。该指标用于评估市场多空情绪。",
                        "category": "衍生品",
                        "key_value": f"{rate*100:.3f}%",
                        "link": f"https://www.binance.com/zh-CN/futures/{symbol}",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
    except Exception as e: print(f"Binance Error: {e}")
    return signals

def get_okx_funding():
    """获取 OKX 永续合约资金费率"""
    # OKX API V5 接口
    url = "https://www.okx.com/api/v5/public/funding-rate"
    # 获取主流品种，这里以 BTC 和 ETH 为例，实际可扩展
    symbols = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP"]
    signals = []
    try:
        for instId in symbols:
            res = requests.get(f"{url}?instId={instId}", timeout=5)
            if res.status_code == 200:
                data = res.json().get('data', [{}])[0]
                rate = float(data.get('fundingRate', 0))
                signals.append({
                    "title": f"OKX: {instId} 信号监测",
                    "summary": f"当前资金费率为 {rate*100:.4f}%。OKX 费率是跨所对冲策略的核心参考。",
                    "category": "衍生品",
                    "key_value": f"{rate*100:.3f}%",
                    "link": f"https://www.okx.com/trade-swap/{instId}",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
    except Exception as e: print(f"OKX Error: {e}")
    return signals

def scrape_all():
    print("正在聚合 Binance 和 OKX 量化因子...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(get_binance_funding)
        f2 = executor.submit(get_okx_funding)
        
        # 合并结果
        all_signals = f1.result() + f2.result()
        
    # 如果接口都失败了，保留保底逻辑确保 UI 不白屏
    if not all_signals:
        return [{"title": "API 暂时受限", "summary": "正在尝试重新连接交易所数据源...", "category": "其它", "date": ""}]
    
    return all_signals

if __name__ == "__main__":
    data = scrape_all()
    with open('web3_news.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"聚合完成：共获 {len(data)} 条跨所信号数据。")
