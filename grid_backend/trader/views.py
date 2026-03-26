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
GRID_RATIO = Decimal('0.03')   # 3 % grid interval
SHARES_PER_LOT = 100    # A-share: 1 lot = 100 shares


def _compute_grid_records(plan: GridPlan) -> list[dict]:
    """
    Generate part_count grid records from the plan's base price.

    Grid layout:
      Part 1 → buy at base_price,  sell at base_price * 1.03 (if ratio=0.03)
      Part 2 → buy at base_price * 0.97, sell at base_price
      Part 3 → buy at base_price * 0.94, sell at base_price * 0.97
      ...
    """
    base = Decimal(str(plan.base_price))
    ratio = Decimal(str(plan.grid_ratio))
    part_count = plan.part_count
    total_funds = Decimal(str(plan.total_funds))
    part_funds = total_funds / Decimal(str(part_count)) if part_count > 0 else Decimal('0')
    
    records = []
    for i in range(part_count):
        buy_price = base * ((1 - ratio) ** i)
        sell_price = buy_price * (1 + ratio)

        # Round to 3 decimal places (matching model field precision)
        buy_price = buy_price.quantize(Decimal('0.001'))
        sell_price = sell_price.quantize(Decimal('0.001'))

        # Volume: floor down to whole lots
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


@api_view(['GET', 'DELETE', 'PATCH'])
@permission_classes([IsApprovedUser])
def plan_detail(request, plan_id):
    """Retrieve (GET), update (PATCH) or delete (DELETE) a single plan (must belong to current user)."""
    try:
        plan = GridPlan.objects.prefetch_related('records').get(
            pk=plan_id, user=request.user
        )
    except GridPlan.DoesNotExist:
        return Response({'detail': '计划不存在。'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    if request.method == 'PATCH':
        serializer = GridPlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

@api_view(['POST'])
@permission_classes([IsApprovedUser])
def record_restart(request, record_id):
    """Restart a CLEARED record. Moves it to inactive cycle and creates a new PENDING record."""
    try:
        record = GridRecord.objects.select_related('plan').get(
            pk=record_id, plan__user=request.user
        )
    except GridRecord.DoesNotExist:
        return Response({'detail': '记录不存在。'}, status=status.HTTP_404_NOT_FOUND)

    if record.status != GridRecord.STATUS_CLEARED:
        return Response(
            {'detail': f'只有已清仓的状态才可以重启。'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not record.is_active_cycle:
        return Response(
            {'detail': f'该档位已被重启过，请针对最新的清仓记录进行操作。'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 1. 标记老记录不再是当前活跃循环
    record.is_active_cycle = False
    record.save()

    # 2. 为当前档位创建一条全新的 PENDING 记录
    new_record = GridRecord.objects.create(
        plan=record.plan,
        part_index=record.part_index,
        target_buy_price=record.target_buy_price,
        target_sell_price=record.target_sell_price,
        volume=record.volume,
        status=GridRecord.STATUS_PENDING,
        is_active_cycle=True
    )
    return Response(GridRecordSerializer(new_record).data, status=status.HTTP_201_CREATED)

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


@api_view(['GET'])
@permission_classes([IsApprovedUser])
def stock_quotes(request):
    """Fetch real-time stock prices from Sina API."""
    import requests
    codes = request.GET.get('codes', '')
    if not codes:
        return Response({})
    url = f"http://hq.sinajs.cn/list={codes}"
    headers = {"Referer": "http://finance.sina.com.cn"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.encoding = 'gbk'
        res = {}
        for line in r.text.strip().split('\n'):
            if '=' in line:
                var_name, val_str = line.split('=', 1)
                code = var_name.split('_')[-1]
                parts = val_str.replace('"', '').replace(';', '').split(',')
                if len(parts) > 3:
                    res[code] = {
                        "name": parts[0],
                        "open": float(parts[1]),
                        "close": float(parts[2]),
                        "price": float(parts[3]),
                        "high": float(parts[4]),
                        "low": float(parts[5]),
                    }
        return Response(res)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsApprovedUser])
def stock_search(request):
    """Search stock by Chinese name, pinyin, or code using Sina Suggest API."""
    import requests
    keyword = request.GET.get('keyword', '')
    if not keyword:
        return Response([])
    
    # type=11,12 表示 A股
    url = f"http://suggest3.sinajs.cn/suggest/type=11,12&key={keyword}"
    try:
        r = requests.get(url, timeout=5)
        r.encoding = 'gbk'
        text = r.text.strip()
        results = []
        if '="' in text:
            data_str = text.split('="')[1].replace('";', '')
            if data_str:
                items = data_str.split(';')
                for item in items:
                    parts = item.split(',')
                    if len(parts) >= 5:
                        results.append({
                            "name": parts[4],       # 贵州茅台
                            "code": parts[3],       # sh600519
                            "raw_code": parts[2]    # 600519
                        })
        return Response(results)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsApprovedUser])
def stock_kline(request):
    """Fetch K-Line data from Sina API."""
    import requests
    symbol = request.GET.get('symbol', '')
    scale = request.GET.get('scale', '60')
    datalen = request.GET.get('datalen', '100')
    if not symbol:
        return Response([])
    url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&ma=no&datalen={datalen}"
    try:
        r = requests.get(url, timeout=5)
        r.encoding = 'utf-8'
        import json
        return Response(json.loads(r.text))
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


from .models import StockWatchlist
from .serializers import StockWatchlistSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsApprovedUser])
def watchlist_list_create(request):
    if request.method == 'GET':
        watch_qs = StockWatchlist.objects.filter(user=request.user)
        serializer = StockWatchlistSerializer(watch_qs, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = StockWatchlistSerializer(data=request.data)
        if serializer.is_valid():
            # Check unique together
            if StockWatchlist.objects.filter(user=request.user, stock_code=serializer.validated_data['stock_code']).exists():
                return Response({'error': '股票已在自选股中'}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsApprovedUser])
def watchlist_delete(request, code):
    try:
        watch_item = StockWatchlist.objects.get(user=request.user, stock_code=code)
        watch_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except StockWatchlist.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

