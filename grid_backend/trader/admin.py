from django.contrib import admin
from .models import GridPlan, GridRecord


@admin.register(GridPlan)
class GridPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'stock_code', 'stock_name', 'base_price', 'total_funds', 'created_at']
    list_filter = ['created_at']
    search_fields = ['stock_code', 'stock_name']


@admin.register(GridRecord)
class GridRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'plan', 'part_index', 'status',
        'target_buy_price', 'target_sell_price', 'volume',
        'actual_buy_price', 'buy_time', 'actual_sell_price', 'sell_time', 'profit',
    ]
    list_filter = ['status', 'plan']
    search_fields = ['plan__stock_code', 'plan__stock_name']
