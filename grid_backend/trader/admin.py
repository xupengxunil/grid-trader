from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import GridPlan, GridRecord, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '审批状态'
    fields = ['status']


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'is_staff', 'is_active', 'get_approval_status']
    list_filter = BaseUserAdmin.list_filter + ('profile__status',)

    @admin.display(description='审批状态')
    def get_approval_status(self, obj):
        try:
            return obj.profile.get_status_display()
        except UserProfile.DoesNotExist:
            return '-'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'user__email']
    actions = ['approve_users', 'reject_users']

    @admin.action(description='✅ 审批通过选中用户')
    def approve_users(self, request, queryset):
        updated = queryset.update(status=UserProfile.STATUS_APPROVED)
        self.message_user(request, f'已批准 {updated} 个用户。')

    @admin.action(description='❌ 拒绝选中用户')
    def reject_users(self, request, queryset):
        updated = queryset.update(status=UserProfile.STATUS_REJECTED)
        self.message_user(request, f'已拒绝 {updated} 个用户。')


@admin.register(GridPlan)
class GridPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'stock_code', 'stock_name', 'base_price', 'total_funds', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['stock_code', 'stock_name', 'user__username']


@admin.register(GridRecord)
class GridRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'plan', 'part_index', 'status',
        'target_buy_price', 'target_sell_price', 'volume',
        'actual_buy_price', 'buy_time', 'actual_sell_price', 'sell_time', 'profit',
    ]
    list_filter = ['status', 'plan']
    search_fields = ['plan__stock_code', 'plan__stock_name']
