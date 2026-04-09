from django.apps import AppConfig
import threading
import time
import datetime
import requests


def check_stock_suitability(symbol, return_details=False):
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

        passed = cond1 and cond2 and cond3 and cond4 and bollPassed and macdPassed
        if return_details:
            return passed, {
                "price": currentPx,
                "ma30": ma30,
                "ma30_slope": ma30_slope,
                "atr_ratio": atrRatio,
                "dispersion": ma_dispersion,
                "boll_passed": bollPassed,
                "macd_passed": macdPassed
            }
        return passed
    except Exception as e:
        print(f"Error evaluating {symbol}: {e}")
        if return_details:
            return False, {}
        return False

def run_wechat_scheduler():
    from .models import UserProfile, StockWatchlist
    import tushare as ts
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    def send_wechat_msg(webhook_url, content):
        if not webhook_url: return
        msg = {
            "msgtype": "text",
            "text": {"content": content}
        }
        try:
            requests.post(webhook_url, json=msg, timeout=5)
            logger.info(f"Successfully sent wechat msg to {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to send wechat msg: {e}")
            
    last_run_date = None
    while True:
        now = datetime.datetime.now()
        # Run at 7:00 AM once a day using last_run_date checking to prevent missing minute zero
        if now.hour == 7 and now.date() != last_run_date:
            logger.info("Starting scheduled daily WeChat push at 7:00 AM")
            last_run_date = now.date()
                
            profiles = UserProfile.objects.exclude(wechat_webhook__isnull=True).exclude(wechat_webhook='')
            if profiles.exists():
                token = getattr(settings, 'TUSHARE_TOKEN', '')
                if token:
                    ts.set_token(token)
                
                # Fetch suitable grid stocks for each user (for simplicity, sending their watchlists)
                for profile in profiles:
                    webhook = profile.wechat_webhook
                    watchlists = StockWatchlist.objects.filter(user=profile.user)
                    if not watchlists.exists():
                        logger.info(f"User {profile.user.username} has no watchlist, skipping.")
                        continue
                    
                    codes = [v.stock_code for v in watchlists]
                    logger.info(f"Processing user {profile.user.username} with watchlist: {codes}")
                    
                    try:
                        # 1. Analyse Market Indices (Only Shanghai Index)
                        market_analysis_lines = ["【大盘(上证)网格适合度分析】"]
                        sz_code = 'sh000001'
                        passed, details = check_stock_suitability(sz_code, return_details=True)
                        if details:
                            status_icon = "✅ 适合网格" if passed else "❌ 不太适合"
                            market_analysis_lines.append(f"结果: {status_icon}")
                            market_analysis_lines.append(
                                f"详情: 收盘: {details['price']:.2f}, "
                                f"MA30: {details['ma30']:.2f} (斜率: {details['ma30_slope']:.2f}%), "
                                f"ATR比例: {details['atr_ratio']:.2f}%, "
                                f"均线散度: {details['dispersion']:.2f}%, "
                                f"MACD: {'通过' if details['macd_passed'] else '不通过'}, "
                                f"BOLL: {'通过' if details['boll_passed'] else '不通过'}"
                            )
                        else:
                            market_analysis_lines.append(f"- 上证指数分析失败")
                                
                        # 2. Analyse user's watchlist
                        df = ts.get_realtime_quotes(codes)
                        msg_lines = ["\n【每日自选股网格推荐 (7:00)】"]
                        recommended_count = 0
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
                                recommended_count += 1
                            else:
                                pass # skip the unsuited
                            
                        if recommended_count == 0:
                            msg_lines.append("- 当前自选股中暂无完美适合网格交易的股票。")
                            
                        final_msg = "\n".join(market_analysis_lines + msg_lines)
                        send_wechat_msg(webhook, final_msg)
                    except Exception as e:
                        logger.error(f"Error fetching quotes or analysing: {e}")
            else:
                logger.info("No profiles with wechat_webhook found.")
                
        # sleep 60 seconds
        time.sleep(60)


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
