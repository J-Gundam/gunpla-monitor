import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup

# ==================== 【設定欄】 ====================
MY_ID = "8725074760"

# 監視するXアカウント（サボリーマンさんのIDを設定済み）
WATCH_X_USER = "aanc20"

# ［ターゲットガンプラと税込定価の設定］
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

SECRET_KEY = os.environ.get("TELEGRAM_TOKEN")
X_COOKIE = os.environ.get("X_COOKIE")
CHECKED_POSTS = set()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def push_msg(text_data):
    """Telegramへ通知を強制送信する"""
    if not SECRET_KEY:
        print("❌ エラー: TELEGRAM_TOKEN が設定されていません。")
        return
    base_api = "https://" + "api." + "telegram" + ".org/bot"
    send_url = f"{base_api}{SECRET_KEY}/sendMessage"
    payload = {"chat_id": MY_ID, "text": text_data, "parse_mode": "HTML"}
    try:
        requests.post(send_url, data=payload)
    except Exception as e:
        print(f"Telegramエラー: {e}")

def check_amazon_product(asin, keyword, max_price):
    """Amazonの販売元と価格をピンポイントで最速チェックする"""
    url = f"https://amazon.co.jp{asin}"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ja-JP,ja;q=0.9",
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        merchant_info = soup.find('div', id='merchantInfoID') or soup.find('div', class_='tabular-buybox-text')
        is_amazon_sales = False
        if merchant_info and "Amazon" in merchant_info.text:
            is_amazon_sales = True
            
        if not is_amazon_sales:
            print(f"⚠️ 転売屋の出品のためスルー: {keyword}")
            return
            
        price_el = soup.find('span', class_='a-price-whole')
        if price_el:
            price_val = int(price_el.text.replace(',', '').strip())
            if price_val <= max_price:
                cart_url = f"https://amazon.co.jp{asin}&Quantity.1=1"
                msg = f"🔥 <b>【ガンプラ最速検知！】</b>\n\n<b>商品:</b> {keyword}\n<b>価格:</b> {price_val}円（定価以下・Amazon直販）\n\n🛒 <b>1タップカートイン直リンク:</b>\n{cart_url}"
                push_msg(msg)
                print(f"★条件合致！通知送信: {keyword}")
    except Exception as e:
        print(f"Amazonチェックエラー: {e}")

def get_x_posts():
    """Xのアカウントを使ってポストをリアルタイムに確認する"""
    if not X_COOKIE:
        print("❌ エラー: X_COOKIE が設定されていません。")
        return
        
    url = f"https://twitter.com{WATCH_X_USER}"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Cookie": X_COOKIE
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        links = re.findall(r'https://amzn\.to/[a-zA-Z0-9]+', res.text)
        
        for link in links:
            if link in CHECKED_POSTS:
                continue
            CHECKED_POSTS.add(link)
            
            try:
                real_res = requests.head(link, allow_redirects=True, timeout=5)
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', real_res.url)
                if asin_match:
                    asin = asin_match.group(1)
                    
                    for keyword, max_price in TARGET_PRODUCTS.items():
                        if keyword in res.text:
                            check_amazon_product(asin, keyword, max_price)
            except:
                continue
    except Exception as e:
        print(f"X巡回エラー: {e}")

if __name__ == "__main__":
    get_x_posts()
