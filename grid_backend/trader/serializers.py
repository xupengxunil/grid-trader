from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import GridPlan, GridRecord, UserProfile


class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=6, write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('该用户名已被占用。')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
        )
        UserProfile.objects.create(user=user, status=UserProfile.STATUS_PENDING)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('用户名或密码错误。')
        if not user.is_active:
            raise serializers.ValidationError('账号已被禁用。')
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError('账号状态异常，请联系管理员。')
        if profile.status == UserProfile.STATUS_PENDING:
            raise serializers.ValidationError('账号待审批，请等待管理员审核后登录。')
        if profile.status == UserProfile.STATUS_REJECTED:
            raise serializers.ValidationError('账号已被拒绝，请联系管理员。')
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_staff = serializers.BooleanField(source='user.is_staff', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'status', 'status_display', 'created_at', 'is_staff']


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
