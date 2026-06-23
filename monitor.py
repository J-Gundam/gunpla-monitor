import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup

# ==================== 【設定欄】 ====================
# あなたのTelegramチャットID（固定化して確実に届くようにしました）
MY_CHAT_ID = "8725074760"

# ［あなた専用・完璧定価フィルター仕様］
TARGET_PRODUCTS = {
    "MG ケンプファー": 4400,
    "HGUC ケンプファー": 1980,
    "クシャトリヤ・リペアード": 7150,
    "ガンダムEX": 2090,
    "MGSD ガンダムエアリアル": 4290,
    "MGSD デスティニーガンダム": 4950,
    "プルツー": 3520,
    "RG AV-98Plus": 4950,
    "グローグー G3477": 5800,
    "RMZ-016 パンツァー": 9900
}
# ====================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHECKED_ASINS = set()

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]

def send_telegram(message):
    """Telegramに1タップ購入リンクを通知する"""
    if not TELEGRAM_TOKEN:
        print("エラー: TELEGRAM_TOKEN が設定されていません。")
        return
        
    send_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": MY_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(send_url, data=payload)
    except Exception as e:
        print(f"Telegram送信エラー: {e}")

def monitor_amazon_direct():
    """Amazonを巡回してガンプラを最速検知する"""
    print("Amazonのガンプラ在庫を直接巡回中...")
    
    for keyword, max_price in TARGET_PRODUCTS.items():
        encoded_keyword = requests.utils.quote(keyword)
        search_url = f"https://amazon.co.jp{encoded_keyword}&s=date-desc-rank"
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "ja-JP,ja;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        try:
            res = requests.get(search_url, headers=headers, timeout=10)
            
            if res.status_code == 503 or "api-services-support@amazon.com" in res.text:
                print("⚠️ Amazonからブロック（503）を検知しました。待機します。")
                continue
                
            soup = BeautifulSoup(res.text, 'html.parser')
            products = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for product in products:
                asin = product.get('data-asin')
                if not asin or asin in CHECKED_ASINS:
                    continue
                
                title_el = product.find('h2')
                if not title_el:
                    continue
                title = title_el.text.strip()
                
                price_text = "不明"
                price_el = product.find('span', class_='a-price-whole')
                if price_el:
                    price_text = price_el.text.replace(',', '').strip()
                
                try:
                    price_val = int(price_text)
                    if price_val > max_price:
                        continue
                except ValueError:
                    continue
                
                CHECKED_ASINS.add(asin)
                cart_url = f"https://amazon.co.jp{asin}&Quantity.1=1"
                
                msg = f"🔥 <b>【Amazon公式 ガンプラ検知！】</b>\n\n<b>商品:</b> {title}\n<b>価格:</b> {price_val}円（定価: {max_price}円以下）\n\n🛒 <b>1タップカートイン直リンク:</b>\n{cart_url}"
                send_telegram(msg)
                print(f"★Amazon直検知！Telegramへ通知: {title}")
                    
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"Amazon巡回エラー: {e}")

if __name__ == "__main__":
    # 保存直後のテスト通知
    send_telegram("🤖 ガンプラBotの接続テスト成功です！本番稼働を開始します。")
    monitor_amazon_direct()
