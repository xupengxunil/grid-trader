from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Extended profile for each registered user, tracking approval status."""
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_PENDING, '待审批'),
        (STATUS_APPROVED, '已通过'),
        (STATUS_REJECTED, '已拒绝'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='用户',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='审批状态',
    )   

    wechat_webhook = models.URLField(max_length=500, blank=True, null=True, verbose_name='企业微信机器人地址')    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='注册时间') 

    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f'{self.user.username} [{self.get_status_display()}]'


class GridPlan(models.Model):
    """One grid trading plan per stock."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plans',
        verbose_name='所属用户',
        null=True,
        blank=True,
    )
    stock_code = models.CharField(max_length=10, verbose_name='股票代码')
    stock_name = models.CharField(max_length=50, verbose_name='股票名称')
    base_price = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='建仓基准价')
    total_funds = models.DecimalField(
        max_digits=12, decimal_places=2, default=50000.00, verbose_name='总资金(元)'
    )
    part_count = models.IntegerField(default=5, verbose_name='网格档数')
    grid_ratio = models.DecimalField(
        max_digits=6, decimal_places=4, default=0.03, verbose_name='网格大小'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'grid_plan'
        verbose_name = '网格交易计划'
        verbose_name_plural = '网格交易计划'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.stock_name}({self.stock_code}) - ¥{self.base_price}'


class GridRecord(models.Model):
    """One independent trade record per grid level (part)."""
    STATUS_PENDING = 'PENDING'   # 待买入
    STATUS_HOLDING = 'HOLDING'   # 持仓中
    STATUS_CLEARED = 'CLEARED'   # 已清仓

    STATUS_CHOICES = [
        (STATUS_PENDING, '待买入'),
        (STATUS_HOLDING, '持仓中'),
        (STATUS_CLEARED, '已清仓'),
    ]

    plan = models.ForeignKey(
        GridPlan, on_delete=models.CASCADE, related_name='records', verbose_name='所属计划'
    )
    part_index = models.IntegerField(verbose_name='档位编号')  # 1–5

    # Grid target prices (computed at plan creation)
    target_buy_price = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name='计划买入价'
    )
    target_sell_price = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name='计划卖出价'
    )
    volume = models.IntegerField(verbose_name='买入股数(100的整数倍)')

    # Actual transaction data (filled in by user)
    actual_buy_price = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='实际买入价'
    )
    buy_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='买入金额'
    )
    buy_time = models.DateTimeField(null=True, blank=True, verbose_name='买入时间')

    actual_sell_price = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='实际卖出价'
    )
    sell_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='卖出金额'
    )
    sell_time = models.DateTimeField(null=True, blank=True, verbose_name='卖出时间')

    profit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name='收益(元)'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='状态'
    )
    is_active_cycle = models.BooleanField(default=True, verbose_name='当前循环')

    class Meta:
        db_table = 'grid_record'
        verbose_name = '网格交易记录'
        verbose_name_plural = '网格交易记录'
        ordering = ['part_index', '-id']

    def __str__(self):
        return f'{self.plan.stock_name} 第{self.part_index}档 [{self.get_status_display()}]'

class StockWatchlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlists',
        verbose_name='所属用户'
    )
    stock_code = models.CharField(max_length=20, verbose_name='股票代码')
    stock_name = models.CharField(max_length=50, verbose_name='股票名称')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        db_table = 'stock_watchlist'
        verbose_name = '自选股'
        verbose_name_plural = '自选股'
        ordering = ['-created_at']
        unique_together = ('user', 'stock_code')

    def __str__(self):
        return f'{self.stock_name}({self.stock_code})'

