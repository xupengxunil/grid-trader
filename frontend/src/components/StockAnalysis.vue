<template>
  <div class="analysis-page">
    <div class="page-header">
      <h2>网格策略分析</h2>
      <p style="color: #909399; font-size: 14px; margin-top: 5px;">基于历史真实的K线波动（ATR），自动测算建议的网格密度并在下方模拟拦截网。</p>
    </div>

    <!-- Watchlist Section -->
    <div class="watchlist-section" v-if="watchlist.length > 0">
      <div style="margin-bottom: 12px; font-weight: bold; font-size: 16px; color: #303133;">
        <el-icon style="margin-right: 4px; vertical-align: -2px;"><Star /></el-icon>我的自选
      </div>
      <el-row :gutter="16">
        <el-col :span="6" :xs="12" :sm="8" :md="6" v-for="w in watchlist" :key="w.id">
          <el-card shadow="hover" class="watchlist-card" @click="selectWatchlist(w.stock_code)">
            <div style="font-weight: bold; font-size: 16px; color: #303133;">{{ w.stock_name }}</div>
            <div style="color: #909399; font-size: 14px; margin-top: 4px;">{{ w.stock_code }}</div>
            <el-button type="danger" link class="delete-btn" @click.stop="removeWatchlist(w.stock_code)">删除</el-button>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-card class="search-card" shadow="hover">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="股票代码">
          <el-autocomplete 
            v-model="stockCodeInput"
            :fetch-suggestions="querySearchAsync"
            placeholder="输入代码、拼音或名称" 
            style="width: 300px"
            @select="handleSelect"
            @keyup.enter="handleSearch"
            value-key="code"
            clearable
          >
            <template #default="{ item }">
              <div style="display: flex; justify-content: space-between;">
                <span>{{ item.name }}</span>
                <span style="color: #999; font-size: 12px;">{{ item.code }}</span>
              </div>
            </template>
            <template #append>
              <el-button type="primary" :loading="loading" @click="handleSearch">
                开始分析
              </el-button>
            </template>
          </el-autocomplete>
        </el-form-item>
      </el-form>

      <template v-if="quoteData">
        <div class="quote-header">
          <span class="stock-name">{{ quoteData.name }}</span>
          <span class="stock-code">{{ sinaCode }}</span>
          <span :class="['current-price', pctChange >= 0 ? 'profit' : 'loss']">
            ¥{{ currentPrice.toFixed(3) }} 
            <span style="font-size:14px">({{ pctChange >= 0 ? '+' : '' }}{{ pctChange.toFixed(2) }}%)</span>
          </span>
          <el-button 
            type="success" 
            plain 
            size="small" 
            style="margin-left: auto;" 
            @click="addToWatchlist"
            v-if="!isInWatchlist"
          >
            <el-icon style="margin-right:4px"><Plus /></el-icon>加入自选
          </el-button>
          <el-button 
            type="info" 
            plain 
            size="small" 
            style="margin-left: auto;" 
            disabled
            v-else
          >
            已加入自选
          </el-button>
        </div>
        <el-row :gutter="24" style="margin-top: 16px;">
          <el-col :span="6">
            <div class="stat-box">
              <div class="label">今日开盘</div>
              <div class="value">¥{{ quoteData.open.toFixed(2) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-box">
              <div class="label">昨日收盘</div>
              <div class="value">¥{{ quoteData.close.toFixed(2) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-box">
              <div class="label">今日最高</div>
              <div class="value profit">¥{{ quoteData.high.toFixed(2) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-box">
              <div class="label">今日最低</div>
              <div class="value loss">¥{{ quoteData.low.toFixed(2) }}</div>
            </div>
          </el-col>
        </el-row>
      </template>
    </el-card>

    <template v-if="quoteData && !loading">
      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :md="8" :sm="24">
          <el-card class="recommendation-card" shadow="hover">
            <template #header>
              <div style="font-weight: bold;">
                <el-icon style="margin-right: 4px; vertical-align: middle;"><Lightning /></el-icon>网格参数推荐
              </div>
            </template>
            <el-form label-position="left" label-width="120px" size="small">
              <el-form-item label="建议建仓价">
                <span class="highlight-text">¥{{ recommendBasePrice.toFixed(3) }}</span>
                <span style="margin-left: 8px; color: #909399;">(当前市价)</span>
              </el-form-item>
              
              <el-divider style="margin: 8px 0; border-style: dashed;" />
              
              <el-form-item label="最高价(100天)">
                <span>¥{{ max100Data.toFixed(3) }}</span>
              </el-form-item>
              <el-form-item label="最低价(100天)">
                <span>¥{{ min100Data.toFixed(3) }}</span>
              </el-form-item>
              <el-form-item label="平均真实波幅(ATR)">
                <span>¥{{ atrValue.toFixed(3) }} / 天</span>
              </el-form-item>
              
              <el-divider style="margin: 8px 0;" />
              
              <el-form-item label="推荐网格大小">
                <div style="display:flex; align-items:center; width:100%">
                  <el-input-number v-model="editRatio" :step="0.5" :min="0.5" :max="20" style="width: 100px; margin-right:8px" @change="recalcDraw" /> %
                  <el-tooltip content="基于14天平均波幅/当前价格计算" placement="top">
                    <el-icon style="margin-left:4px; color:#909399; cursor:help"><InfoFilled /></el-icon>
                  </el-tooltip>
                </div>
              </el-form-item>
              <el-form-item label="推荐覆盖档数">
                <div style="display:flex; align-items:center; width:100%">
                  <el-input-number v-model="editParts" :step="1" :min="1" :max="50" style="width: 100px; margin-right:8px" @change="recalcDraw" /> 档
                  <el-tooltip content="能够覆盖到近期100天最低价所需的档数" placement="top">
                    <el-icon style="margin-left:4px; color:#909399; cursor:help"><InfoFilled /></el-icon>
                  </el-tooltip>
                </div>
              </el-form-item>
              <el-form-item label="最低兜底价">
                <span style="font-weight:bold" class="loss">¥{{ bottomPrice.toFixed(3) }}</span>
              </el-form-item>

              <el-alert
                type="success"
                :closable="false"
                style="margin-top: 10px;"
                :description="`按上述参数，这 ${editParts} 层网格可以兜住股价跌至 ¥${bottomPrice.toFixed(3)} 的风险，网间距保证每天波幅能轻易触发。`"
              />
            </el-form>
          </el-card>
        </el-col>

        <el-col :md="16" :sm="24">
          <!-- K-line Chart -->
          <el-card shadow="hover" v-loading="chartLoading">
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight:bold;">虚拟网格落点图 (日线)</span>
              </div>
            </template>
            <div ref="chartContainer" style="width: 100%; height: 440px;"></div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { InfoFilled, Lightning, Star, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getQuotes, getKLine, getWatchlist, addWatchlist, deleteWatchlist, searchStocks } from '../api/index.js'

const stockCodeInput = ref('')
const sinaCode = ref('')
const loading = ref(false)
const chartLoading = ref(false)

const quoteData = ref(null)
const currentPrice = ref(0)
const pctChange = ref(0)
const klineList = ref([])

// Watchlist Data
const watchlist = ref([])

onMounted(() => {
  loadWatchlist()
})

const isInWatchlist = computed(() => {
  if (!sinaCode.value) return false
  return watchlist.value.some(item => item.stock_code === sinaCode.value)
})

async function loadWatchlist() {
  try {
    const res = await getWatchlist()
    watchlist.value = res.data
  } catch(e) {
    console.error('Failed to load watchlist', e)
  }
}

async function addToWatchlist() {
  if (!sinaCode.value || !quoteData.value) return
  if (isInWatchlist.value) return
  
  try {
    await addWatchlist({
      stock_code: sinaCode.value,
      stock_name: quoteData.value.name
    })
    ElMessage.success('已加入自选')
    loadWatchlist()
  } catch(e) {
    if (e.response?.data?.error) {
      ElMessage.error(e.response.data.error)
    } else {
      ElMessage.error('添加失败')
    }
  }
}

async function removeWatchlist(code) {
  try {
    await deleteWatchlist(code)
    ElMessage.success('已删除')
    loadWatchlist()
  } catch(e) {
    ElMessage.error('删除失败')
  }
}

function selectWatchlist(code) {
  stockCodeInput.value = code
  handleSearch()
}

// Analysed Data
const recommendBasePrice = ref(0)
const max100Data = ref(0)
const min100Data = ref(0)
const atrValue = ref(0)
const editRatio = ref(3.0)
const editParts = ref(5)

const bottomPrice = computed(() => {
  if (!recommendBasePrice.value) return 0
  const ratio = editRatio.value / 100
  let p = recommendBasePrice.value
  for (let i = 0; i < editParts.value; i++) {
    p = p * (1 - ratio)
  }
  return p
})

const chartContainer = ref(null)
let chartInstance = null

function getFormattedSinaCode(code) {
  code = code.trim().toLowerCase();
  if (!code) return '';
  if (code.startsWith('sh') || code.startsWith('sz') || code.startsWith('bj')) return code;
  if (/^6/.test(code)) return 'sh' + code;
  if (/^0|^3/.test(code)) return 'sz' + code;
  if (/^8|^4/.test(code)) return 'bj' + code;
  return code;
}

// Autocomplete logic
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
  }, 300) // debounce
}

function handleSelect(item) {
  stockCodeInput.value = item.code
  handleSearch()
}

async function handleSearch() {
  if (!stockCodeInput.value) return
  sinaCode.value = getFormattedSinaCode(stockCodeInput.value)
  if (!sinaCode.value) return
  
  loading.value = true
  quoteData.value = null
  
  try {
    // 1. Fetch Quote
    const rsQuote = await getQuotes(sinaCode.value)
    if (rsQuote.data && rsQuote.data[sinaCode.value]) {
      quoteData.value = rsQuote.data[sinaCode.value]
      currentPrice.value = quoteData.value.price > 0 ? quoteData.value.price : quoteData.value.close
      pctChange.value = ((currentPrice.value - quoteData.value.close) / quoteData.value.close) * 100
      recommendBasePrice.value = currentPrice.value
    } else {
      ElMessage.warning('查无此股票')
      loading.value = false
      return
    }

    // 2. Fetch K-line (100 days)
    const rsKline = await getKLine(sinaCode.value, 240, 100)
    if (rsKline.data && rsKline.data.length > 0) {
      klineList.value = rsKline.data
      analyzeData(rsKline.data)
      
      // End loading here so the DOM element conditional (v-if="quoteData && !loading") renders 
      loading.value = false 
      await nextTick()
      drawChart()
    } else {
      loading.value = false
    }
  } catch (e) {
    ElMessage.error('查询失败')
    loading.value = false
  } finally {
    // loading is handled above to ensure DOM mounts before nextTick
  }
}

function analyzeData(kData) {
  let highest = -Infinity
  let lowest = Infinity
  
  let trSum = 0
  let validDays = 0
  
  // Need at least 14 days for ATR, but we compute over whole range or recent 14
  const atrRange = 14
  
  for (let i = 0; i < kData.length; i++) {
    const d = kData[i]
    if (d.high > highest) highest = parseFloat(d.high)
    if (d.low < lowest) lowest = parseFloat(d.low)
    
    if (i > 0 && i >= kData.length - atrRange) {
      const todayHigh = parseFloat(kData[i].high)
      const todayLow = parseFloat(kData[i].low)
      const preClose = parseFloat(kData[i - 1].close)
      
      const tr1 = todayHigh - todayLow
      const tr2 = Math.abs(todayHigh - preClose)
      const tr3 = Math.abs(todayLow - preClose)
      trSum += Math.max(tr1, tr2, tr3)
      validDays++
    }
  }
  
  max100Data.value = highest
  min100Data.value = lowest
  
  if (validDays > 0) {
    atrValue.value = trSum / validDays
    
    let rawRatio = (atrValue.value / currentPrice.value) * 100
    if (rawRatio < 0.5) rawRatio = 0.5
    if (rawRatio > 20) rawRatio = 20
    editRatio.value = Math.round(Number(rawRatio) * 2) / 2
  } else {
    editRatio.value = 3.0
    atrValue.value = 0
  }

  // Recommend parts based on bottom
  // How many steps to reach lowest?
  const ratio = editRatio.value / 100
  if (currentPrice.value > lowest && ratio > 0) {
    // base * (1-ratio)^n = lowest
    // ln(lowest/base) = n * ln(1-ratio)
    const n = Math.log(lowest / currentPrice.value) / Math.log(1 - ratio)
    editParts.value = Math.ceil(n)
    if (editParts.value < 3) editParts.value = 3
    if (editParts.value > 50) editParts.value = 50
  } else {
    editParts.value = 5
  }
}

function recalcDraw() {
  drawChart()
}

function drawChart() {
  if (!chartContainer.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartContainer.value)
    window.addEventListener('resize', () => { if (chartInstance) chartInstance.resize() })
  } else {
    // Ensure we are rendering on the correct DOM instance if it gets recreated
    chartInstance.dispose()
    chartInstance = echarts.init(chartContainer.value)
  }
  
  const categoryData = klineList.value.map(item => item.day)
  const values = klineList.value.map(item => [
    parseFloat(item.open),
    parseFloat(item.close),
    parseFloat(item.low),
    parseFloat(item.high)
  ])

  const markLineData = []
  
  // Base line
  markLineData.push({
    yAxis: recommendBasePrice.value,
    name: '基准价',
    label: { formatter: '推荐建仓: {c}', position: 'insideStartTop', color: '#f56c6c' },
    lineStyle: { color: '#f56c6c', type: 'solid', width: 2 }
  })

  // Grid lines
  let p = recommendBasePrice.value
  const r = editRatio.value / 100
  for (let i = 1; i <= editParts.value; i++) {
    p = p * (1 - r)
    markLineData.push({
      yAxis: p,
      name: `第${i}档网络`,
      label: { formatter: `第${i}档拦截 {c}`, position: 'end', color: '#409EFF', fontSize: 10 },
      lineStyle: { color: '#409EFF', type: 'dashed', width: 1, opacity: 0.6 }
    })
  }

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: '8%', right: '12%', bottom: '15%', top: '10%' },
    xAxis: { type: 'category', data: categoryData, scale: true, boundaryGap: false, splitLine: { show: false } },
    yAxis: { scale: true, splitArea: { show: true } },
    dataZoom: [ { type: 'inside', start: 0, end: 100 }, { show: true, type: 'slider', top: '90%', start: 0, end: 100 } ],
    series: [
      {
        name: '日K',
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
</script>

<style scoped>
.analysis-page {
  padding-bottom: 40px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 24px;
  color: #303133;
}

.watchlist-section {
  margin-bottom: 20px;
}
.watchlist-card {
  cursor: pointer;
  position: relative;
  margin-bottom: 16px;
  transition: all 0.3s;
}
.watchlist-card:hover {
  transform: translateY(-2px);
}
.delete-btn {
  position: absolute;
  right: 10px;
  top: 10px;
  opacity: 0;
  transition: opacity 0.3s;
}
.watchlist-card:hover .delete-btn {
  opacity: 1;
}

.search-card {
  margin-bottom: 16px;
}

.quote-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
}
.stock-name {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}
.stock-code {
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 14px;
  color: #606266;
}
.current-price {
  font-size: 24px;
  font-weight: bold;
}
.profit { color: #f56c6c; }
.loss { color: #14b143; } /* note: A-share loss is green */

.stat-box {
  background: #f8f9fa;
  padding: 12px 16px;
  border-radius: 8px;
}
.stat-box .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.stat-box .value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.highlight-text {
  font-weight: bold;
  font-size: 16px;
  color: #409EFF;
}
</style>