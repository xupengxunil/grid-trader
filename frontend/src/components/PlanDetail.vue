<template>
  <div v-loading="loading">
    <!-- Back button -->
    <div class="back-bar">
      <el-button :icon="ArrowLeft" @click="$router.push('/plans')">返回列表</el-button>
    </div>

    <template v-if="plan">
      <!-- Plan summary -->
      <el-card class="summary-card">
        <template #header>
          <div class="summary-header">
            <span class="stock-code">{{ plan.stock_code }}</span>
            <span class="stock-name">{{ plan.stock_name }}</span>
            <span class="base-price">基准价：¥{{ plan.base_price }}</span>
            <span class="grid-ratio" style="margin-left:8px; color:#606266; font-size:14px">
              网格大小：{{ plan.grid_ratio ? (plan.grid_ratio * 100).toFixed(1) + '%' : '3.0%' }}
            </span>
          </div>
        </template>
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ plan.record_count }}</div>
              <div class="stat-label">总档位</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item pending">
              <div class="stat-value">{{ pendingCount }}</div>
              <div class="stat-label">待买入</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item holding">
              <div class="stat-value">{{ plan.holding_count }}</div>
              <div class="stat-label">持仓中</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item cleared">
              <div class="stat-value">{{ plan.cleared_count }}</div>
              <div class="stat-label">已清仓</div>
            </div>
          </el-col>
        </el-row>
        <el-divider style="margin: 12px 0;" />
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="stat-item">
              <div :class="['stat-value', realizedProfit >= 0 ? 'profit' : 'loss']">
                {{ realizedProfit >= 0 ? '+' : '' }}{{ realizedProfit.toFixed(2) }}
              </div>
              <div class="stat-label">平仓总收益 (元)</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item loss">
              <div class="stat-value">-{{ totalFee }}</div>
              <div class="stat-label">预估手续费 (元)</div>
            </div>
          </el-col>
          <el-col :span="8">
             <div class="stat-item">
              <div :class="['stat-value', netProfit >= 0 ? 'profit' : 'loss']">
                {{ netProfit >= 0 ? '+' : '' }}{{ netProfit.toFixed(2) }}
              </div>
              <div class="stat-label">预估净收益 (元)</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- Grid records table -->
      <el-card style="margin-top:16px">
        <template #header>
          <span>网格档位详情</span>
        </template>
        <el-table :data="plan.records" border stripe>
          <el-table-column label="档位" prop="part_index" width="60" align="center" />
          <el-table-column label="计划买入价" align="right">
            <template #default="{ row }">
              ¥{{ row.target_buy_price }}
            </template>
          </el-table-column>
          <el-table-column label="计划卖出价" align="right">
            <template #default="{ row }">
              ¥{{ row.target_sell_price }}
            </template>
          </el-table-column>
          <el-table-column label="数量(股)" prop="volume" align="right" />
          <el-table-column label="状态" align="center" width="90">
            <template #default="{ row }">
              <el-tag :type="tagType(row.status)" size="small">
                {{ row.status_display }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="实际买入价" align="right">
            <template #default="{ row }">
              {{ row.actual_buy_price ? '¥' + row.actual_buy_price : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="买入金额" align="right">
            <template #default="{ row }">
              {{ row.buy_amount ? '¥' + row.buy_amount : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="买入时间" align="center" width="160">
            <template #default="{ row }">
              {{ formatTime(row.buy_time) }}
            </template>
          </el-table-column>
          <el-table-column label="实际卖出价" align="right">
            <template #default="{ row }">
              {{ row.actual_sell_price ? '¥' + row.actual_sell_price : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="卖出金额" align="right">
            <template #default="{ row }">
              {{ row.sell_amount ? '¥' + row.sell_amount : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="卖出时间" align="center" width="160">
            <template #default="{ row }">
              {{ formatTime(row.sell_time) }}
            </template>
          </el-table-column>
          <el-table-column label="收益" align="right" width="100">
            <template #default="{ row }">
              <span v-if="row.status === 'CLEARED'" :class="row.profit >= 0 ? 'profit' : 'loss'">
                {{ row.profit >= 0 ? '+' : '' }}{{ row.profit }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" align="center" width="140" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'PENDING'"
                type="primary"
                size="small"
                @click="openBuyDialog(row)"
              >买入</el-button>
              <el-button
                v-if="row.status === 'HOLDING'"
                type="warning"
                size="small"
                @click="openSellDialog(row)"
              >卖出</el-button>
              <span v-if="row.status === 'CLEARED'" class="cleared-label">已清仓</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <!-- Buy dialog -->
    <el-dialog v-model="buyDialog.visible" title="记录买入" width="400px">
      <el-form label-width="100px">
        <el-form-item label="档位">第 {{ buyDialog.record?.part_index }} 档</el-form-item>
        <el-form-item label="计划买入价">¥{{ buyDialog.record?.target_buy_price }}</el-form-item>
        <el-form-item label="买入数量">{{ buyDialog.record?.volume }} 股</el-form-item>
        <el-form-item label="实际买入价" required>
          <el-input-number
            v-model="buyDialog.price"
            :precision="3"
            :step="0.01"
            :min="0.001"
            style="width:100%"
            placeholder="请输入实际成交价"
          />
        </el-form-item>
        <el-alert
          v-if="buyDialog.price && buyDialog.record"
          type="info"
          :closable="false"
          :description="`预计买入金额：¥${(buyDialog.price * buyDialog.record.volume).toFixed(2)}`"
        />
      </el-form>
      <template #footer>
        <el-button @click="buyDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="buyDialog.loading" @click="confirmBuy">确认买入</el-button>
      </template>
    </el-dialog>

    <!-- Sell dialog -->
    <el-dialog v-model="sellDialog.visible" title="记录卖出" width="400px">
      <el-form label-width="100px">
        <el-form-item label="档位">第 {{ sellDialog.record?.part_index }} 档</el-form-item>
        <el-form-item label="计划卖出价">¥{{ sellDialog.record?.target_sell_price }}</el-form-item>
        <el-form-item label="持仓数量">{{ sellDialog.record?.volume }} 股</el-form-item>
        <el-form-item label="买入成本">¥{{ sellDialog.record?.buy_amount }}</el-form-item>
        <el-form-item label="实际卖出价" required>
          <el-input-number
            v-model="sellDialog.price"
            :precision="3"
            :step="0.01"
            :min="0.001"
            style="width:100%"
            placeholder="请输入实际卖出价"
          />
        </el-form-item>
        <el-alert
          v-if="sellDialog.price && sellDialog.record"
          :type="previewProfit >= 0 ? 'success' : 'error'"
          :closable="false"
          :description="`预计卖出金额：¥${(sellDialog.price * sellDialog.record.volume).toFixed(2)}，预计收益：${previewProfit >= 0 ? '+' : ''}${previewProfit.toFixed(2)} 元`"
        />
      </el-form>
      <template #footer>
        <el-button @click="sellDialog.visible = false">取消</el-button>
        <el-button type="warning" :loading="sellDialog.loading" @click="confirmSell">确认卖出（清仓）</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getPlan, executeBuy, executeSell } from '../api/index.js'

const props = defineProps({ id: { type: String, required: true } })

const plan = ref(null)
const loading = ref(false)

const pendingCount = computed(() =>
  plan.value?.records.filter(r => r.status === 'PENDING').length ?? 0
)

const totalOperations = computed(() => {
  if (!plan.value) return 0
  // 每清仓1档代表有买入和卖出2次操作，按要求只计算清仓的手续费
  return (plan.value.cleared_count || 0) * 2
})

const totalFee = computed(() => {
  if (!plan.value) return 0
  // 仅计算清仓的操作，每清仓1档收取一次15元手续费
  return (plan.value.cleared_count || 0) * 15
})

const realizedProfit = computed(() => {
  if (!plan.value) return 0
  let p = 0
  for (const r of plan.value.records) {
    if (r.status === 'CLEARED' && r.profit) {
      p += Number(r.profit)
    }
  }
  return p
})

const netProfit = computed(() => realizedProfit.value - totalFee.value)

async function fetchPlan() {
  loading.value = true
  try {
    const { data } = await getPlan(props.id)
    plan.value = data
  } catch {
    ElMessage.error('加载计划详情失败')
  } finally {
    loading.value = false
  }
}

function tagType(status) {
  return { PENDING: 'info', HOLDING: 'warning', CLEARED: 'success' }[status] ?? ''
}

function formatTime(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ── Buy dialog ────────────────────────────────────────────────────────────────
const buyDialog = ref({ visible: false, record: null, price: null, loading: false })

function openBuyDialog(record) {
  buyDialog.value = { visible: true, record, price: Number(record.target_buy_price), loading: false }
}

async function confirmBuy() {
  if (!buyDialog.value.price) return ElMessage.warning('请输入买入价格')
  buyDialog.value.loading = true
  try {
    await executeBuy(buyDialog.value.record.id, buyDialog.value.price)
    ElMessage.success('买入记录已保存')
    buyDialog.value.visible = false
    await fetchPlan()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    buyDialog.value.loading = false
  }
}

// ── Sell dialog ───────────────────────────────────────────────────────────────
const sellDialog = ref({ visible: false, record: null, price: null, loading: false })

const previewProfit = computed(() => {
  if (!sellDialog.value.price || !sellDialog.value.record?.buy_amount) return 0
  const sell = sellDialog.value.price * sellDialog.value.record.volume
  return sell - Number(sellDialog.value.record.buy_amount)
})

function openSellDialog(record) {
  sellDialog.value = {
    visible: true,
    record,
    price: Number(record.target_sell_price),
    loading: false,
  }
}

async function confirmSell() {
  if (!sellDialog.value.price) return ElMessage.warning('请输入卖出价格')
  sellDialog.value.loading = true
  try {
    await executeSell(sellDialog.value.record.id, sellDialog.value.price)
    ElMessage.success('卖出记录已保存，该档已清仓！')
    sellDialog.value.visible = false
    await fetchPlan()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    sellDialog.value.loading = false
  }
}

onMounted(fetchPlan)
</script>

<style scoped>
.back-bar { margin-bottom: 16px; }

.summary-card { margin-bottom: 8px; }
.summary-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
}
.stock-code {
  background: #409eff;
  color: #fff;
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 700;
}
.stock-name { font-weight: 600; flex: 1; }
.base-price { color: #606266; font-size: 14px; }

.stat-item { text-align: center; padding: 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: #303133; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.pending .stat-value { color: #909399; }
.holding .stat-value { color: #e6a23c; }
.cleared .stat-value { color: #67c23a; }

/* A-share convention: red = gain, green = loss */
.profit { color: #f56c6c; font-weight: 600; }
.loss  { color: #67c23a; font-weight: 600; }

.cleared-label { color: #909399; font-size: 12px; }
</style>
