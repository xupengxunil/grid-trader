"""
Unit tests for the trader app.
Run with:  python manage.py test trader
"""
import math
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import GridPlan, GridRecord
from .views import _compute_grid_records, GRID_RATIO, PART_FUNDS, PART_COUNT, SHARES_PER_LOT


class GridComputationTests(TestCase):
    """Test the core grid calculation logic."""

    def _make_plan(self, base_price: float) -> GridPlan:
        return GridPlan(
            stock_code='600000',
            stock_name='浦发银行',
            base_price=Decimal(str(base_price)),
            total_funds=Decimal('50000.00'),
        )

    def test_grid_count_normal_price(self):
        """A normal base price should produce 5 grid records."""
        plan = self._make_plan(10.00)
        records = _compute_grid_records(plan)
        self.assertEqual(len(records), PART_COUNT)

    def test_grid_buy_prices_decrease(self):
        """Each subsequent part's buy price must be 3 % lower."""
        plan = self._make_plan(10.00)
        records = _compute_grid_records(plan)
        for i in range(1, len(records)):
            prev = records[i - 1]['target_buy_price']
            curr = records[i]['target_buy_price']
            expected = (prev * (1 - GRID_RATIO)).quantize(Decimal('0.001'))
            self.assertEqual(curr, expected)

    def test_grid_sell_price_is_buy_plus_3pct(self):
        """Each part's sell price must be 3 % above its buy price."""
        plan = self._make_plan(10.00)
        records = _compute_grid_records(plan)
        for row in records:
            expected_sell = (row['target_buy_price'] * (1 + GRID_RATIO)).quantize(Decimal('0.001'))
            self.assertEqual(row['target_sell_price'], expected_sell)

    def test_volume_multiple_of_100(self):
        """Volumes must be multiples of 100 (whole lots)."""
        plan = self._make_plan(10.00)
        records = _compute_grid_records(plan)
        for row in records:
            self.assertEqual(row['volume'] % SHARES_PER_LOT, 0)
            self.assertGreaterEqual(row['volume'], SHARES_PER_LOT)

    def test_volume_floor_down(self):
        """Volume should be floor(funds / price / 100) * 100."""
        base = 10.00
        plan = self._make_plan(base)
        records = _compute_grid_records(plan)
        for row in records:
            expected = math.floor(PART_FUNDS / float(row['target_buy_price']) / 100) * 100
            self.assertEqual(row['volume'], expected)

    def test_too_expensive_stock_returns_empty(self):
        """If buy price > PART_FUNDS / 100, no lot can be bought → empty list."""
        plan = self._make_plan(200.00)  # 200 × 100 = 20 000 > 10 000
        records = _compute_grid_records(plan)
        self.assertEqual(records, [])


class PlanAPITests(TestCase):
    """Integration tests for the plan and record REST endpoints."""

    def test_create_plan_success(self):
        resp = self.client.post(
            '/api/plans/',
            data={'stock_code': '600000', 'stock_name': '浦发银行', 'base_price': '10.000'},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['stock_code'], '600000')
        self.assertEqual(len(data['records']), PART_COUNT)

    def test_create_plan_too_expensive(self):
        resp = self.client.post(
            '/api/plans/',
            data={'stock_code': 'TEST', 'stock_name': '测试', 'base_price': '200.000'},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_list_plans(self):
        self.client.post(
            '/api/plans/',
            data={'stock_code': '000001', 'stock_name': '平安银行', 'base_price': '12.000'},
            content_type='application/json',
        )
        resp = self.client.get('/api/plans/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_buy_and_sell_flow(self):
        # Create plan
        resp = self.client.post(
            '/api/plans/',
            data={'stock_code': '600000', 'stock_name': '浦发银行', 'base_price': '10.000'},
            content_type='application/json',
        )
        plan_data = resp.json()
        record_id = plan_data['records'][0]['id']

        # Buy
        buy_resp = self.client.post(
            f'/api/records/{record_id}/buy/',
            data={'price': '10.100'},
            content_type='application/json',
        )
        self.assertEqual(buy_resp.status_code, 200)
        self.assertEqual(buy_resp.json()['status'], 'HOLDING')

        # Sell
        sell_resp = self.client.post(
            f'/api/records/{record_id}/sell/',
            data={'price': '10.400'},
            content_type='application/json',
        )
        self.assertEqual(sell_resp.status_code, 200)
        rec = sell_resp.json()
        self.assertEqual(rec['status'], 'CLEARED')
        volume = rec['volume']
        expected_profit = round((10.400 - 10.100) * volume, 2)
        self.assertAlmostEqual(float(rec['profit']), expected_profit, places=2)

    def test_double_buy_rejected(self):
        resp = self.client.post(
            '/api/plans/',
            data={'stock_code': '600000', 'stock_name': '浦发银行', 'base_price': '10.000'},
            content_type='application/json',
        )
        record_id = resp.json()['records'][0]['id']
        self.client.post(
            f'/api/records/{record_id}/buy/',
            data={'price': '10.000'},
            content_type='application/json',
        )
        resp2 = self.client.post(
            f'/api/records/{record_id}/buy/',
            data={'price': '10.000'},
            content_type='application/json',
        )
        self.assertEqual(resp2.status_code, 400)

    def test_sell_without_buy_rejected(self):
        resp = self.client.post(
            '/api/plans/',
            data={'stock_code': '600000', 'stock_name': '浦发银行', 'base_price': '10.000'},
            content_type='application/json',
        )
        record_id = resp.json()['records'][0]['id']
        resp2 = self.client.post(
            f'/api/records/{record_id}/sell/',
            data={'price': '10.500'},
            content_type='application/json',
        )
        self.assertEqual(resp2.status_code, 400)

    def test_statistics(self):
        # Create plan, buy, sell all 5 records
        resp = self.client.post(
            '/api/plans/',
            data={'stock_code': '600000', 'stock_name': '浦发银行', 'base_price': '10.000'},
            content_type='application/json',
        )
        records = resp.json()['records']
        for rec in records:
            self.client.post(
                f'/api/records/{rec["id"]}/buy/',
                data={'price': str(rec['target_buy_price'])},
                content_type='application/json',
            )
            self.client.post(
                f'/api/records/{rec["id"]}/sell/',
                data={'price': str(rec['target_sell_price'])},
                content_type='application/json',
            )

        stats_resp = self.client.get('/api/statistics/')
        self.assertEqual(stats_resp.status_code, 200)
        data = stats_resp.json()
        self.assertEqual(data['total_operations'], len(records))
        self.assertGreater(float(data['total_profit']), 0)

    def test_delete_plan(self):
        resp = self.client.post(
            '/api/plans/',
            data={'stock_code': '600000', 'stock_name': '浦发银行', 'base_price': '10.000'},
            content_type='application/json',
        )
        plan_id = resp.json()['id']
        del_resp = self.client.delete(f'/api/plans/{plan_id}/')
        self.assertEqual(del_resp.status_code, 204)
        self.assertEqual(GridPlan.objects.count(), 0)
        self.assertEqual(GridRecord.objects.count(), 0)
