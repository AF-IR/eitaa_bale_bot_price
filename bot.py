import re
import requests

# ═══════════════════════════════════════════════════════════
#                    تنظیمات
# ═══════════════════════════════════════════════════════════
BALE_TOKEN = "197490409:ZFE5SflFy0CNIuMdMNdUtNIdFF4GpfRfyCE"
BALE_CHANNEL = "5107422630"

EITAA_TOKEN = "bot203362:2edad421-628f-4534-80b9-6675bdf9f46c"
EITAA_CHANNEL = "11148234"  # ← شناسه عددی کانال ایتا

# ═══════════════════════════════════════════════════════════
#                    دریافت قیمت تتر
# ═══════════════════════════════════════════════════════════
def get_usdt_price():
    try:
        r = requests.get(
            "https://nobitex.ir/price/usdt/",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=15
        )
        
        patterns = [
            r'<span class="text-body-large text-headline-medium[^"]*">([\d,]+)</span>',
            r'<span[^>]*class="[^"]*text-headline[^"]*"[^>]*>([\d,]+)</span>',
            r'>([\d]{5,7})</span>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, r.text)
            if match:
                price = float(match.group(1).replace(',', ''))
                if price > 10000:
                    return price
        return None
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#                    ارسال به بله
# ═══════════════════════════════════════════════════════════
def send_to_bale(price):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    
    message = f"""💵 قیمت تتر

{price:,.0f} تومان

📊 منبع: نوبیتکس"""

    try:
        r = requests.post(url, json={
            'chat_id': BALE_CHANNEL,
            'text': message,
            'parse_mode': 'Markdown'
        }, timeout=30)
        
        result = r.json()
        if result.get('ok'):
            print("✅ بله: ارسال شد")
            return True
        else:
            print(f"❌ بله: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ بله: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#                    ارسال به ایتا
# ═══════════════════════════════════════════════════════════
def send_to_eitaa(price):
    url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
    
    message = f"""💵 قیمت تتر

{price:,.0f} تومان

📊 منبع: نوبیتکس"""

    try:
        r = requests.post(url, data={
            'chat_id': EITAA_CHANNEL,
            'text': message
        }, timeout=30)
        
        result = r.json()
        if result.get('ok'):
            print("✅ ایتا: ارسال شد")
            return True
        else:
            print(f"❌ ایتا: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ ایتا: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#                    اجرا
# ═══════════════════════════════════════════════════════════
def main():
    print("=" * 40)
    print("🤖 تست ارسال قیمت تتر")
    print("=" * 40)
    
    print("\n📡 دریافت قیمت از نوبیتکس...")
    price = get_usdt_price()
    
    if not price:
        print("❌ قیمت دریافت نشد!")
        return
    
    print(f"✅ قیمت: {price:,.0f} تومان")
    
    print("\n📤 ارسال...")
    send_to_bale(price)
    send_to_eitaa(price)
    
    print("\n" + "=" * 40)
    print(f"تمام شد! قیمت: {price:,.0f} تومان")
    print("=" * 40)


if __name__ == '__main__':
    main()
