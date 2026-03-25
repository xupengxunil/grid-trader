<template>
  <div>
    <div class="page-header">
      <h2>收益统计</h2>
    </div>

    <!-- Filter bar -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="统计时间段">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY/MM/DD"
            value-format="YYYY-MM-DD"
            style="width:280px"
          />
        </el-form-item>
        <el-form-item label="股票计划">
          <el-select v-model="filterPlanId" placeholder="全部" clearable style="width:180px">
            <el-option
              v-for="p in plans"
              :key="p.id"
              :label="`${p.stock_name}(${p.stock_code})`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="fetchStats">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Summary cards -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :xs="24" :sm="12" :lg="8" style="margin-bottom:16px">
        <el-card class="summary-card" shadow="always">
          <div class="summary-icon">💰</div>
          <div class="summary-label">总收益（元）</div>
          <div :class="['summary-value', stats.total_profit >= 0 ? 'profit' : 'loss']">
            {{ stats.total_profit >= 0 ? '+' : '' }}{{ Number(stats.total_profit).toFixed(2) }}
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="8" style="margin-bottom:16px">
        <el-card class="summary-card" shadow="always">
          <div class="summary-icon">💸</div>
          <div class="summary-label">预估手续费（元）</div>
          <div class="summary-value loss">-{{ stats.total_operations * 15 }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="8" style="margin-bottom:16px">
         <el-card class="summary-card" shadow="always">
          <div class="summary-icon">💎</div>
          <div class="summary-label">预估净收益（元）</div>
          <div :class="['summary-value', (stats.total_profit - stats.total_operations * 15) >= 0 ? 'profit' : 'loss']">
            {{ (stats.total_profit - stats.total_operations * 15) >= 0 ? '+' : '' }}{{ Number(stats.total_profit - stats.total_operations * 15).toFixed(2) }}
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="12" style="margin-bottom:16px">
        <el-card class="summary-card" shadow="always">
          <div class="summary-icon">📊</div>
          <div class="summary-label">操作总次数（笔）</div>
          <div class="summary-value neutral">{{ stats.total_operations }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="12" style="margin-bottom:16px">
        <el-card class="summary-card" shadow="always">
          <div class="summary-icon">📈</div>
          <div class="summary-label">涉及股票（只）</div>
          <div class="summary-value neutral">{{ stats.breakdown?.length ?? 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Per-stock breakdown -->
    <el-card style="margin-top:16px" v-if="stats.breakdown && stats.breakdown.length > 0">
      <template #header>按股票分组统计</template>
      <el-table :data="stats.breakdown" border stripe>
        <el-table-column label="股票代码" prop="stock_code" width="120" align="center" />
        <el-table-column label="股票名称" prop="stock_name" />
        <el-table-column label="操作次数" prop="operations" align="center" />
        <el-table-column label="预估手续费(元)" align="right">
          <template #default="{ row }">
            <span class="loss">-{{ row.operations * 15 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="总收益(元)" align="right">
          <template #default="{ row }">
            <span :class="row.profit >= 0 ? 'profit' : 'loss'">
              {{ row.profit >= 0 ? '+' : '' }}{{ Number(row.profit).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="净收益(元)" align="right">
          <template #default="{ row }">
            <span :class="(row.profit - row.operations * 15) >= 0 ? 'profit' : 'loss'">
              {{ (row.profit - row.operations * 15) >= 0 ? '+' : '' }}{{ Number(row.profit - row.operations * 15).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-empty
      v-else-if="!loading && stats.total_operations === 0"
      description="所选时间段内暂无已清仓记录"
      style="margin-top:40px"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getStatistics, getPlans } from '../api/index.js'

const dateRange = ref([])
const filterPlanId = ref(null)
const loading = ref(false)
const plans = ref([])

const stats = ref({
  total_profit: 0,
  total_operations: 0,
  breakdown: [],
})

async function fetchStats() {
  loading.value = true
  try {
    const params = {}
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (filterPlanId.value) params.plan_id = filterPlanId.value
    const { data } = await getStatistics(params)
    stats.value = data
  } catch {
    ElMessage.error('查询统计数据失败')
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  dateRange.value = []
  filterPlanId.value = null
  fetchStats()
}

async function loadPlans() {
  try {
    const { data } = await getPlans()
    plans.value = data
  } catch {
    // silent
  }
}

onMounted(() => {
  loadPlans()
  fetchStats()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { font-size: 20px; color: #303133; }

.filter-card { padding: 4px 0; }

.summary-card {
  text-align: center;
  padding: 12px 0;
  margin-bottom: 0;
}
.summary-icon { font-size: 32px; margin-bottom: 8px; }
.summary-label { font-size: 13px; color: #909399; margin-bottom: 6px; }
.summary-value { font-size: 32px; font-weight: 700; }
/* A-share convention: red = gain, green = loss */
.profit { color: #f56c6c; }
.loss   { color: #67c23a; }
.neutral { color: #409eff; }
</style>
