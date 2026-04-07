from django.apps import AppConfig
import threading
import time
import datetime
import requests


def check_stock_suitability(symbol):
    try:
        import tushare as ts
        import numpy as np
        
        ts_code = symbol
        if symbol.lower().startswith('sh'):
            ts_code = f"{symbol[2:]}.SH"
        elif symbol.lower().startswith('sz'):
            ts_code = f"{symbol[2:]}.SZ"
            
        pro = ts.pro_api()
        asset_type = 'E'
        if ts_code in ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000016.SH']:
            asset_type = 'I'
            
        df = ts.pro_bar(ts_code=ts_code, asset=asset_type, adj='qfq', start_date='', end_date='')
        if df is None or df.empty:
            return False
            
        df = df.head(100)
        if len(df) < 40:  # Require enough history for MA30 past slope
            return False
            
        # Reverse to have oldest first to calculate EMA and MA
        df = df.iloc[::-1].reset_index(drop=True)
        
        close_prices = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        
        currentPx = close_prices[-1]
        
        ma5 = np.mean(close_prices[-5:])
        ma10 = np.mean(close_prices[-10:])
        ma30 = np.mean(close_prices[-30:])
        
        pastClose30 = close_prices[-40:-10]
        ma30_past = np.mean(pastClose30) if len(pastClose30) > 0 else ma30
        ma30_slope = ((ma30 - ma30_past) / ma30_past) * 100 if ma30_past > 0 else 0
        
        ma_max = max(ma5, ma10, ma30)
        ma_min = min(ma5, ma10, ma30)
        ma_dispersion = ((ma_max - ma_min) / ma_min) * 100 if ma_min > 0 else 0

        # ATR
        atrRange = 14
        trSum = 0
        validDays = 0
        for i in range(1, len(df)):
            if i >= len(df) - atrRange:
                todayHigh = highs[i]
                todayLow = lows[i]
                preClose = close_prices[i - 1]
                tr1 = todayHigh - todayLow
                tr2 = abs(todayHigh - preClose)
                tr3 = abs(todayLow - preClose)
                trSum += max(tr1, tr2, tr3)
                validDays += 1
                
        atr = trSum / validDays if validDays > 0 else 0
        atrRatio = (atr / currentPx) * 100 if currentPx > 0 else 0
        
        # MACD
        ema12 = close_prices[0]
        ema26 = close_prices[0]
        dea = 0
        macdDif = []
        macdDea = []
        macdHist = []
        
        for i in range(len(close_prices)):
            c = close_prices[i]
            if i == 0:
                macdDif.append(0)
                macdDea.append(0)
                macdHist.append(0)
            else:
                ema12 = c * (2/13) + ema12 * (11/13)
                ema26 = c * (2/27) + ema26 * (25/27)
                dif = ema12 - ema26
                dea = dif * (2/10) + dea * (8/10)
                hist = (dif - dea) * 2
                macdDif.append(dif)
                macdDea.append(dea)
                macdHist.append(hist)
                
        lastDif, lastDea, lastHist = macdDif[-1], macdDea[-1], macdHist[-1]
        prevHist = macdHist[-2] if len(macdHist) > 1 else 0
        
        macdPassed = True
        if lastDif < lastDea and lastHist < prevHist and lastHist < 0:
            macdPassed = False
        elif lastDif < 0 and lastDea > 0 and lastDif < lastDea:
            macdPassed = False
            
        # BOLL
        bollPassed = True
        if len(close_prices) >= 20:
            recent20 = close_prices[-20:]
            bolMB = np.mean(recent20)
            bolMD = np.std(recent20, ddof=0)
            bolUP = bolMB + 2 * bolMD
            bolDN = bolMB - 2 * bolMD
            
            if (bolUP - bolDN) != 0:
                bollPosition = (currentPx - bolDN) / (bolUP - bolDN)
                if bollPosition > 0.9:
                    bollPassed = False

        cond1 = currentPx > ma30 * 0.95 and ma30_slope > -2.0
        cond2 = atrRatio > 1.5
        cond3 = currentPx <= ma30 * 1.15
        cond4 = ma_dispersion < 5.0
        
        print(f"[{symbol}] DEBUG: cond1({cond1}) cond2({cond2}) cond3({cond3}) cond4({cond4}) boll({bollPassed}) macd({macdPassed}) | Px:{currentPx} ma30:{ma30} ma30slp:{ma30_slope} atr:{atrRatio} disp:{ma_dispersion}")

        return cond1 and cond2 and cond3 and cond4 and bollPassed and macdPassed
    except Exception as e:
        print(f"Error evaluating {symbol}: {e}")
        return False

def run_wechat_scheduler():
    from .models import UserProfile, StockWatchlist
    import tushare as ts
    from django.conf import settings
    
    def send_wechat_msg(webhook_url, content):
        if not webhook_url: return
        msg = {
            "msgtype": "text",
            "text": {"content": content}
        }
        try:
            requests.post(webhook_url, json=msg, timeout=5)
        except Exception as e:
            print("Failed to send wechat msg:", e)
            
    while True:
        now = datetime.datetime.now()
        # Run at 7:00 AM
        if now.hour == 7 and now.minute == 0:
            profiles = UserProfile.objects.exclude(wechat_webhook__isnull=True).exclude(wechat_webhook='')
            if profiles.exists():
                token = getattr(settings, 'TUSHARE_TOKEN', '')
                if token:
                    ts.set_token(token)
                
                # Fetch suitable grid stocks for each user (for simplicity, sending their watchlists)
                for profile in profiles:
                    webhook = profile.wechat_webhook
                    watchlists = StockWatchlist.objects.filter(user=profile.user)
                    if not watchlists.exists(): continue
                    
                    codes = [v.stock_code for v in watchlists]
                    
                    try:
                        df = ts.get_realtime_quotes(codes)
                        msg_lines = ["【每日网格股票推荐 (7:00)】"]
                        for _, row in df.iterrows():
                            raw_code = str(row['code'])
                            
                            # Tushare get_realtime_quotes usually returns numeric codes. Re-add prefix SH/SZ based on watchlists
                            original_code = None
                            for c in codes:
                                if c.endswith(raw_code):
                                    original_code = c
                                    break
                            
                            if not original_code:
                                original_code = f"sh{raw_code}" if raw_code.startswith('6') else f"sz{raw_code}"
                                
                            # Replicate the stock analysis logic from vue
                            if check_stock_suitability(original_code):
                                msg_lines.append(f"- {row['name']} ({original_code}) 当前价: {row['price']} ✅ 完美适合网格")
                            else:
                                pass # skip the unsuited
                            
                        if len(msg_lines) > 1:
                            send_wechat_msg(webhook, "\n".join(msg_lines))
                    except Exception as e:
                        print("Error fetching quotes:", e)
                        
            # Sleep until 7:01 to avoid multiple runs
            time.sleep(60)
        else:
            time.sleep(30)


class TraderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trader'
    
    def ready(self):
        # Prevent running twice in dev mode with auto-reloader
        import os
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
        thread = threading.Thread(target=run_wechat_scheduler, daemon=True)
        thread.start()
    verbose_name = '网格交易'
