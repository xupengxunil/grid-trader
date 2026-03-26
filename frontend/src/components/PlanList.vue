<template>
  <div>
    <!-- Page header -->
    <div class="page-header">
      <h2>交易计划列表</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        新建计划
      </el-button>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="plan-tabs">
      <el-tab-pane label="活跃计划" name="active" />
      <el-tab-pane label="已归档" name="archived" />
    </el-tabs>

    <!-- Plan cards -->
    <el-empty v-if="!loading && displayedPlans.length === 0" :description="activeTab === 'active' ? '暂无活跃计划，点击右上角新建' : '暂无已归档计划'" />

    <el-row :gutter="24" v-loading="loading">
      <el-col
        v-for="plan in displayedPlans"
        :key="plan.id"
        :xs="24" :sm="24" :md="12" :lg="12" :xl="8"
        class="plan-col"
      >
        <el-card class="plan-card" shadow="hover" @click="goDetail(plan.id)">
          <template #header>
            <div class="card-header">
              <span class="stock-code">{{ plan.stock_code }}</span>
              <span class="stock-name">{{ plan.stock_name }}</span>
              <el-tag v-if="!plan.is_active" type="info" size="small" effect="plain">已归档</el-tag>
              <div style="flex-grow: 1"></div>
              <el-button
                type="primary"
                size="small"
                :icon="CopyDocument"
                title="复制计划"
                circle
                @click.stop="duplicatePlan(plan)"
              />
              <el-button
                v-if="plan.is_active"
                type="warning"
                size="small"
                :icon="Box"
                title="归档计划"
                circle
                @click.stop="confirmArchive(plan)"
              />
              <el-button
                type="danger"
                size="small"
                :icon="Delete"
                title="删除计划"
                circle
                @click.stop="confirmDelete(plan)"
              />
            </div>
          </template>

          <el-descriptions :column="2" size="default" class="plan-desc">
            <el-descriptions-item label="基准价">
              <span class="highlight-text">¥{{ plan.base_price }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="当前价">
              <span v-if="plan.current_price" :class="plan.price_change >= 0 ? 'profit-text' : 'loss-text'">
                ¥{{ plan.current_price.toFixed(3) }}
                <span style="font-size:12px; margin-left:2px">({{ plan.price_change >= 0 ? '+' : '' }}{{ plan.price_change.toFixed(2) }}%)</span>
              </span>
              <span v-else class="highlight-text">获取中...</span>
            </el-descriptions-item>
            <el-descriptions-item label="网格大小">
              <span class="highlight-text">{{ plan.grid_ratio ? (plan.grid_ratio * 100).toFixed(1) + '%' : '3.0%' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="总资金">
              <span class="highlight-text">¥{{ plan.total_funds }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="网格档位">
              <span class="highlight-text">{{ plan.record_count }} 档</span>
            </el-descriptions-item>
            <el-descriptions-item label="已持仓">
              <span class="holding-text">{{ plan.holding_count }} 档</span>
            </el-descriptions-item>
            <el-descriptions-item label="已清仓">
              <span class="cleared-text">{{ plan.cleared_count }} 档</span>
            </el-descriptions-item>
            <el-descriptions-item label="预估净收益">
              <span :class="['profit-value', plan.net_profit >= 0 ? 'profit-text' : 'loss-text']">
                {{ plan.net_profit >= 0 ? '+' : '' }}{{ Number(plan.net_profit || 0).toFixed(2) }}
              </span>
            </el-descriptions-item>
          </el-descriptions>

          <div class="card-footer">
            <el-button type="primary" size="small" plain>查看详情 →</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Create plan dialog -->
    <el-dialog v-model="showCreateDialog" title="新建网格交易计划" width="480px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="股票代码" prop="stock_code">
          <el-autocomplete 
            v-model="form.stock_code"
            :fetch-suggestions="querySearchAsync"
            placeholder="输入代码、拼音或名称" 
            style="width: 100%"
            @select="handleSelectStock"
            @blur="handleStockCodeBlur"
            value-key="code"
          >
            <template #default="{ item }">
              <div style="display: flex; justify-content: space-between;">
                <span>{{ item.name }}</span>
                <span style="color: #999; font-size: 12px;">{{ item.code }}</span>
              </div>
            </template>
          </el-autocomplete>
        </el-form-item>
        <el-form-item label="股票名称" prop="stock_name">
          <el-input v-model="form.stock_name" placeholder="例如：浦发银行" maxlength="20" />
        </el-form-item>
        <el-form-item label="建仓基准价" prop="base_price">
          <el-input-number
            v-model="form.base_price"
            :precision="3"
            :step="0.1"
            :min="0.001"
            style="width:100%"
            placeholder="请输入当前股价作为基准"
          />
        </el-form-item>
        <el-form-item label="总资金(元)" prop="total_funds">
          <el-input-number
            v-model="form.total_funds"
            :precision="2"
            :step="1000"
            :min="1"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="网格档位" prop="part_count">
          <div style="width: 100%;">
            <el-input-number
              v-model="form.part_count"
              :precision="0"
              :step="1"
              :min="1"
              :max="50"
              style="width:100%"
            />
            <div v-if="recommendedParts !== null" style="font-size: 12px; color: #67c23a; margin-top: 4px; line-height: 1.2;">
              已自动推荐为 {{ recommendedParts }} 档。(为能够覆盖近100天最低点 ¥{{ lowestPx?.toFixed(2) }} 防破网)
            </div>
          </div>
        </el-form-item>
        <el-form-item label="网格大小(%)" prop="grid_ratio">
          <div style="width: 100%;">
            <el-input-number
              v-model="ratioPercent"
              :precision="1"
              :step="0.5"
              :min="0.5"
              :max="20"
              style="width: 100%"
              placeholder="例如输入3表示3%"
            />
            <div v-if="recommendedRatio !== null" style="font-size: 12px; color: #67c23a; margin-top: 4px; line-height: 1.2;">
              已自动推荐大小为 {{ recommendedRatio }}%。(基于过去14天日均真实波幅 ¥{{ atrVal?.toFixed(2) }} 计算)
            </div>
          </div>
        </el-form-item>
        
        <!-- Preview Grid Configuration -->
        <div v-if="form.base_price && form.total_funds && form.part_count && ratioPercent" class="preview-section">
          <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #606266;">计划试算预览</h4>
          <el-table :data="previewData" size="small" border style="width: 100%" max-height="200">
            <el-table-column prop="part" label="档位" width="60" align="center" />
            <el-table-column prop="buy_price" label="买入价" align="center" />
            <el-table-column prop="sell_price" label="卖出价" align="center" />
            <el-table-column prop="shares" label="股数" align="center" />
            <el-table-column prop="profit" label="预估收益" align="center" />
          </el-table>
          <div style="text-align: right; margin-top: 8px; font-weight: bold; color: #f56c6c; font-size: 14px;">
            单轮总收益：¥{{ totalPreviewProfit }}
          </div>
          <div v-if="hasInvalidPreview" class="error-text" style="color: #f56c6c; font-size: 12px; margin-top: 5px;">
            <el-icon><Warning /></el-icon> 资金不足！每档至少需要购买1手(100股)，请增加总资金或减少网格档数。
          </div>
        </div>

        <el-alert
          type="info"
          :closable="false"
          style="margin-top:8px"
          :description="`系统将按每份约 ${ (form.total_funds / form.part_count).toFixed(2) } 元（总资金÷${form.part_count}）和基准价自动生成${form.part_count}档买卖网格（间距${ratioPercent}%）。每档需至少可买1手（100股）。`"
        />
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" :disabled="hasInvalidPreview" @click="submitCreate">创建计划</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Warning, Box, CopyDocument } from '@element-plus/icons-vue'
import { getPlans, createPlan, deletePlan, updatePlan, getQuotes, getKLine, searchStocks } from '../api/index.js'

const router = useRouter()
const plans = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const formRef = ref(null)
const ratioPercent = ref(3.0)
const recommendedRatio = ref(null)
const recommendedParts = ref(null)
const atrVal = ref(null)
const lowestPx = ref(null)
const activeTab = ref('active')

// Autocomplete search
let searchTimeout = null
async function querySearchAsync(queryString, cb) {
  if (!queryString) {
    cb([])
    return
  }
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(async () => {
    try {
      const res = await searchStocks(queryString)
      cb(res.data || [])
    } catch (e) {
      cb([])
    }
  }, 300)
}

function handleSelectStock(item) {
  form.value.stock_code = item.code
  form.value.stock_name = item.name
  handleStockCodeBlur()
}

function getSinaCode(code) {
  code = code.trim().toLowerCase();
  if (!code) return '';
  if (code.startsWith('sh') || code.startsWith('sz') || code.startsWith('bj')) return code;
  if (/^6/.test(code)) return 'sh' + code;
  if (/^0|^3/.test(code)) return 'sz' + code;
  if (/^8|^4/.test(code)) return 'bj' + code;
  return code;
}

async function handleStockCodeBlur() {
  const code = form.value.stock_code;
  if (!code) return;
  const sinaCode = getSinaCode(code);
  if (!sinaCode) return;
  try {
    const { data } = await getQuotes(sinaCode);
    if (data && data[sinaCode]) {
      const quote = data[sinaCode];
      if (!form.value.stock_name) {
        form.value.stock_name = quote.name;
      }
      if (!form.value.base_price) {
        form.value.base_price = quote.price > 0 ? quote.price : quote.close;
      }
    }
    
    // Fetch K-line to recommend grid size based on ATR
    recommendedRatio.value = null;
    recommendedParts.value = null;
    const kData = await getKLine(sinaCode, 240, 100); // Fetch 100 days for better lowest coverage
    if (kData.data && kData.data.length > 0) {
      let trSum = 0;
      let validDays = 0;
      let lowest = Infinity;
      
      const atrRange = 14;
      
      for (let i = 0; i < kData.data.length; i++) {
        const d = kData.data[i];
        if (parseFloat(d.low) < lowest) {
            lowest = parseFloat(d.low);
        }
        
        if (i > 0 && i >= kData.data.length - atrRange) {
          const todayHigh = parseFloat(kData.data[i].high);
          const todayLow = parseFloat(kData.data[i].low);
          const preClose = parseFloat(kData.data[i - 1].close);
          
          const tr1 = todayHigh - todayLow;
          const tr2 = Math.abs(todayHigh - preClose);
          const tr3 = Math.abs(todayLow - preClose);
          trSum += Math.max(tr1, tr2, tr3);
          validDays++;
        }
      }
      
      lowestPx.value = lowest;
      
      const currentPx = form.value.base_price || parseFloat(kData.data[kData.data.length - 1].close);
      
      if (validDays > 0 && currentPx > 0) {
        const atr = trSum / validDays;
        atrVal.value = atr;
        let rawRatio = (atr / currentPx) * 100;
        if (rawRatio < 0.5) rawRatio = 0.5;
        if (rawRatio > 20) rawRatio = 20;
        // round to nearest 0.5
        recommendedRatio.value = Math.round(Number(rawRatio) * 2) / 2;
        ratioPercent.value = recommendedRatio.value; // <--- Auto apply
        
        // Recommend parts to cover lowest
        const ratio = recommendedRatio.value / 100;
        if (currentPx > lowest && ratio > 0) {
           const n = Math.log(lowest / currentPx) / Math.log(1 - ratio);
           let parts = Math.ceil(n);
           if (parts < 3) parts = 3;
           if (parts > 50) parts = 50;
           recommendedParts.value = parts;
           form.value.part_count = parts; // <--- Auto apply
        }
      }
    }
  } catch (e) {
    console.error('获取股票实时价格失败', e);
  }
}

const displayedPlans = computed(() => {
  if (activeTab.value === 'active') {
    return plans.value.filter(p => p.is_active !== false)
  } else {
    return plans.value.filter(p => p.is_active === false)
  }
})

const form = ref({
  stock_code: '',
  stock_name: '',
  base_price: null,
  total_funds: 50000,
  part_count: 5,
})

const rules = {
  stock_code: [{ required: true, message: '请输入股票代码', trigger: 'blur' }],
  stock_name: [{ required: true, message: '请输入股票名称', trigger: 'blur' }],
  base_price: [{ required: true, type: 'number', message: '请输入建仓基准价', trigger: 'change' }],
  total_funds: [{ required: true, type: 'number', message: '请输入总资金', trigger: 'change' }],
  part_count: [{ required: true, type: 'number', message: '请输入网格档数', trigger: 'change' }],
}

// Preview calculation logic
const previewData = computed(() => {
  if (!form.value.base_price || !form.value.total_funds || !form.value.part_count || !ratioPercent.value) {
    return []
  }

  const base = form.value.base_price
  const ratio = ratioPercent.value / 100
  const partCount = form.value.part_count
  const partFunds = form.value.total_funds / partCount
  
  const records = []
  for (let i = 0; i < partCount; i++) {
    const buyPrice = base * Math.pow(1 - ratio, i)
    const sellPrice = buyPrice * (1 + ratio)
    
    // Round down to whole lots (100 shares)
    const rawShares = Math.floor((partFunds / buyPrice) / 100) * 100
    const profit = (sellPrice - buyPrice) * rawShares
    
    records.push({
      part: i + 1,
      buy_price: buyPrice.toFixed(3),
      sell_price: sellPrice.toFixed(3),
      shares: rawShares,
      profit: profit.toFixed(2),
      raw_profit: profit
    })
  }
  return records
})

const totalPreviewProfit = computed(() => {
  return previewData.value.reduce((sum, item) => sum + item.raw_profit, 0).toFixed(2)
})

const hasInvalidPreview = computed(() => {
  if (previewData.value.length === 0) return false
  return previewData.value.some(record => record.shares < 100)
})

async function fetchPlans() {
  loading.value = true
  try {
    const { data } = await getPlans()
    plans.value = data

    // 获取所有计划股票的实时价格
    const codes = [...new Set(data.map(p => getSinaCode(p.stock_code)).filter(c => c))].join(',')
    if (codes) {
      getQuotes(codes).then(res => {
        if (res.data) {
          plans.value.forEach(plan => {
            const sc = getSinaCode(plan.stock_code)
            if (res.data[sc]) {
              plan.current_price = res.data[sc].price > 0 ? res.data[sc].price : res.data[sc].close;
              plan.price_change = ((plan.current_price - res.data[sc].close) / res.data[sc].close) * 100;
            }
          })
        }
      }).catch(err => console.error('Failed to fetch real-time quotes', err))
    }
  } catch (e) {
    ElMessage.error('加载计划列表失败')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = { stock_code: '', stock_name: '', base_price: null, total_funds: 50000, part_count: 5 }
  ratioPercent.value = 3.0
  recommendedRatio.value = null
  recommendedParts.value = null
  atrVal.value = null
  lowestPx.value = null
  formRef.value?.resetFields()
}

async function submitCreate() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  if (hasInvalidPreview.value) {
    ElMessage.error('请调整资金或档数，确保每档至少可买100股！')
    return
  }

  creating.value = true
  const payload = {
    ...form.value,
    grid_ratio: ratioPercent.value / 100, // 转换百分比为小数
  }

  try {
    await createPlan(payload)
    ElMessage.success('网格计划创建成功！')
    showCreateDialog.value = false
    await fetchPlans()
  } catch (e) {
    const msg = e.response?.data?.detail || '创建失败，请重试'
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
}

async function confirmDelete(plan) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${plan.stock_name}(${plan.stock_code})」的交易计划吗？此操作将同时删除所有相关记录。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
    await deletePlan(plan.id)
    ElMessage.success('已删除')
    await fetchPlans()
  } catch {
    // user cancelled or request failed
  }
}

async function confirmArchive(plan) {
  try {
    await ElMessageBox.confirm(
      `确定要归档「${plan.stock_name}(${plan.stock_code})」吗？归档后该计划不再活跃。`,
      '归档确认',
      { type: 'warning', confirmButtonText: '确定归档', cancelButtonText: '取消' }
    )
    await updatePlan(plan.id, { is_active: false })
    ElMessage.success('已归档')
    await fetchPlans()
  } catch {
    // user cancelled or request failed
  }
}

function goDetail(id) {
  router.push(`/plans/${id}`)
}

function duplicatePlan(plan) {
  form.value = {
    stock_code: plan.stock_code,
    stock_name: plan.stock_name,
    base_price: parseFloat(plan.base_price),
    total_funds: parseFloat(plan.total_funds),
    part_count: plan.part_count,
  }
  ratioPercent.value = plan.grid_ratio ? plan.grid_ratio * 100 : 3.0
  showCreateDialog.value = true
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(fetchPlans)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { font-size: 20px; color: #303133; }

.plan-tabs { margin-bottom: 20px; }

.plan-col { margin-bottom: 24px; }

.plan-card { 
  cursor: pointer; 
  transition: transform .15s; 
  height: 320px;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.plan-card:hover { transform: translateY(-2px); }

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stock-code {
  background: #409eff;
  color: #fff;
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 700;
}
.stock-name { flex: 1; font-weight: 600; font-size: 15px; }

.card-footer { margin-top: 12px; text-align: right; }

.plan-desc {
  margin-top: 8px;
}
:deep(.el-descriptions__label) {
  font-size: 14px;
  color: #606266;
}
:deep(.el-descriptions__content) {
  font-size: 15px;
  font-weight: 500;
}

.highlight-text { color: #303133; font-weight: 600; }
.holding-text { color: #e6a23c; font-weight: 600; }
.cleared-text { color: #67c23a; font-weight: 600; }

.profit-value {
  font-size: 16px;
  font-weight: bold;
}
.profit-text { color: #f56c6c; } /* A-share convention: red gain */
.loss-text   { color: #67c23a; } /* A-share convention: green loss */

.preview-section {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  margin-top: 10px;
  margin-bottom: 10px;
}
</style>
