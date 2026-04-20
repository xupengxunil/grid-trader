import datetime
import requests
import tushare as ts
import numpy as np
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from trader.models import UserProfile, StockWatchlist

def calculate_macd(close_prices):
    ema12 = close_prices[0]
    ema26 = close_prices[0]
    dea = 0
    macd = []
    
    for i, c in enumerate(close_prices):
        if i == 0:
            macd.append({'dif': 0, 'dea': 0, 'hist': 0})
        else:
            ema12 = c * (2/13) + ema12 * (11/13)
            ema26 = c * (2/27) + ema26 * (25/27)
            dif = ema12 - ema26
            dea = dif * (2/10) + dea * (8/10)
            hist = (dif - dea) * 2
            macd.append({'dif': dif, 'dea': dea, 'hist': hist})
    return macd

def calculate_kdj(df):
    kdj = []
    k, d = 50, 50
    period = 9
    
    for i in range(len(df)):
        if i < period - 1:
            kdj.append({'k': 50, 'd': 50, 'j': 50})
            continue
        recent = df.iloc[i - period + 1 : i + 1]
        low_px = recent['low'].min()
        high_px = recent['high'].max()
        c = df.iloc[i]['close']
        
        rsv = 50
        if high_px != low_px:
            rsv = ((c - low_px) / (high_px - low_px)) * 100
            
        k = (2/3) * k + (1/3) * rsv
        d = (2/3) * d + (1/3) * k
        j = 3 * k - 2 * d
        kdj.append({'k': k, 'd': d, 'j': j})
    return kdj

def calculate_boll(close_prices):
    boll = []
    period = 20
    for i in range(len(close_prices)):
        if i < period - 1:
            boll.append({'mb': None, 'up': None, 'dn': None})
            continue
        recent = close_prices[i - period + 1 : i + 1]
        mb = np.mean(recent)
        md = np.std(recent, ddof=0)
        boll.append({
            'mb': mb,
            'up': mb + 2 * md,
            'dn': mb - 2 * md
        })
    return boll

def analyze_signals(df):
    if len(df) < 20: 
        return 0, []
        
    close_prices = df['close'].values
    macd_data = calculate_macd(close_prices)
    kdj_data = calculate_kdj(df)
    boll_data = calculate_boll(close_prices)

    last_idx = len(df) - 1
    prev_idx = last_idx - 1
    current_price = close_prices[last_idx]

    last_macd = macd_data[last_idx]
    prev_macd = macd_data[prev_idx]
    
    score = 0
    tags = []
    
    if prev_macd['dif'] <= prev_macd['dea'] and last_macd['dif'] > last_macd['dea']:
        tags.append('MACD金叉')
        score += 2
    elif last_macd['hist'] < 0 and last_macd['hist'] > prev_macd['hist']:
        tags.append('MACD绿缩短')
        score += 1
    elif prev_macd['dif'] >= prev_macd['dea'] and last_macd['dif'] < last_macd['dea']:
        tags.append('MACD死叉')
        score -= 2

    last_kdj = kdj_data[last_idx]
    if last_kdj['j'] < 0 or (last_kdj['k'] < 20 and last_kdj['d'] < 20):
        tags.append('KDJ超卖')
        score += 2
    elif last_kdj['j'] > 100 or (last_kdj['k'] > 80 and last_kdj['d'] > 80):
        tags.append('KDJ超买')
        score -= 2

    last_boll = boll_data[last_idx]
    if last_boll['dn'] is not None and current_price <= last_boll['dn'] * 1.01:
        tags.append('触及布林下轨')
        score += 2
    elif last_boll['up'] is not None and current_price >= last_boll['up'] * 0.99:
        tags.append('触及布林上轨')
        score -= 1

    return score, tags


class Command(BaseCommand):
    help = 'Scan active users watchlists for opportunities based on MACD, KDJ, and BOLL.'

    def send_wechat_msg(self, webhook_url, content):
        if not webhook_url: return
        msg = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
        try:
            requests.post(webhook_url, json=msg, timeout=5)
            self.stdout.write(self.style.SUCCESS(f"成功发送消息到: {webhook_url}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"发送消息失败: {e}"))

    def get_market_analysis(self):
        try:
            df = ts.pro_bar(ts_code='000001.SH', asset='I', adj='qfq', start_date='', end_date='')
            if df is None or df.empty:
                return "大盘数据获取失败。"
            
            df = df.head(100).iloc[::-1].reset_index(drop=True)
            closes = df['close'].values
            current = closes[-1]
            
            ma5 = np.mean(closes[-5:]) if len(closes) >= 5 else current
            ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else current
            ma60 = np.mean(closes[-60:]) if len(closes) >= 60 else current
            
            recent_10 = closes[-10:] if len(closes) >= 10 else closes
            volatility = (np.max(recent_10) - np.min(recent_10)) / current * 100
            
            advice = f"### 📈 大盘综合分析 (上证: {current:.2f})\n"
            advice += f"> 短期趋势(MA5): <font color='{'warning' if current > ma5 else 'info'}'>{'多头占优' if current > ma5 else '空头压制'}</font>\n"
            advice += f"> 中期趋势(MA20): <font color='{'warning' if current > ma20 else 'info'}'>{'上升通道' if current > ma20 else '下降通道'}</font>\n"
            advice += f"> 长期趋势(MA60): <font color='{'warning' if current > ma60 else 'info'}'>{'多头牛市' if current > ma60 else '长线熊市'}</font>\n"
            advice += f"> 近期波动率: {volatility:.2f}%\n>\n"
            
            if current < ma20 * 0.98 and current < ma60:
                advice += "> **结论：绝佳低位建仓期**\n> 大盘处于下行探底或稳固底部区间，是分批建仓、布置大网格防守的极佳时机。"
            elif volatility > 4 and ma20 * 0.98 <= current <= ma20 * 1.02:
                advice += "> **结论：黄金震荡期**\n> 大盘围绕核心均线宽幅震荡，极易触发量化策略高频买卖。"
            elif current > ma20 * 1.02 and current > ma60 * 1.02:
                advice += "> **结论：高位防踏空期**\n> 大盘处于单边发散阶段，请注意防范踏空风险，适当保留底仓。"
            else:
                advice += "> **结论：正常结构性阶段**\n> 大盘趋势收敛，量化策略正常运转，取决于个股独立形态。"
                
            return advice
        except Exception as e:
            return f"> 大盘综合分析获取失败: {e}"

    def handle(self, *args, **options):
        self.stdout.write(f"[{datetime.datetime.now()}] 开始执行自选股机会扫描...")
        
        # 只查找已审批通过且配置了Webhook的用户
        profiles = UserProfile.objects.filter(
            status=UserProfile.STATUS_APPROVED
        ).exclude(wechat_webhook__isnull=True).exclude(wechat_webhook='')
        
        if not profiles.exists():
            self.stdout.write(self.style.WARNING("没有找到配置了企业微信Webhook且审批通过的用户。"))
            return

        token = getattr(settings, 'TUSHARE_TOKEN', '')
        if token:
            ts.set_token(token)

        market_analysis_text = self.get_market_analysis()

        all_stocks = {}
        user_stocks = {}

        for profile in profiles:
            watchlists = StockWatchlist.objects.filter(user=profile.user)
            if not watchlists.exists():
                continue
            
            user_stocks[profile] = watchlists
            for w in watchlists:
                all_stocks[w.stock_code] = w.stock_name
        
        if not all_stocks:
            self.stdout.write("所有用户都没有自选股。")
            return

        self.stdout.write(f"需要扫描的唯一股票数量: {len(all_stocks)}")
        
        stock_results = {}
        
        for code, name in all_stocks.items():
            time.sleep(0.3)  # tushare限流
            ts_code = code
            if code.lower().startswith('sh'):
                ts_code = f"{code[2:]}.SH"
            elif code.lower().startswith('sz'):
                ts_code = f"{code[2:]}.SZ"
                
            asset_type = 'E'
            if ts_code in ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000016.SH']:
                asset_type = 'I'
                
            try:
                df = ts.pro_bar(ts_code=ts_code, asset=asset_type, adj='qfq', start_date='', end_date='')
                if df is None or df.empty:
                    self.stdout.write(self.style.WARNING(f"未能获取到 {code} 的行情数据。"))
                    continue
                    
                df = df.head(100)
                df = df.iloc[::-1].reset_index(drop=True)
                
                score, tags = analyze_signals(df)
                if score >= 2:
                    stock_results[code] = {'score': score, 'tags': tags, 'name': name}
                    self.stdout.write(self.style.SUCCESS(f"扫描到机会: {name} ({code}) - 得分: {score} - 信号: {', '.join(tags)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"处理 {code} 时出错: {e}"))

        # 给每个用户分组推送
        for profile, wt_qs in user_stocks.items():
            opps = []
            for w in wt_qs:
                if w.stock_code in stock_results:
                    opp = stock_results[w.stock_code]
                    opps.append({'code': w.stock_code, **opp})
                    
            content = f"{market_analysis_text}\n\n---\n### 💡 自选股交易机会扫描\n\n"
            if opps:
                for op in opps:
                    tags_str = ', '.join(op['tags'])
                    content += f"- **{op['name']}** ({op['code']}): 得分 `{op['score']}` 分 - 信号: <font color='warning'>{tags_str}</font>\n"
            else:
                content += "> 暂无高分共振机会，您的自选股目前技术面相对平稳。\n"
                
            self.send_wechat_msg(profile.wechat_webhook, content)

        self.stdout.write(self.style.SUCCESS("扫描执行完毕。"))