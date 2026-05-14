from django.core.management.base import BaseCommand
import datetime
from trader.tasks import scan_stock_prices

class Command(BaseCommand):
    help = '手动测试发送企业微信股价监控提醒(调用统一的Task)'

    def handle(self, *args, **options):
        self.stdout.write(f"[{datetime.datetime.now()}] 开始调用统一任务 scan_stock_prices 执行股价监控测试推送...")
        
        try:
            scan_stock_prices()
            self.stdout.write(self.style.SUCCESS("测试推送调用完毕！请检查日志及企业微信接收情况。"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"执行异常: {e}"))
