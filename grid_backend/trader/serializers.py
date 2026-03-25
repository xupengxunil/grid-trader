from rest_framework import serializers
from .models import GridPlan, GridRecord


class GridRecordSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GridRecord
        fields = [
            'id', 'part_index',
            'target_buy_price', 'target_sell_price', 'volume',
            'actual_buy_price', 'buy_amount', 'buy_time',
            'actual_sell_price', 'sell_amount', 'sell_time',
            'profit', 'status', 'status_display',
        ]
        read_only_fields = [
            'id', 'part_index',
            'target_buy_price', 'target_sell_price', 'volume',
            'buy_amount', 'sell_amount', 'profit',
            'status', 'status_display',
        ]


class GridPlanSerializer(serializers.ModelSerializer):
    records = GridRecordSerializer(many=True, read_only=True)
    record_count = serializers.SerializerMethodField()
    holding_count = serializers.SerializerMethodField()
    cleared_count = serializers.SerializerMethodField()

    class Meta:
        model = GridPlan
        fields = [
            'id', 'stock_code', 'stock_name', 'base_price', 'total_funds',
            'created_at', 'updated_at',
            'records', 'record_count', 'holding_count', 'cleared_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_record_count(self, obj):
        return obj.records.count()

    def get_holding_count(self, obj):
        return obj.records.filter(status=GridRecord.STATUS_HOLDING).count()

    def get_cleared_count(self, obj):
        return obj.records.filter(status=GridRecord.STATUS_CLEARED).count()


class GridPlanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for plan list (no nested records)."""
    record_count = serializers.SerializerMethodField()
    holding_count = serializers.SerializerMethodField()
    cleared_count = serializers.SerializerMethodField()

    class Meta:
        model = GridPlan
        fields = [
            'id', 'stock_code', 'stock_name', 'base_price', 'total_funds',
            'created_at', 'record_count', 'holding_count', 'cleared_count',
        ]

    def get_record_count(self, obj):
        return obj.records.count()

    def get_holding_count(self, obj):
        return obj.records.filter(status=GridRecord.STATUS_HOLDING).count()

    def get_cleared_count(self, obj):
        return obj.records.filter(status=GridRecord.STATUS_CLEARED).count()
