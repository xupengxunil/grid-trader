import math
from decimal import Decimal

from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import GridPlan, GridRecord, UserProfile
from .permissions import IsApprovedUser
from .serializers import (
    GridPlanSerializer, GridPlanListSerializer, GridRecordSerializer,
    UserRegisterSerializer, UserLoginSerializer, UserProfileSerializer,
)

# ── Constants ─────────────────────────────────────────────────────────────────
PART_COUNT = 5          # number of grid parts
PART_FUNDS = 10000.00   # funds per part (yuan)
GRID_RATIO = Decimal('0.03')   # 3 % grid interval
SHARES_PER_LOT = 100    # A-share: 1 lot = 100 shares


def _compute_grid_records(plan: GridPlan) -> list[dict]:
    """
    Generate PART_COUNT grid records from the plan's base price.

    Grid layout:
      Part 1 → buy at base_price,  sell at base_price * 1.03 (if ratio=0.03)
      Part 2 → buy at base_price * 0.97, sell at base_price
      Part 3 → buy at base_price * 0.94, sell at base_price * 0.97
      ...
    """
    base = Decimal(str(plan.base_price))
    ratio = Decimal(str(plan.grid_ratio))
    records = []
    for i in range(PART_COUNT):
        buy_price = base * ((1 - ratio) ** i)
        sell_price = buy_price * (1 + ratio)

        # Round to 3 decimal places (matching model field precision)
        buy_price = buy_price.quantize(Decimal('0.001'))
        sell_price = sell_price.quantize(Decimal('0.001'))

        # Volume: floor down to whole lots
        part_funds = Decimal(str(PART_FUNDS))
        raw_shares = math.floor(float(part_funds / buy_price) / SHARES_PER_LOT) * SHARES_PER_LOT
        if raw_shares < SHARES_PER_LOT:
            # Less than 1 lot – skip this grid level
            continue

        records.append({
            'part_index': i + 1,
            'target_buy_price': buy_price,
            'target_sell_price': sell_price,
            'volume': int(raw_shares),
        })
    return records


# ── Auth endpoints ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user (account starts as PENDING, awaiting admin approval)."""
    serializer = UserRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(
        {'detail': '注册成功，请等待管理员审批后登录。'},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login and return an auth token."""
    serializer = UserLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user)
    profile_data = UserProfileSerializer(user.profile).data
    return Response({'token': token.key, 'user': profile_data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Invalidate the current auth token."""
    request.user.auth_token.delete()
    return Response({'detail': '已退出登录。'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the current user's profile info."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return Response({'detail': '用户资料不存在。'}, status=status.HTTP_404_NOT_FOUND)
    return Response(UserProfileSerializer(profile).data)


# ── Plan endpoints ─────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsApprovedUser])
def plan_list_create(request):
    """List all plans (GET) or create a new plan with grid records (POST)."""
    if request.method == 'GET':
        plans = GridPlan.objects.prefetch_related('records').filter(user=request.user)
        serializer = GridPlanListSerializer(plans, many=True)
        return Response(serializer.data)

    # POST – create plan
    serializer = GridPlanSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    plan = serializer.save(user=request.user)
    grid_rows = _compute_grid_records(plan)
    if not grid_rows:
        plan.delete()
        return Response(
            {'detail': '基准价过高，每份资金不足1手，无法生成网格计划。'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    for row in grid_rows:
        GridRecord.objects.create(plan=plan, **row)

    plan.refresh_from_db()
    return Response(GridPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'DELETE'])
@permission_classes([IsApprovedUser])
def plan_detail(request, plan_id):
    """Retrieve (GET) or delete (DELETE) a single plan (must belong to current user)."""
    try:
        plan = GridPlan.objects.prefetch_related('records').get(
            pk=plan_id, user=request.user
        )
    except GridPlan.DoesNotExist:
        return Response({'detail': '计划不存在。'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(GridPlanSerializer(plan).data)


# ── Record endpoints ───────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsApprovedUser])
def record_list(request, plan_id):
    """List all grid records for a plan (must belong to current user)."""
    try:
        plan = GridPlan.objects.get(pk=plan_id, user=request.user)
    except GridPlan.DoesNotExist:
        return Response({'detail': '计划不存在。'}, status=status.HTTP_404_NOT_FOUND)

    records = plan.records.all()
    return Response(GridRecordSerializer(records, many=True).data)


@api_view(['POST'])
@permission_classes([IsApprovedUser])
def record_buy(request, record_id):
    """Mark a PENDING record as HOLDING (execute buy)."""
    try:
        record = GridRecord.objects.select_related('plan').get(
            pk=record_id, plan__user=request.user
        )
    except GridRecord.DoesNotExist:
        return Response({'detail': '记录不存在。'}, status=status.HTTP_404_NOT_FOUND)

    if record.status != GridRecord.STATUS_PENDING:
        return Response(
            {'detail': f'当前状态为「{record.get_status_display()}」，不可再次买入。'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    price_raw = request.data.get('price')
    if price_raw is None:
        return Response({'detail': '请提供买入价格(price)。'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        actual_price = Decimal(str(price_raw))
        if actual_price <= 0:
            raise ValueError
    except (ValueError, Exception):
        return Response({'detail': '买入价格无效。'}, status=status.HTTP_400_BAD_REQUEST)

    record.actual_buy_price = actual_price
    record.buy_amount = (actual_price * record.volume).quantize(Decimal('0.01'))
    record.buy_time = timezone.now()
    record.status = GridRecord.STATUS_HOLDING
    record.save()
    return Response(GridRecordSerializer(record).data)


@api_view(['POST'])
@permission_classes([IsApprovedUser])
def record_sell(request, record_id):
    """Mark a HOLDING record as CLEARED (execute sell)."""
    try:
        record = GridRecord.objects.select_related('plan').get(
            pk=record_id, plan__user=request.user
        )
    except GridRecord.DoesNotExist:
        return Response({'detail': '记录不存在。'}, status=status.HTTP_404_NOT_FOUND)

    if record.status != GridRecord.STATUS_HOLDING:
        return Response(
            {'detail': f'当前状态为「{record.get_status_display()}」，不可执行卖出。'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    price_raw = request.data.get('price')
    if price_raw is None:
        return Response({'detail': '请提供卖出价格(price)。'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        actual_price = Decimal(str(price_raw))
        if actual_price <= 0:
            raise ValueError
    except (ValueError, Exception):
        return Response({'detail': '卖出价格无效。'}, status=status.HTTP_400_BAD_REQUEST)

    record.actual_sell_price = actual_price
    record.sell_amount = (actual_price * record.volume).quantize(Decimal('0.01'))
    record.sell_time = timezone.now()
    record.profit = (record.sell_amount - record.buy_amount).quantize(Decimal('0.01'))
    record.status = GridRecord.STATUS_CLEARED
    record.save()
    return Response(GridRecordSerializer(record).data)


# ── Statistics endpoint ────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsApprovedUser])
def statistics(request):
    """
    Return profit statistics for CLEARED records (current user only).

    Query params:
      start_date  – ISO-8601 date string (inclusive)
      end_date    – ISO-8601 date string (inclusive, end of day)
      plan_id     – optional; filter to a single plan
    """
    records = GridRecord.objects.filter(
        status=GridRecord.STATUS_CLEARED,
        plan__user=request.user,
    )

    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    plan_id = request.query_params.get('plan_id')

    if start_date:
        records = records.filter(sell_time__date__gte=start_date)
    if end_date:
        records = records.filter(sell_time__date__lte=end_date)
    if plan_id:
        records = records.filter(plan_id=plan_id)

    agg = records.aggregate(
        total_profit=Sum('profit'),
        total_operations=Count('id'),
    )

    # Per-stock breakdown
    breakdown = (
        records.values('plan__stock_code', 'plan__stock_name')
        .annotate(profit=Sum('profit'), operations=Count('id'))
        .order_by('-profit')
    )
    breakdown_list = [
        {
            'stock_code': row['plan__stock_code'],
            'stock_name': row['plan__stock_name'],
            'profit': row['profit'],
            'operations': row['operations'],
        }
        for row in breakdown
    ]

    return Response({
        'total_profit': agg['total_profit'] or Decimal('0'),
        'total_operations': agg['total_operations'] or 0,
        'breakdown': breakdown_list,
    })
