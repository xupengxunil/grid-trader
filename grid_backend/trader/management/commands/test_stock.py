from django.core.management.base import BaseCommand
from trader.apps import check_stock_suitability
from django.conf import settings
import tushare as ts

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('symbol', type=str)

    def handle(self, *args, **options):
        symbol = options['symbol']
        token = getattr(settings, 'TUSHARE_TOKEN', '')
        if token:
            ts.set_token(token)
            
        self.stdout.write(f"Testing {symbol}...")
        res = check_stock_suitability(symbol)
        self.stdout.write(f"Result: {res}")
