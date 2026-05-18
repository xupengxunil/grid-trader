import datetime
import requests
import tushare as ts
from django.core.management.base import BaseCommand
from django.conf import settings
from trader.models import UserProfile, StockWatchlist
import numpy as np
import time

def send_wechat_msg(webhook_url, content):
    if not webhook_url: return
    msg = {
        "msgtype": "text",
        "text": {"content": content}
    }
    try:
        requests.post(webhook_url, json=msg, timeout=5)
    except Exception as e:
        print(f"Failed to send wechat msg: {e}")

class Command(BaseCommand):
    help = 'Scan watchlist for long-term opportunities (MA200 / Valuation) and push to WeChat'

    def handle(self, *args, **options):
        profiles = UserProfile.objects.exclude(wechat_webhook__isnull=True).exclude(wechat_webhook='')
        if not profiles.exists():
            return
            
        token = getattr(settings, 'TUSHARE_TOKEN', '')
        if token:
            ts.set_token(token)
            
        pro = ts.pro_api()

        for profile in profiles:
            webhook = profile.wechat_webhook
            watchlists = StockWatchlist.objects.filter(user=profile.user)
            if not watchlists.exists():
                continue
                
            codes_and_names = [(v.stock_code, v.stock_name) for v in watchlists]
            msg_lines = ["【自选股长线诊断扫描】"]
            found_opportunities = False
            
            for code, name in codes_and_names:
                ts_code = code
                if code.startswith('sh'): ts_code = f"{code[2:]}.SH"
                elif code.startswith('sz'): ts_code = f"{code[2:]}.SZ"
                elif code.startswith('bj'): ts_code = f"{code[2:]}.BJ"

                asset_type = 'E'
                if ts_code in ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000016.SH']:
                    asset_type = 'I'
                
                try:
                    # K-line data for MA200
                    df = ts.pro_bar(ts_code=ts_code, asset=asset_type, adj='qfq', start_date='', end_date='')
                    time.sleep(0.3)
                    
                    if df is not None and len(df) > 0:
                        df = df.head(250).iloc[::-1].reset_index(drop=True)
                        close_prices = df['close'].values
                        current_price = close_prices[-1]
                        
                        ma200 = None
                        bias_200 = None
                        if len(close_prices) >= 200:
                            ma200 = np.mean(close_prices[-200:])
                            bias_200 = ((current_price - ma200) / ma200) * 100
                            
                        # Daily basic for Valuation
                        basic_df = pro.daily_basic(ts_code=ts_code, fields='trade_date,pe_ttm,pb')
                        time.sleep(0.3)
                        
                        pe_percentile = None
                        pb_percentile = None
                        
                        if basic_df is not None and len(basic_df) > 0:
                            basic_df = basic_df.head(250)
                            pe_list = basic_df['pe_ttm'].dropna().values
                            pb_list = basic_df['pb'].dropna().values
                            
                            if len(pe_list) > 0:
                                current_pe = pe_list[0]
                                min_pe = np.min(pe_list)
                                max_pe = np.max(pe_list)
                                pe_percentile = ((current_pe - min_pe) / (max_pe - min_pe)) * 100 if max_pe > min_pe else 50
                                
                            if len(pb_list) > 0:
                                current_pb = pb_list[0]
                                min_pb = np.min(pb_list)
                                max_pb = np.max(pb_list)
                                pb_percentile = ((current_pb - min_pb) / (max_pb - min_pb)) * 100 if max_pb > min_pb else 50

                        # Determine if this is an opportunity
                        opp_tags = []
                        if bias_200 is not None and abs(bias_200) <= 5:
                            opp_tags.append(f"接近200均线(乖离{bias_200:.2f}%)")
                        if bias_200 is not None and bias_200 < -15:
                            opp_tags.append(f"严重超跌(乖离{bias_200:.2f}%)")
                        if pe_percentile is not None and pe_percentile < 30:
                            opp_tags.append(f"PE低估(历史前{pe_percentile:.1f}%)")
                        if pb_percentile is not None and pb_percentile < 30:
                            opp_tags.append(f"PB低估(历史前{pb_percentile:.1f}%)")
                            
                        if len(opp_tags) > 0:
                            found_opportunities = True
                            msg_lines.append(f"- 【{name} ({code})】: {' | '.join(opp_tags)}")
                except Exception as e:
                    print(f"Error analyzing long term for {name} ({code}): {e}")
                    
            if not found_opportunities:
                msg_lines.append("- 目前自选股中暂无长线极佳建仓/低估机会。")
                
            final_msg = "\n".join(msg_lines)
            send_wechat_msg(webhook, final_msg)
