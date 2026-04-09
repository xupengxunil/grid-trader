from django.core.management.base import BaseCommand
import datetime
import requests
import tushare as ts
from django.conf import settings
from trader.models import UserProfile, StockWatchlist

class Command(BaseCommand):
    help = '手动测试发送企业微信网格交易提醒'

    def send_wechat_msg(self, webhook_url, content):
        if not webhook_url: return
        msg = {
            "msgtype": "text",
            "text": {"content": content}
        }
        try:
            requests.post(webhook_url, json=msg, timeout=5)
            self.stdout.write(self.style.SUCCESS(f"成功发送消息到: {webhook_url}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"发送消息失败: {e}"))

    def handle(self, *args, **options):
        self.stdout.write(f"[{datetime.datetime.now()}] 开始执行测试推送...")
        
        profiles = UserProfile.objects.exclude(wechat_webhook__isnull=True).exclude(wechat_webhook='')
        if not profiles.exists():
            self.stdout.write(self.style.WARNING("没有找到配置了企业微信Webhook的用户。"))
            return

        token = getattr(settings, 'TUSHARE_TOKEN', '')
        if token:
            ts.set_token(token)
            
        for profile in profiles:
            webhook = profile.wechat_webhook
            watchlists = StockWatchlist.objects.filter(user=profile.user)
            if not watchlists.exists():
                self.stdout.write(self.style.WARNING(f"用户 {profile.user.username}没有自选股配置，跳过推送。"))
                continue
            
            codes = [v.stock_code for v in watchlists]
            
            try:
                self.stdout.write(f"拉取行情: {codes}")
                df = ts.get_realtime_quotes(codes)
                if df is None or df.empty:
                    self.stdout.write(self.style.WARNING(f"未能获取到 {codes} 的行情数据。"))
                    continue

                msg_lines = ["\n【测试】每日自选股网格推荐 (7:00)"]
                recommended_count = 0
                for _, row in df.iterrows():
                    from trader.apps import check_stock_suitability
                    
                    if _ == 0: # Only run market analysis once
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
                    
                    raw_code = str(row['code'])
                    original_code = None
                    for c in codes:
                        if c.endswith(raw_code):
                            original_code = c
                            break
                    if not original_code:
                        original_code = f"sh{raw_code}" if raw_code.startswith('6') else f"sz{raw_code}"

                    if check_stock_suitability(original_code):
                        msg_lines.append(f"- {row['name']} ({original_code}) 当前价: {row['price']} ✅ 完美适合网格")
                        recommended_count += 1
                        
                if recommended_count == 0:
                    msg_lines.append("- 当前自选股中暂无完美适合网格交易的股票。")
                    
                final_msg = "\n".join(market_analysis_lines + msg_lines)
                print(final_msg)
                    
                self.send_wechat_msg(webhook, final_msg)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"获取行情出错: {e}"))

        self.stdout.write(self.style.SUCCESS("测试推送执行完毕！"))