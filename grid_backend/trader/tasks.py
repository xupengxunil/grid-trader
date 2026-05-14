import requests
from .models import StockPriceMonitor
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def fetch_sina_quote(stock_code):
    # Determine sina prefix
    prefix = 'sh' if stock_code.startswith('6') else 'sz'
    full_code = f'{prefix}{stock_code}'
    
    url = f'http://hq.sinajs.cn/list={full_code}'
    try:
        response = requests.get(url, headers={'Referer': 'http://finance.sina.com.cn'}, timeout=10)
        response.encoding = 'gbk'
        data_text = response.text
        if '=' in data_text:
            content = data_text.split('=')[1].strip().strip('";')
            if content:
                fields = content.split(',')
                current_price = float(fields[3])
                return current_price
    except Exception as e:
        logger.error(f"Error fetching quote for {stock_code}: {e}")
    return None

def send_wechat_webhook(webhook_url, content):
    if not webhook_url:
        return
    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Error sending wechat message: {e}")

def scan_stock_prices():
    from trader.models import StockPriceMonitor
    monitors = StockPriceMonitor.objects.filter(is_active=True).select_related('user', 'user__profile')
    if not monitors.exists():
        return

    # Group by stock_code to save API requests
    grouped_monitors = {}
    for m in monitors:
        grouped_monitors.setdefault(m.stock_code, []).append(m)

    user_messages = {}

    for stock_code, group in grouped_monitors.items():
        if stock_code.startswith('sh') or stock_code.startswith('sz'):
            full_code = stock_code
        else:
            prefix = 'sh' if stock_code.startswith('6') or stock_code.startswith('5') else 'sz'
            full_code = f'{prefix}{stock_code}'
            
        url = f'http://hq.sinajs.cn/list={full_code}'
        try:
            response = requests.get(url, headers={'Referer': 'http://finance.sina.com.cn'}, timeout=10)
            response.encoding = 'gbk'
            data_text = response.text
            if '=' in data_text:
                content = data_text.split('=')[1].strip().strip('";')
                if content:
                    fields = content.split(',')
                    current_price = float(fields[3])
                else:
                    current_price = None
            else:
                current_price = None
        except Exception as e:
            logger.error(f"Error fetching quote for {stock_code}: {e}")
            current_price = None

        if current_price is None:
            continue
            
        for monitor in group:
            alert = False
            if monitor.condition == 'above' and current_price >= monitor.target_price:
                alert = True
            elif monitor.condition == 'below' and current_price <= monitor.target_price:
                alert = True
                
            msg = f"{monitor.stock_name} 目标价{monitor.target_price} 当前价格{current_price}"
            if alert:
                msg = f"【触发告警】{msg}"
            else:
                msg = f"【未触发告警】{msg}"
                
            try:
                webhook_url = monitor.user.profile.wechat_webhook
                if webhook_url:
                    if webhook_url not in user_messages:
                        user_messages[webhook_url] = []
                    user_messages[webhook_url].append(msg)
            except Exception as e:
                logger.error(f'Could not extract webhook for user {monitor.user.username}: {e}')

    for webhook_url, msgs in user_messages.items():
        if msgs:
            final_content = "【股价监控日常推送】\n" + "\n".join(msgs)
            send_wechat_webhook(webhook_url, final_content)
