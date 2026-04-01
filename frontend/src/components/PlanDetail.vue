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
            <span v-if="currentPrice" :class="['current-price', priceChange >= 0 ? 'profit' : 'loss']" style="margin-left:16px; font-weight: bold;">
              当前价：¥{{ currentPrice.toFixed(3) }} 
              <span style="font-size:14px">({{ priceChange >= 0 ? '+' : '' }}{{ priceChange.toFixed(2) }}%)</span>
            </span>
            <span class="grid-ratio" style="margin-left:auto; color:#606266; font-size:14px">
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

      <!-- K-line Chart -->
      <el-card style="margin-top:16px" v-loading="chartLoading">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>网格水位走势图</span>
            <el-radio-group v-model="klineScale" size="small" @change="fetchAndDrawKline">
              <el-radio-button label="15">15分钟</el-radio-button>
              <el-radio-button label="60">60分钟</el-radio-button>
              <el-radio-button label="240">日线</el-radio-button>
            </el-radio-group>
          </div>
        </template>
        <div ref="chartContainer" style="width: 100%; height: 400px;"></div>
      </el-card>

      <!-- Grid records table -->
      <el-card style="margin-top:16px">
        <template #header>
          <span>网格档位详情</span>
        </template>
        <el-table :data="activeRecords" border stripe>
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
              <el-button
                v-if="row.status === 'CLEARED'"
                type="info"
                size="small"
                style="margin-left:8px;"
                @click="confirmRestart(row)"
              >重启</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Transaction History Card -->
      <el-card style="margin-top:16px; margin-bottom: 20px;">
        <template #header>
          <span>交易历史记录</span>
        </template>
        <el-table :data="tradeHistory" border stripe style="width: 100%" max-height="500">
          <el-table-column label="时间" align="center" width="160">
            <template #default="{ row }">
              {{ formatTime(row.time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" align="center" width="80">
            <template #default="{ row }">
              <el-tag :type="row.type === '买入' ? 'primary' : 'warning'" size="small">
                {{ row.type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="档位" prop="part_index" align="center" width="80" />
          <el-table-column label="成交价" align="right">
            <template #default="{ row }">
              ¥{{ row.price }}
            </template>
          </el-table-column>
          <el-table-column label="数量(股)" prop="volume" align="right" />
          <el-table-column label="成交金额" align="right">
            <template #default="{ row }">
              ¥{{ row.amount }}
            </template>
          </el-table-column>
          <el-table-column label="收益" align="right">
            <template #default="{ row }">
              <span v-if="row.profit !== null" :class="row.profit >= 0 ? 'profit' : 'loss'">
                {{ row.profit >= 0 ? '+' : '' }}{{ row.profit }}
              </span>
              <span v-else>-</span>
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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getPlan, executeBuy, executeSell, restartRecord, getQuotes, getKLine } from '../api/index.js'

const props = defineProps({ id: { type: String, required: true } })

const plan = ref(null)
const loading = ref(false)
const currentPrice = ref(null)
const priceChange = ref(0)

const chartContainer = ref(null)
const chartLoading = ref(false)
const klineScale = ref('60')
let chartInstance = null

function getSinaCode(code) {
  code = code.trim().toLowerCase();
  if (!code) return '';
  if (code.startsWith('sh') || code.startsWith('sz') || code.startsWith('bj')) return code;
  if (/^6/.test(code)) return 'sh' + code;
  if (/^0|^3/.test(code)) return 'sz' + code;
  if (/^8|^4/.test(code)) return 'bj' + code;
  return code;
}

async function fetchQuote() {
  if (!plan.value?.stock_code) return
  const sc = getSinaCode(plan.value.stock_code)
  try {
    const { data } = await getQuotes(sc)
    if (data && data[sc]) {
      currentPrice.value = data[sc].price > 0 ? data[sc].price : data[sc].close
      priceChange.value = ((currentPrice.value - data[sc].close) / data[sc].close) * 100
    }
  } catch (e) {
    // silence background quote errors
  }
}

async function fetchAndDrawKline() {
  if (!plan.value?.stock_code) return
  chartLoading.value = true
  try {
    const sc = getSinaCode(plan.value.stock_code)
    const { data } = await getKLine(sc, klineScale.value, 150)
    if (data && data.length) {
      await nextTick()
      drawChart(data)
    }
  } catch (e) {
    ElMessage.error('获取K线数据失败')
  } finally {
    chartLoading.value = false
  }
}

function drawChart(klineData) {
  if (!chartContainer.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartContainer.value)
  }
  
  const categoryData = klineData.map(item => item.day)
  const values = klineData.map(item => [
    parseFloat(item.open),
    parseFloat(item.close),
    parseFloat(item.low),
    parseFloat(item.high)
  ])

  const markLineData = []
  if (plan.value && plan.value.records) {
    const activeR = plan.value.records.filter(r => r.is_active_cycle)
    
    // Create base price line
    if (plan.value.base_price) {
      markLineData.push({
        yAxis: Number(plan.value.base_price),
        name: '基准价',
        label: { formatter: '基准: {c}', position: 'end', color: '#888' },
        lineStyle: { color: '#888', type: 'solid', width: 2 }
      })
    }

    activeR.forEach(r => {
      // 待买入 (PENDING) 蓝色虚线
      if (r.status === 'PENDING') {
        markLineData.push({
          yAxis: Number(r.target_buy_price),
          name: '买' + r.part_index,
          label: { formatter: '买' + r.part_index + ' ({c})', position: 'end', color: '#409EFF' },
          lineStyle: { color: '#409EFF', type: 'dashed', width: 2 }
        })
      }
      
      // 持仓中 (HOLDING) 代表已经买入，需要画出它的目标卖出价，橙色实线，表示网格“拦截网”已挂靠
      if (r.status === 'HOLDING') {
        markLineData.push({
          yAxis: Number(r.target_sell_price),
          name: '卖' + r.part_index,
          label: { formatter: '卖' + r.part_index + ' ({c})', position: 'start', color: '#E6A23C' },
          lineStyle: { color: '#E6A23C', type: 'solid', width: 2 }
        })
        
        // 也可以顺便画一条半透明的买入成本线供参考
        markLineData.push({
          yAxis: Number(r.actual_buy_price || r.target_buy_price),
          name: '买入成本',
          label: { formatter: '建仓价(第' + r.part_index + '档)', position: 'end', color: '#909399', fontSize: 10 },
          lineStyle: { color: '#909399', type: 'dotted', width: 1, opacity: 0.6 }
        })
      }
    })
  }

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: '8%', right: '10%', bottom: '15%' },
    xAxis: { type: 'category', data: categoryData, scale: true, boundaryGap: false, splitLine: { show: false } },
    yAxis: { scale: true, splitArea: { show: true } },
    dataZoom: [ { type: 'inside', start: 60, end: 100 }, { show: true, type: 'slider', top: '90%', start: 60, end: 100 } ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: values,
        itemStyle: { color: '#ef232a', color0: '#14b143', borderColor: '#ef232a', borderColor0: '#14b143' },
        markLine: {
          symbol: ['none', 'none'],
          data: markLineData,
          precision: 3
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

function resizeChart() {
  if (chartInstance) chartInstance.resize()
}

const activeRecords = computed(() => {
  if (!plan.value) return []
  return plan.value.records.filter(r => r.is_active_cycle)
})

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

const tradeHistory = computed(() => {
  if (!plan.value || !plan.value.records) return []
  const history = []
  plan.value.records.forEach(r => {
    if (r.buy_time) {
      history.push({
        id: r.id + '_buy',
        type: '买入',
        part_index: r.part_index,
        price: r.actual_buy_price,
        volume: r.volume,
        amount: r.buy_amount,
        time: r.buy_time,
        profit: null
      })
    }
    if (r.sell_time && r.status === 'CLEARED') {
      history.push({
        id: r.id + '_sell',
        type: '卖出',
        part_index: r.part_index,
        price: r.actual_sell_price,
        volume: r.volume,
        amount: r.sell_amount,
        time: r.sell_time,
        profit: r.profit
      })
    }
  })
  history.sort((a, b) => new Date(b.time) - new Date(a.time))
  return history
})

async function fetchPlan() {
  loading.value = true
  try {
    const { data } = await getPlan(props.id)
    plan.value = data
    fetchQuote()
    fetchAndDrawKline()
  } catch {
    ElMessage.error('加载计划详情失败')
  } finally {
    loading.value = false
  }
}

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  if (chartInstance) chartInstance.dispose()
})

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

async function confirmRestart(record) {
  try {
    await ElMessageBox.confirm('确定要重启该网格档位吗？该档位将被归档，并生成一条新的待买入记录。', '确认重启', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await restartRecord(record.id)
    ElMessage.success(res.data?.message || '重启成功')
    await fetchPlan()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

onMounted(() => {
  fetchPlan()
  window.addEventListener('resize', resizeChart)
})
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
