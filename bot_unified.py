#!/usr/bin/env python3
"""
📊 ربات استعلام قیمت ارز - بله و ایتا
نسخه 5.0 - یکپارچه
یک بار استعلام → ارسال به هر دو پلتفرم
"""
import json
import os
import logging
import random
import re
from datetime import datetime
from typing import Optional
import requests
import pytz

# ═══════════════════════════════════════════════════════════
#                    تنظیمات اولیه
# ═══════════════════════════════════════════════════════════
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

NOBITEX_URL = "https://nobitex.ir/price/usdt/"

# ═══════════════════════════════════════════════════════════
#                    API Bale
# ═══════════════════════════════════════════════════════════
class BaleAPI:
    """کلاس ارتباط با API بله"""
    
    BASE_URL = "https://tapi.bale.ai"
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"{self.BASE_URL}/bot{token}"
    
    def _request(self, method: str, data: dict = None) -> dict:
        """ارسال درخواست به API بله"""
        url = f"{self.base_url}/{method}"
        
        try:
            if data is None:
                response = requests.get(url, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('ok'):
                return result.get('result', {})
            else:
                logger.error(f"خطای API بله: {result.get('description')}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در اتصال به API بله: {e}")
            return {}
    
    def getMe(self) -> dict:
        """دریافت اطلاعات ربات"""
        return self._request("getMe")
    
    def sendMessage(self, chat_id: str, text: str) -> bool:
        """ارسال پیام به بله"""
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        result = self._request("sendMessage", data)
        return bool(result)


# ═══════════════════════════════════════════════════════════
#                    API Eitaa
# ═══════════════════════════════════════════════════════════
class EitaaAPI:
    """کلاس ارتباط با API ایتا"""
    
    BASE_URL = "https://eitaayar.ir/api"
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"{self.BASE_URL}/{token}"
    
    def _request(self, method: str, data: dict = None) -> dict:
        """ارسال درخواست به API ایتا"""
        url = f"{self.base_url}/{method}"
        
        try:
            if data:
                response = requests.post(url, data=data, timeout=30)
            else:
                response = requests.get(url, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                error_desc = result.get("description", "خطای نامشخص")
                logger.error(f"خطای API ایتا: {error_desc}")
                return {}
            
            return result.get("result", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در اتصال به API ایتا: {e}")
            return {}
    
    def getMe(self) -> dict:
        """دریافت اطلاعات ربات"""
        return self._request("getMe")
    
    def sendMessage(self, chat_id: str, text: str) -> bool:
        """ارسال پیام به ایتا"""
        data = {
            "chat_id": chat_id,
            "text": text
        }
        result = self._request("sendMessage", data)
        return bool(result)


# ═══════════════════════════════════════════════════════════
#                    توابع کمکی
# ═══════════════════════════════════════════════════════════
def to_persian_num(num: float, decimals: int = 0) -> str:
    """تبدیل عدد به فرمت فارسی با حفظ اعشار"""
    if num is None or num == 0:
        return "نامشخص"
    
    persian_digits = str.maketrans('0123456789.,', '۰۱۲۳۴۵۶۷۸۹٫٬')
    
    if decimals > 0:
        formatted = f"{num:,.{decimals}f}".replace(',', '٬')
    else:
        formatted = f"{num:,.0f}".replace(',', '٬')
    
    return formatted.translate(persian_digits)


def format_percent(change: float) -> str:
    """فرمت درصد تغییرات"""
    if change is None or change == 0:
        return "۰٪"
    
    persian_digits = str.maketrans('0123456789.-', '۰۱۲۳۴۵۶۷۸۹٫−')
    sign = "+" if change > 0 else ""
    percent_str = f"{sign}{change:.2f}٪"
    return percent_str.translate(persian_digits)


def get_change_emoji(change: float) -> str:
    """ایموجی بر اساس درصد تغییرات"""
    if change is None:
        return "➖"
    elif change > 5:
        return "🚀"
    elif change > 2:
        return "📈"
    elif change > 0:
        return "⬆️"
    elif change == 0:
        return "➖"
    elif change > -2:
        return "⬇️"
    elif change > -5:
        return "📉"
    else:
        return "💥"


def load_config() -> dict:
    """بارگذاری تنظیمات"""
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # تنظیمات بله
    config['bot_token'] = os.environ.get('BOT_TOKEN', config.get('bot_token', ''))
    config['admin_id'] = int(os.environ.get('ADMIN_ID', config.get('admin_id', 0)))
    config['channel_id'] = os.environ.get('CHANNEL_ID', config.get('channel_id', ''))
    config['channel_link'] = os.environ.get('CHANNEL_LINK', config.get('channel_link', ''))
    config['ad_link'] = os.environ.get('AD_LINK', config.get('ad_link', ''))
    
    # تنظیمات ایتا
    config['eitaa_token'] = os.environ.get('EITAA_BOT_TOKEN', config.get('eitaa_token', ''))
    config['eitaa_channel_id'] = os.environ.get('EITAA_CHANNEL_ID', config.get('eitaa_channel_id', ''))
    
    return config


# ═══════════════════════════════════════════════════════════
#                    دریافت قیمت تتر از نوبیتکس
# ═══════════════════════════════════════════════════════════
def get_usdt_price_from_nobitex() -> Optional[float]:
    """دریافت قیمت تتر از نوبیتکس"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'fa,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    try:
        response = requests.get(NOBITEX_URL, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text
        
        patterns = [
            r'<span class="text-body-large text-headline-medium[^"]*">([\d,]+)</span>',
            r'<span[^>]*class="[^"]*text-headline[^"]*"[^>]*>([\d,]+)</span>',
            r'>([\d]{5,7})</span>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                price_str = match.group(1).replace(',', '')
                price = float(price_str)
                if price > 10000:
                    logger.info(f"✅ قیمت تتر: {price:,.0f} تومان")
                    return price
        
        logger.error("هیچ الگویی با قیمت تتر مطابقت نکرد")
        return None
        
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت از نوبیتکس: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#                    دریافت قیمت‌های جهانی از CoinGecko
# ═══════════════════════════════════════════════════════════
def get_global_prices() -> dict:
    """دریافت قیمت‌های جهانی از CoinGecko"""
    prices = {
        'crypto': {},
        'gold_usd': 0.0,
        'gold_change_24h': 0.0,
    }
    
    # ارزهای دیجیتال
    crypto_ids = [
        'bitcoin', 'ethereum', 'ripple', 'solana', 'dogecoin',
        'cardano', 'polkadot', 'tron', 'litecoin', 'bitcoin-cash',
        'avalanche-2', 'chainlink', 'uniswap', 'matic-network', 'shiba-inu',
        'binancecoin', 'stellar', 'cosmos', 'near'
    ]
    
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': ','.join(crypto_ids),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        for coin_id, info in data.items():
            prices['crypto'][coin_id] = {
                'usd': float(info.get('usd', 0)),
                'change_24h': float(info.get('usd_24h_change', 0))
            }
        
        logger.info(f"✅ {len(prices['crypto'])} ارز دیجیتال دریافت شد")
        
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت کریپتو: {e}")
    
    # طلا (Pax Gold)
    try:
        gold_url = "https://api.coingecko.com/api/v3/simple/price"
        gold_params = {
            'ids': 'pax-gold',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        gold_response = requests.get(gold_url, params=gold_params, timeout=10)
        gold_data = gold_response.json()
        
        if 'pax-gold' in gold_data:
            prices['gold_usd'] = float(gold_data['pax-gold'].get('usd', 0))
            prices['gold_change_24h'] = float(gold_data['pax-gold'].get('usd_24h_change', 0))
            logger.info(f"✅ قیمت طلا (PAXG): ${prices['gold_usd']}")
            
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت طلا: {e}")
        prices['gold_usd'] = 2350.0
        prices['gold_change_24h'] = 0.0
    
    return prices


# ═══════════════════════════════════════════════════════════
#                    فرمت‌های پیام
# ═══════════════════════════════════════════════════════════
def format_message_v1(usdt_price: float, global_prices: dict, config: dict) -> str:
    """فرمت ۱: جدول کامل"""
    tz = pytz.timezone(config.get('timezone', 'Asia/Tehran'))
    now = datetime.now(tz)
    date_str = now.strftime('%Y/%m/%d')
    time_str = now.strftime('%H:%M')
    
    crypto_list = [
        ('bitcoin', 'BTC', 0),
        ('ethereum', 'ETH', 2),
        ('solana', 'SOL', 2),
        ('ripple', 'XRP', 4),
        ('cardano', 'ADA', 4),
        ('dogecoin', 'DOGE', 5),
        ('polkadot', 'DOT', 2),
        ('chainlink', 'LINK', 2),
        ('litecoin', 'LTC', 2),
        ('avalanche-2', 'AVAX', 2),
        ('binancecoin', 'BNB', 2),
        ('uniswap', 'UNI', 3),
        ('matic-network', 'MATIC', 4),
        ('shiba-inu', 'SHIB', 6),
    ]
    
    crypto_lines = []
    for coin_id, symbol, decimals in crypto_list:
        coin_data = global_prices['crypto'].get(coin_id, {})
        if coin_data.get('usd', 0) > 0:
            change = coin_data.get('change_24h', 0)
            emoji = get_change_emoji(change)
            price_str = to_persian_num(coin_data.get('usd', 0), decimals)
            change_str = format_percent(change)
            crypto_lines.append(f"🔸 {symbol}: ${price_str} {emoji} {change_str}")
    
    gold_change = global_prices.get('gold_change_24h', 0)
    gold_emoji = get_change_emoji(gold_change)
    
    message = f"""📊 #گزارش_بازار {date_str} - {time_str}
━━━━━━━━━━━━━━━━━━━━━━
💵 #نرخ_تتر: {to_persian_num(usdt_price)} تومان
━━━━━━━━━━━━━━━━━━━━━━
🪙 #ارزهای_دیجیتال (دلار):
{chr(10).join(crypto_lines)}
━━━━━━━━━━━━━━━━━━━━━━
🥇 #طلای_جهانی (Pax Gold):
   💰 ${to_persian_num(global_prices.get('gold_usd', 0), 2)}
   {gold_emoji} ۲۴ساعته: {format_percent(gold_change)}
━━━━━━━━━━━━━━━━━━━━━━
{config.get('ad_text', '📢')}
🔗 {config.get('ad_link', '')}
━━━━━━━━━━━━━━━━━━━━━━"""
    return message


def format_message_v2(usdt_price: float, global_prices: dict, config: dict) -> str:
    """فرمت ۲: خلاصه"""
    tz = pytz.timezone(config.get('timezone', 'Asia/Tehran'))
    now = datetime.now(tz)
    time_str = now.strftime('%H:%M')
    
    btc = global_prices['crypto'].get('bitcoin', {})
    eth = global_prices['crypto'].get('ethereum', {})
    sol = global_prices['crypto'].get('solana', {})
    
    message = f"""⚡ #بروزرسانی {time_str}
━━━━━━━━━━━━━━━━━━━━━━
💵 تتر: {to_persian_num(usdt_price)} تومان
━━━━━━━━━━━━━━━━━━━━━━
🪙 BTC: ${to_persian_num(btc.get('usd', 0), 0)} {get_change_emoji(btc.get('change_24h', 0))} {format_percent(btc.get('change_24h', 0))}
🪙 ETH: ${to_persian_num(eth.get('usd', 0), 2)} {get_change_emoji(eth.get('change_24h', 0))} {format_percent(eth.get('change_24h', 0))}
🪙 SOL: ${to_persian_num(sol.get('usd', 0), 2)} {get_change_emoji(sol.get('change_24h', 0))} {format_percent(sol.get('change_24h', 0))}
━━━━━━━━━━━━━━━━━━━━━━
🥇 طلا: ${to_persian_num(global_prices.get('gold_usd', 0), 2)} {get_change_emoji(global_prices.get('gold_change_24h', 0))}
━━━━━━━━━━━━━━━━━━━━━━
{config.get('ad_text', '📢')}
🔗 {config.get('ad_link', '')}
━━━━━━━━━━━━━━━━━━━━━━"""
    return message


def format_message_v3(usdt_price: float, global_prices: dict, config: dict) -> str:
    """فرمت ۳: کارت‌ها"""
    tz = pytz.timezone(config.get('timezone', 'Asia/Tehran'))
    now = datetime.now(tz)
    date_str = now.strftime('%Y/%m/%d')
    time_str = now.strftime('%H:%M')
    
    crypto_list = [
        ('bitcoin', 'BTC', 0),
        ('ethereum', 'ETH', 2),
        ('solana', 'SOL', 2),
        ('ripple', 'XRP', 4),
        ('cardano', 'ADA', 4),
        ('dogecoin', 'DOGE', 5),
        ('polkadot', 'DOT', 2),
        ('chainlink', 'LINK', 2),
    ]
    
    crypto_cards = []
    for coin_id, symbol, decimals in crypto_list:
        coin_data = global_prices['crypto'].get(coin_id, {})
        if coin_data.get('usd', 0) > 0:
            change = coin_data.get('change_24h', 0)
            emoji = get_change_emoji(change)
            crypto_cards.append(
                f"{symbol}: ${to_persian_num(coin_data.get('usd', 0), decimals)} {emoji} {format_percent(change)}"
            )
    
    message = f"""📈 #بازار_رمزارزها
📅 {date_str} ⏰ {time_str}
━━━━━━━━━━━━━━━━━━━━━━
💎 #کریپتو:
{chr(10).join(crypto_cards)}
━━━━━━━━━━━━━━━━━━━━━━
🥇 #طلا:
💰 Pax Gold: ${to_persian_num(global_prices.get('gold_usd', 0), 2)}
📊 24h: {get_change_emoji(global_prices.get('gold_change_24h', 0))} {format_percent(global_prices.get('gold_change_24h', 0))}
━━━━━━━━━━━━━━━━━━━━━━
💵 #تتر: {to_persian_num(usdt_price)} تومان
━━━━━━━━━━━━━━━━━━━━━━
{config.get('ad_text', '📢')}
🔗 {config.get('ad_link', '')}
━━━━━━━━━━━━━━━━━━━━━━"""
    return message


def format_message_v4(usdt_price: float, global_prices: dict, config: dict) -> str:
    """فرمت ۴: مینیمال"""
    tz = pytz.timezone(config.get('timezone', 'Asia/Tehran'))
    now = datetime.now(tz)
    time_str = now.strftime('%H:%M')
    
    btc = global_prices['crypto'].get('bitcoin', {})
    eth = global_prices['crypto'].get('ethereum', {})
    
    message = f"""🔔 قیمت‌ها - {time_str}
━━━━━━━━━━━━━━━
💵 تتر: {to_persian_num(usdt_price)} تومان
━━━━━━━━━━━━━━━
₿ {to_persian_num(btc.get('usd', 0), 0)}$ {format_percent(btc.get('change_24h', 0))}
Ξ {to_persian_num(eth.get('usd', 0), 2)}$ {format_percent(eth.get('change_24h', 0))}
━━━━━━━━━━━━━━━
🥇 طلا: {to_persian_num(global_prices.get('gold_usd', 0), 2)}$
━━━━━━━━━━━━━━━"""
    return message


def get_random_format() -> int:
    """انتخاب تصادفی فرمت"""
    return random.choice([1, 2, 3, 4])


# ═══════════════════════════════════════════════════════════
#                    توابع ارسال
# ═══════════════════════════════════════════════════════════
def send_to_bale(bale_api: BaleAPI, chat_id: str, message: str) -> bool:
    """ارسال پیام به بله"""
    result = bale_api.sendMessage(chat_id=chat_id, text=message)
    if result:
        logger.info("✅ ارسال به بله موفق")
    else:
        logger.error("❌ خطا در ارسال به بله")
    return result


def send_to_eitaa(eitaa_api: EitaaAPI, chat_id: str, message: str) -> bool:
    """ارسال پیام به ایتا"""
    result = eitaa_api.sendMessage(chat_id=chat_id, text=message)
    if result:
        logger.info("✅ ارسال به ایتا موفق")
    else:
        logger.error("❌ خطا در ارسال به ایتا")
    return result


def notify_admin_bale(bale_api: BaleAPI, admin_id: int, status: str, details: str = "") -> None:
    """اطلاع‌رسانی به ادمین در بله"""
    status_emoji = {'success': '✅', 'error': '❌', 'warning': '⚠️'}
    emoji = status_emoji.get(status, '📌')
    
    tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(tz)
    
    message = f"""{emoji} گزارش ربات
📊 وضعیت: {status}
📝 جزئیات: {details}
🕐 {now.strftime('%Y/%m/%d %H:%M:%S')}"""
    
    bale_api.sendMessage(chat_id=admin_id, text=message)


def notify_admin_eitaa(eitaa_api: EitaaAPI, admin_id: int, status: str, details: str = "") -> None:
    """اطلاع‌رسانی به ادمین در ایتا"""
    status_emoji = {'success': '✅', 'error': '❌', 'warning': '⚠️'}
    emoji = status_emoji.get(status, '📌')
    
    tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(tz)
    
    message = f"""{emoji} گزارش ربات ایتا
📊 وضعیت: {status}
📝 جزئیات: {details}
🕐 {now.strftime('%Y/%m/%d %H:%M:%S')}"""
    
    eitaa_api.sendMessage(chat_id=admin_id, text=message)


# ═══════════════════════════════════════════════════════════
#                    تابع اصلی
# ═══════════════════════════════════════════════════════════
def main():
    """تابع اصلی - یک بار استعلام، ارسال به هر دو"""
    
    config = load_config()
    
    # ایجاد API ها
    bale_api = BaleAPI(config['bot_token'])
    eitaa_api = EitaaAPI(config['eitaa_token'])
    
    logger.info("🤖 ربات یکپارچه شروع به کار کرد...")
    
    # بررسی اتصال هر دو API
    bale_ok = bool(bale_api.getMe())
    eitaa_ok = bool(eitaa_api.getMe())
    
    logger.info(f"🔗 بله: {'متصل' if bale_ok else 'خطا'}")
    logger.info(f"🔗 ایتا: {'متصل' if eitaa_ok else 'خطا'}")
    
    if not bale_ok and not eitaa_ok:
        logger.error("هیچ API ای متصل نیست!")
        return
    
    try:
        # ═══════════════════════════════════════════════════════════
        #                    مرحله ۱: دریافت قیمت تتر (فقط یک بار)
        # ═══════════════════════════════════════════════════════════
        usdt_price = get_usdt_price_from_nobitex()
        
        if not usdt_price:
            logger.error("قیمت تتر دریافت نشد!")
            if bale_ok:
                notify_admin_bale(bale_api, config['admin_id'], 'error', 'خطا در دریافت قیمت تتر')
            if eitaa_ok:
                notify_admin_eitaa(eitaa_api, config['admin_id'], 'error', 'خطا در دریافت قیمت تتر')
            return
        
        # ═══════════════════════════════════════════════════════════
        #                    مرحله ۲: دریافت قیمت‌های جهانی (فقط یک بار)
        # ═══════════════════════════════════════════════════════════
        global_prices = get_global_prices()
        
        # ═══════════════════════════════════════════════════════════
        #                    مرحله ۳: ساخت پیام (فقط یک بار)
        # ═══════════════════════════════════════════════════════════
        format_type = get_random_format()
        
        if format_type == 1:
            message = format_message_v1(usdt_price, global_prices, config)
        elif format_type == 2:
            message = format_message_v2(usdt_price, global_prices, config)
        elif format_type == 3:
            message = format_message_v3(usdt_price, global_prices, config)
        else:
            message = format_message_v4(usdt_price, global_prices, config)
        
        logger.info(f"📝 پیام آماده شد (فرمت {format_type})")
        
        # ═══════════════════════════════════════════════════════════
        #                    مرحله ۴: ارسال به هر دو پلتفرم
        # ═══════════════════════════════════════════════════════════
        results = {}
        
        # ارسال به بله
        if bale_ok:
            bale_result = send_to_bale(bale_api, config['channel_id'], message)
            results['bale'] = bale_result
        else:
            results['bale'] = False
        
        # ارسال به ایتا
        if eitaa_ok:
            eitaa_result = send_to_eitaa(eitaa_api, config['eitaa_channel_id'], message)
            results['eitaa'] = eitaa_result
        else:
            results['eitaa'] = False
        
        # ═══════════════════════════════════════════════════════════
        #                    مرحله ۵: گزارش نهایی
        # ═══════════════════════════════════════════════════════════
        bale_status = "✅" if results['bale'] else "❌"
        eitaa_status = "✅" if results['eitaa'] else "❌"
        
        summary = f"بله: {bale_status} | ایتا: {eitaa_status} | فرمت: {format_type} | تتر: {usdt_price:,.0f}"
        logger.info(f"📊 {summary}")
        
        # اطلاع‌رسانی به ادمین
        if bale_ok:
            notify_admin_bale(bale_api, config['admin_id'], 'success', summary)
        if eitaa_ok:
            notify_admin_eitaa(eitaa_api, config['admin_id'], 'success', summary)
        
    except Exception as e:
        logger.error(f"خطای کلی: {e}")
        if bale_ok:
            notify_admin_bale(bale_api, config['admin_id'], 'error', str(e))
        if eitaa_ok:
            notify_admin_eitaa(eitaa_api, config['admin_id'], 'error', str(e))


if __name__ == '__main__':
    main()
