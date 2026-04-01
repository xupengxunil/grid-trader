<template>
  <div class="analysis-page">
    <!-- Watchlist Sticky Header -->
    <div class="watchlist-sticky-header" v-if="watchlist.length > 0">
      <div style="font-weight: bold; font-size: 16px; color: #303133; display: flex; align-items: center;">
        <el-icon style="margin-right: 4px; vertical-align: -2px;"><Star /></el-icon>我的自选
      </div>
      <el-select
        v-model="stockCodeInput"
        placeholder="下拉选择自选股快速分析"
        @change="selectWatchlist"
        style="width: 260px;"
        size="large"
        filterable
      >
        <el-option
          v-for="w in watchlist"
          :key="w.id"
          :label="`${w.stock_name} (${w.stock_code})`"
          :value="w.stock_code"
        >
          <span style="float: left">{{ w.stock_name }}</span>
          <span style="float: right; color: #8492a6; font-size: 13px">{{ w.stock_code }}</span>
        </el-option>
      </el-select>
      <el-button v-if="isInWatchlist" type="warning" size="large" plain @click="removeWatchlist(sinaCode)">
        取消关注
      </el-button>
    </div>

    <div class="page-header" style="margin-top: 20px;">
      <h2>网格策略分析</h2>
      <p style="color: #909399; font-size: 14px; margin-top: 5px;">基于历史真实的K线波动（ATR），自动测算建议的网格密度并在下方模拟拦截网。</p>
    </div>

    <!-- Market Analysis Section -->
    <el-card class="market-analysis-card" shadow="hover" style="margin-bottom: 20px;">
      <template #header>
        <div style="font-weight: bold; font-size: 16px;">
          <el-icon style="margin-right: 4px; vertical-align: -2px;"><DataLine /></el-icon>大盘分析 (Market Analysis)
        </div>
      </template>
      <el-row :gutter="24" v-loading="marketLoading">
        <el-col :span="8" :xs="24" v-for="(idx, code) in marketIndices" :key="code">
          <div class="index-box">
            <div class="index-name">{{ idx.name }}</div>
            <div :class="['index-price', idx.pct >= 0 ? 'profit' : 'loss']">
              {{ idx.price.toFixed(2) }}
            </div>
            <div :class="['index-change', idx.pct >= 0 ? 'profit' : 'loss']">
              {{ idx.change > 0 ? '+' : '' }}{{ idx.change.toFixed(2) }} 
              ({{ idx.pct > 0 ? '+' : '' }}{{ idx.pct.toFixed(2) }}%)
            </div>
          </div>
        </el-col>
      </el-row>
      <div v-if="marketAdvice" class="market-advice">
        <el-alert :title="marketAdviceTitle" :type="marketAdviceType" :description="marketAdvice" show-icon :closable="false" />
      </div>
    </el-card>

    <!-- Watchlist Section replaced by sticky header -->

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
      <!-- Grid Suitability Table -->
      <el-card v-if="suitabilityConditions.length > 0" shadow="hover" style="margin-top: 16px; border-radius: 8px;">
        <template #header>
          <div style="font-weight: bold; display: flex; align-items: center; justify-content: space-between;">
            <div>
              <el-icon style="margin-right: 4px; vertical-align: middle;"><DataLine /></el-icon>网格适用性体检报告
            </div>
            <el-tag :type="isRecommended ? 'success' : 'warning'" effect="dark">
              {{ isRecommended ? '综合判定：符合要求，适合网格' : '综合判定：未全部达标，建议谨慎' }}
            </el-tag>
          </div>
        </template>
        <el-table :data="suitabilityConditions" style="width: 100%" size="small" border>
          <el-table-column prop="name" label="体检项目" width="140" />
          <el-table-column prop="explanation" label="参数释义" />
          <el-table-column prop="desc" label="具体指标 (基于最新和MA计算)" />
          <el-table-column label="结果" width="90" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.passed ? 'success' : 'danger'" size="small">
                {{ scope.row.passed ? '通过' : '未达标' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-alert
          v-if="suitabilityAdvice"
          show-icon
          :type="isRecommended ? 'success' : 'warning'"
          :closable="false"
          style="margin-top: 16px;"
        >
          <div v-html="suitabilityAdvice"></div>
        </el-alert>
      </el-card>

      <!-- Multi-dimension Entry Recommend Card -->
      <el-row v-if="entryRecommendations.length > 0" :gutter="16" style="margin-top: 16px;">
        <el-col :span="24">
          <el-card shadow="hover" style="border-radius: 8px;">
            <template #header>
              <div style="display: flex; align-items: center; gap: 8px; font-weight: 600;">
                <el-icon color="#409eff"><Location /></el-icon>
                <span>多维度建仓点位建议 (参考基准价)</span>
              </div>
            </template>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="8" v-for="(rec, index) in entryRecommendations" :key="index" style="margin-bottom: 12px;">
                <div class="stat-box" :style="{ borderTop: '4px solid ' + (rec.type === 'warning' ? '#E6A23C' : rec.type === 'primary' ? '#409EFF' : '#14b143'), height: '100%', boxSizing: 'border-box', cursor: 'pointer' }" @click="applyBasePrice(rec.price)">
                  <div style="font-weight: bold; margin-bottom: 8px; color: #303133; font-size: 15px;">{{ rec.name }}</div>
                  <div style="font-size: 24px; font-weight: bold; margin-bottom: 8px;" :style="{ color: rec.type === 'warning' ? '#E6A23C' : rec.type === 'primary' ? '#409EFF' : '#14b143' }">
                    ¥{{ rec.price }}
                  </div>
                  <div style="font-size: 12px; color: #909399; line-height: 1.5; text-align: justify;">
                    {{ rec.reason }}
                  </div>
                  <div style="margin-top: 8px; text-align: right;">
                    <el-button size="small" type="primary" link>应用为基准价 →</el-button>
                  </div>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :md="8" :sm="24">
          <el-card class="recommendation-card" shadow="hover">
            <template #header>
              <div style="font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
                <span><el-icon style="margin-right: 4px; vertical-align: middle;"><Lightning /></el-icon>网格参数推荐</span>
                <el-button type="primary" size="small" @click="createPlanFromAnalysis">
                  <el-icon style="margin-right: 4px;"><Plus /></el-icon>按此推荐创建计划
                </el-button>
              </div>
            </template>
            <div v-if="strategyOptions.length > 0" style="margin-bottom: 15px;">
              <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <el-tooltip v-for="opt in strategyOptions" :key="opt.name" :content="opt.desc" placement="top">
                  <el-button :type="opt.type" plain size="small" @click="applyStrategy(opt)">
                    {{ opt.name }} ({{ opt.ratio }}% | {{ opt.parts }}档)
                  </el-button>
                </el-tooltip>
              </div>
              <div style="font-size: 12px; color: #909399; margin-top: 4px; line-height: 1.2;">
                均线参考: MA5 <span :class="{'loss': maData.ma5<currentPrice}">¥{{ maData.ma5?.toFixed(2) }}</span> | 
                MA10 <span :class="{'loss': maData.ma10<currentPrice}">¥{{ maData.ma10?.toFixed(2) }}</span> | 
                MA30 <span :class="{'loss': maData.ma30<currentPrice}">¥{{ maData.ma30?.toFixed(2) }}</span>
                <span v-if="marketTrend" style="margin-left: 8px; padding-left: 8px; border-left: 1px solid #dcdfe6; color: #e6a23c;">
                  {{ marketTrend }}
                </span>
              </div>
              <el-alert v-if="stockTrendAdvice" :title="'趋势诊断：' + stockTrendAdvice" :type="stockTrendType" :closable="false" style="margin-top: 8px; padding: 4px 8px;" />
              <el-alert v-if="currentOperationAdvice" :title="'💡 操作建议：' + currentOperationAdvice" :type="currentOperationType" show-icon :closable="false" style="margin-top: 8px; font-weight: bold;" />
            </div>

            <el-form label-position="left" label-width="120px" size="small">
              <el-form-item label="自定义建仓价">
                <el-input-number v-model="recommendBasePrice" :step="0.1" :min="0.001" style="width: 130px; margin-right:8px" @change="recalcDraw" />
                <span style="color: #909399;">(默认MA30或现价)</span>
              </el-form-item>
              <el-form-item label="对应首档卖出价">
                <span style="font-weight: bold; color: #F56C6C; font-size: 14px;">¥{{ (recommendBasePrice * (1 + editRatio / 100)).toFixed(3) }}</span>
                <span style="color: #909399; margin-left: 6px;">(基于 {{ editRatio }}% 的网格回升卖出)</span>
              </el-form-item>
              
              <el-divider style="margin: 8px 0; border-style: dashed;" />
              
              <el-form-item label="最高价(100天)">
                <span>¥{{ max100Data.toFixed(3) }}</span>
              </el-form-item>
              <el-form-item label="最低价(100日内)">
                <span>¥{{ min100Data.toFixed(3) }}</span>
              </el-form-item>
              <el-form-item label="日均波幅(ATR)">
                <span>¥{{ atrValue.toFixed(3) }}</span>
              </el-form-item>
              
              <el-divider style="margin: 8px 0;" />
              
              <el-form-item label="测试网格大小">
                <div style="display:flex; align-items:center; width:100%">
                  <el-input-number v-model="editRatio" :step="0.5" :min="0.5" :max="20" style="width: 100px; margin-right:8px" @change="handleManualChange" /> %
                  <el-tooltip content="基于14天平均波幅/当前价格计算" placement="top">
                    <el-icon style="margin-left:4px; color:#909399; cursor:help"><InfoFilled /></el-icon>
                  </el-tooltip>
                </div>
              </el-form-item>
              <el-form-item label="推荐覆盖档数">
                <div style="display:flex; align-items:center; width:100%">
                  <el-input-number v-model="editParts" :step="1" :min="1" :max="50" style="width: 100px; margin-right:8px" @change="handleManualChange" /> 档
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

          <!-- History Backtest Section -->
          <el-card shadow="hover" style="margin-top: 16px;" v-if="backtestResult">
            <template #header>
              <div style="font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <el-icon style="margin-right: 4px; vertical-align: middle;"><DataLine /></el-icon>历史回测 (近{{ backtestResult.days }}交易日 - 当前策略：{{ currentStrategyType }})
                </div>
                <div style="font-weight: normal; font-size: 13px;">
                  回测天数:
                  <el-select v-model="backtestDays" size="small" style="width: 100px; margin-left: 8px;" @change="recalcDraw">
                    <el-option label="30日" :value="30" />
                    <el-option label="60日" :value="60" />
                    <el-option label="100日" :value="100" />
                    <el-option label="120日" :value="120" />
                  </el-select>
                </div>
              </div>
            </template>
            <div style="font-size: 13px; color: #909399; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #ebeef5;">
              参数摘要：建仓基准价 ¥{{ backtestResult.basePrice }}，网格 {{ editRatio }}%，总共 {{ editParts }} 档底线防守。
            </div>

            <!-- Holding & Floating PnL Block -->
            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 16px;">
              <el-row :gutter="10">
                <el-col :span="12">
                  <div style="font-size: 12px; color: #909399;">当前未结套牢档数</div>
                  <div style="margin-top: 4px;">
                    <span style="font-weight: bold; font-size: 18px;" :style="{color: backtestResult.holdingCount > 0 ? '#E6A23C' : '#67C23A'}">{{ backtestResult.holdingCount }}</span>
                    <span style="font-size: 12px; color: #909399;"> / {{ backtestResult.parts }} 档</span>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div style="font-size: 12px; color: #909399;">当前未结浮亏/浮盈</div>
                  <div style="margin-top: 4px; font-weight: bold; font-size: 18px;" :class="backtestResult.floatingPnL >= 0 ? 'profit' : 'loss'">
                    {{ backtestResult.floatingPnL >= 0 ? '+' : '' }}{{ backtestResult.floatingPnL }}
                  </div>
                </el-col>
              </el-row>
            </div>

            <!-- Efficiency & Time Block -->
            <div style="margin-bottom: 16px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <div style="font-size: 12px; color: #909399;">成功解套闭环率 (卖出/买入次数)</div>
                <div style="font-size: 12px; font-weight: bold; color: #409EFF;">{{ backtestResult.sellCount }} / {{ backtestResult.buyCount }} ({{ backtestResult.closedLoopRate }}%)</div>
              </div>
              <el-progress :percentage="Number(backtestResult.closedLoopRate)" :color="Number(backtestResult.closedLoopRate) >= 80 ? '#67C23A' : '#409EFF'" :stroke-width="8" :show-text="false" />
              
              <div style="display: flex; justify-content: space-between; margin-top: 10px; margin-bottom: 4px;">
                <div style="font-size: 12px; color: #909399;">防守资金占用率 (最大/总准备金)</div>
                <div style="font-size: 12px; font-weight: bold; color: #E6A23C;">¥{{ backtestResult.maxOccupiedCapital }} / ¥{{ backtestResult.totalPotentialCapital }}</div>
              </div>
              <el-progress :percentage="Number(backtestResult.capitalUtilization)" color="#E6A23C" :stroke-width="8" :show-text="false" />
            </div>

            <!-- Absolute Profits Block -->
            <el-row :gutter="10" style="border-top: 1px dashed #ebeef5; padding-top: 12px;">
              <el-col :span="8" style="margin-bottom:8px;">
                <div style="font-size:12px; color:#909399;">平均持仓周期</div>
                <div style="font-weight:bold; font-size: 15px;">{{ backtestResult.avgHoldingDays }}天</div>
              </el-col>
              <el-col :span="8" style="margin-bottom:8px;">
                <div style="font-size:12px; color:#909399;">累计套利收益</div>
                <div style="font-weight:bold; font-size: 15px; color:#F56C6C;">¥{{ backtestResult.totalProfit }}</div>
              </el-col>
              <el-col :span="8" style="margin-bottom:8px;">
                <div style="font-size:12px; color:#909399;">回测年化收益</div>
                <div style="font-weight:bold; font-size: 15px; color:#F56C6C;">{{ backtestResult.annualizedYield }}%</div>
              </el-col>
              
              <el-col :span="24" style="margin-top: 4px;">
                <el-alert
                  :type="backtestResult.totalNetProfit >= 0 ? 'success' : 'error'"
                  :closable="false"
                  style="padding: 6px 12px; margin-bottom: 12px;"
                >
                  <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <strong>综合净资产变化 (结账+浮动)</strong>
                    <span style="font-size: 16px; font-weight: bold;">{{ backtestResult.totalNetProfit >= 0 ? '+' : '' }}{{ backtestResult.totalNetProfit }}</span>
                  </div>
                </el-alert>
                <el-alert
                  v-if="backtestResult.advice"
                  :title="'📊 策略回测诊断：'"
                  :description="backtestResult.advice"
                  :type="backtestResult.adviceType"
                  show-icon
                  :closable="false"
                  style="font-weight: bold;"
                />
              </el-col>
            </el-row>
            
            <div style="font-size:11px; color:#909399; margin-top:12px; line-height: 1.4;">
              * 按单档1手(100股)进行日内极值触网模拟，忽略滑点费率。<br/>
              * 年化收益以最大实际动用的防守资金为本金计算。
            </div>
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

          <!-- Trade History Card -->
          <el-card shadow="hover" style="margin-top: 16px;" v-if="backtestResult && backtestResult.trades.length > 0">
            <template #header>
              <div style="font-weight: bold; display: flex; align-items: center;">
                <el-icon style="margin-right: 4px;"><DataLine /></el-icon>网格交易明细
              </div>
            </template>
            <el-table :data="backtestResult.trades" style="width: 100%" size="small" max-height="360" stripe>
                <el-table-column prop="buyDate" label="买入日期" width="110" />
                <el-table-column label="买入价">
                  <template #default="scope">
                    <span style="color: #409EFF;">¥{{ scope.row.buyPrice.toFixed(3) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="sellDate" label="卖出日期" width="110">
                  <template #default="scope">
                    <span>{{ scope.row.sellDate || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="卖出价">
                  <template #default="scope">
                    <span v-if="scope.row.sellPrice" style="color: #F56C6C;">¥{{ scope.row.sellPrice.toFixed(3) }}</span>
                    <span v-else style="color: #909399;">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="持仓状态" width="160">
                  <template #default="scope">
                    <div v-if="scope.row.sellPrice">
                      <el-tag type="success" size="small" effect="plain">已平仓</el-tag>
                      <el-tag v-if="scope.row.cleared" type="success" size="small" effect="dark" style="margin-left: 4px;">全网清仓</el-tag>
                    </div>
                    <el-tag v-else type="warning" size="small" effect="plain">仍在运行</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>

          </el-col>
        </el-row>
      </template>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { InfoFilled, Lightning, Star, Plus, DataLine, Location } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getQuotes, getKLine, getWatchlist, addWatchlist, deleteWatchlist, searchStocks } from '../api/index.js'

const route = useRoute()
const router = useRouter()

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

// Market Data
const marketLoading = ref(false)
const marketIndices = ref({})
const marketAdviceTitle = ref('')
const marketAdvice = ref('')
const marketAdviceType = ref('info')

async function loadMarketData() {
  marketLoading.value = true
  try {
    const codes = 'sh000001,sz399001,sz399006'
    const [quotesRes, klineRes] = await Promise.all([
      getQuotes(codes).catch(() => ({ data: {} })),
      getKLine('sh000001', 240, 30).catch(() => ({ data: [] }))
    ])

    if (quotesRes.data) {
      const idxData = {}
      for (const [code, data] of Object.entries(quotesRes.data)) {
        const currentPx = data.price > 0 ? data.price : data.close
        const change = currentPx - data.close
        const pct = (change / data.close) * 100
        idxData[code] = {
           name: data.name,
           price: currentPx,
           change: change,
           pct: pct
        }
      }
      marketIndices.value = idxData
    }

    if (klineRes.data && klineRes.data.length > 0) {
      const closes = klineRes.data.map(d => parseFloat(d.close))
      const current = closes[closes.length - 1]
      const ma20 = closes.slice(-20).reduce((a, b) => a + b, 0) / Math.min(20, closes.length)
      const volatility = ((Math.max(...closes.slice(-10)) - Math.min(...closes.slice(-10))) / current) * 100

      if (current < ma20 * 0.98) {
        marketAdviceTitle.value = '网格指数：适宜建仓期 (★★★★★)'
        marketAdvice.value = '大盘处于弱势下行即底部的区间（上证跌破MA20）。此时多数个股处于低位，是分批建仓、布置大网格防守的好时机，建议采用宽间距稳健型网格。'
        marketAdviceType.value = 'success'
      } else if (volatility > 4 && current >= ma20 * 0.98 && current <= ma20 * 1.02) {
        marketAdviceTitle.value = '网格指数：黄金震荡期 (★★★★)'
        marketAdvice.value = '大盘处于横盘宽幅震荡（上证靠近MA20且波动率较高）。这是网格交易最容易触发买卖、赚取差价的时期！建议采用平衡型网格，密集套利。'
        marketAdviceType.value = 'warning'
      } else if (current > ma20 * 1.02) {
        marketAdviceTitle.value = '网格指数：防踏空期 (★★)'
        marketAdvice.value = '大盘处于强势上行阶段（上证远高于MA20）。注意！如果在此时运行细密网格，极易过早卖飞所有筹码而踏空行情。建议放大网格间距，减少卖出频率，保留底仓。'
        marketAdviceType.value = 'error'
      } else {
        marketAdviceTitle.value = '网格指数：正常套利阶段 (★★★)'
        marketAdvice.value = '大盘处于常规震荡趋稳中。网格策略可正常运转，建议关注个股本身的K线形态表现。'
        marketAdviceType.value = 'info'
      }
    }
  } catch(e) {
    console.error('Failed to load market data', e)
  } finally {
    marketLoading.value = false
  }
}

onMounted(() => {
  loadWatchlist()
  loadMarketData()
  if (route.query.code) {
    stockCodeInput.value = route.query.code
    handleSearch()
  }
})

watch(() => route.query.code, (newCode) => {
  if (newCode) {
    stockCodeInput.value = newCode
    handleSearch()
  }
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
const backtestDays = ref(30)
const max100Data = ref(0)
const min100Data = ref(0)
const atrValue = ref(0)
const editRatio = ref(3.0)
const editParts = ref(5)
const entryRecommendations = ref([])

// Grid Suitability Data
const suitabilityConditions = ref([])
const isRecommended = computed(() => {
  return suitabilityConditions.value.length > 0 && suitabilityConditions.value.every(c => c.passed)
})

const suitabilityAdvice = computed(() => {
  if (isRecommended.value) {
    return '这是一个极佳的网格交易黄金窗口期！各项指标均符合网格震荡特征，建议挑选【平衡型】网格参数进行密集套利。'
  }
  
  let html = '<ul style="margin: 0; padding-left: 20px; line-height: 1.6;">'
  for (let i = 0; i < suitabilityConditions.value.length; i++) {
    const c = suitabilityConditions.value[i]
    if (!c.passed) {
      if (i === 0) {
        html += '<li>存在深跌风险：容易买满被套，建议选【稳健型】拉大网格，轻底仓试水。</li>'
      } else if (i === 1) {
        html += '<li>波动率太低：网格极难触发，建议换股或选【激进型】小网格捕捉微弱波动。</li>'
      } else if (i === 2) {
        html += '<li>单边强势/主升浪：网格极容易卖飞踏空。建议转长线持股，或保留重底仓只拿极少钱做网。</li>'
      } else if (i === 3) {
        html += '<li>无横盘筑底特征：处于明确趋势中而不是典型的震荡修整期，建议等均线收敛再做网格。</li>'
      } else if (i === 4) {
        html += '<li>BOLL触及通道上轨：面临超买变盘风险，极易变成单边主升浪从而快速卖飞，建议暂停新建网格防踏空。</li>'
      } else if (i === 5) {
        html += '<li>MACD空头加速中：做空动能正在释放，处于死叉发散阶段，此时建仓抄底风险极高，建议等待绿柱缩量或金叉。</li>'
      }
    }
  }
  html += '</ul>'
  return html
})

const currentStrategyType = ref('自定义')
const strategyOptions = ref([])
const maData = ref({})
const marketTrend = ref('')
const stockTrendAdvice = ref('')
const stockTrendType = ref('info')
const currentOperationAdvice = ref('')
const currentOperationType = ref('info')

function applyStrategy(opt) {
  editRatio.value = opt.ratio
  editParts.value = opt.parts
  currentStrategyType.value = opt.name
  ElMessage.success(`已应用 ${opt.name} 策略参数`)
  recalcDraw()
}

function applyBasePrice(priceStr) {
  const parsed = parseFloat(priceStr)
  if (!isNaN(parsed) && parsed > 0) {
    recommendBasePrice.value = parsed
    ElMessage.success(`已应用 ${priceStr} 作为建仓基准价`)
    recalcDraw()
  }
}

function handleManualChange() {
  currentStrategyType.value = '自定义'
  recalcDraw()
}

const bottomPrice = computed(() => {
  if (!recommendBasePrice.value) return 0
  const ratio = editRatio.value / 100
  let p = recommendBasePrice.value
  for (let i = 0; i < editParts.value; i++) {
    p = p * (1 - ratio)
  }
  return p
})

const backtestResult = computed(() => {
  if (!klineList.value || klineList.value.length === 0 || !recommendBasePrice.value) return null

  const ratio = editRatio.value / 100
  const parts = editParts.value
  
  let backtestPeriod = klineList.value
  let basePrice = recommendBasePrice.value

  const days = backtestDays.value
  
  if (klineList.value.length > 30) {
    const splitIndex = Math.max(0, klineList.value.length - days)
    const priorDays = klineList.value.slice(Math.max(0, splitIndex - 30), splitIndex)
    backtestPeriod = klineList.value.slice(splitIndex)
    
    if (priorDays.length > 0) {
      const sum = priorDays.reduce((acc, d) => acc + parseFloat(d.close), 0)
      basePrice = sum / priorDays.length
    }
  }

  let gridPrices = []
  let p = basePrice
  for (let i = 0; i < parts; i++) {
    p = p * (1 - ratio)
    gridPrices.push(p)
  }

  let buyCount = 0
  let sellCount = 0
  let holdingCount = 0
  let totalProfit = 0
  let floatingPnL = 0
  let totalNetProfit = 0
let occupiedCapital = 0
  let maxOccupiedCapital = 0

  let gridStatus = new Array(parts).fill(false) // false means not bought
  let buyDays = new Array(parts).fill(0) // tracking day index of buy
  let totalHoldingDays = 0 // sum of holding days for closed trades
  let openTrades = new Array(parts).fill(null)
  let trades = []

  const tradeUnit = 100
  // Calculate max potential capital if all parts trigger
  const totalPotentialCapital = gridPrices.reduce((sum, price) => sum + price * tradeUnit, 0)

  for (let dayIndex = 0; dayIndex < backtestPeriod.length; dayIndex++) {
    let day = backtestPeriod[dayIndex]
    const low = parseFloat(day.low)
    const high = parseFloat(day.high)
    const dateStr = day.day

    // Check for down/buy execution
    for (let i = 0; i < parts; i++) {
      if (!gridStatus[i] && low <= gridPrices[i]) {
        gridStatus[i] = true
        buyDays[i] = dayIndex
        buyCount++
        occupiedCapital += gridPrices[i] * tradeUnit
        maxOccupiedCapital = Math.max(maxOccupiedCapital, occupiedCapital)
        
        let tradeRec = {
          buyDate: dateStr,
          buyPrice: gridPrices[i],
          sellDate: null,
          sellPrice: null,
          cleared: false
        }
        openTrades[i] = tradeRec
        trades.push(tradeRec)
      }
    }
    
    // Check for up/sell execution
    for (let i = 0; i < parts; i++) {
      if (gridStatus[i] && high >= gridPrices[i] * (1 + ratio)) {
        gridStatus[i] = false
        sellCount++
        totalProfit += gridPrices[i] * ratio * tradeUnit
        occupiedCapital -= gridPrices[i] * tradeUnit
        const isCleared = gridStatus.every(s => !s)
        
        if (openTrades[i]) {
          openTrades[i].sellDate = dateStr
          openTrades[i].sellPrice = gridPrices[i] * (1 + ratio)
          openTrades[i].cleared = isCleared
          openTrades[i] = null
        }
        
        totalHoldingDays += (dayIndex - buyDays[i])
      }
    }
  }

  const currentEndPx = parseFloat(backtestPeriod[backtestPeriod.length - 1].close)
  for (let i = 0; i < parts; i++) {
    if (gridStatus[i]) {
      holdingCount++
      floatingPnL += (currentEndPx - gridPrices[i]) * tradeUnit
    }
  }

  totalNetProfit = totalProfit + floatingPnL

  const avgHoldingDays = sellCount > 0 ? (totalHoldingDays / sellCount) : 0
  const avgProfit = sellCount > 0 ? (totalProfit / sellCount) : 0
  const closedLoopRate = buyCount > 0 ? (sellCount / buyCount) * 100 : 0
  const capitalUtilization = totalPotentialCapital > 0 ? (maxOccupiedCapital / totalPotentialCapital) * 100 : 0
  const annualizedYield = maxOccupiedCapital > 0 ? (totalProfit / maxOccupiedCapital) * (365 / backtestPeriod.length) * 100 : 0
  const yieldRate = maxOccupiedCapital > 0 ? (totalProfit / maxOccupiedCapital * 100) : 0

  let advice = ''
  let adviceType = 'info'

  if (buyCount === 0) {
    advice = '在整个回测区间内未能触发任何买入。建议上调建仓基准价，或缩小网格大小，否则资金将完全闲置。'
    adviceType = 'warning'
  } else if (holdingCount === parts && parts > 0) {
    advice = '警告：当前网格在此参数下已被近期低点彻底击穿（全仓套牢）。建议大幅拉大网格间距，或通过增加网格档数降低兜底价。'
    adviceType = 'error'
  } else if (capitalUtilization < 25 && sellCount > 0) {
    advice = '资金利用率偏低（大量资金长期闲置站岗）。说明这套网格价格布得过宽预留过深，建议适当缩小网格或减少底下防守档数。'
    adviceType = 'warning'
  } else if (closedLoopRate < 40 && holdingCount > 0) {
    advice = '解套闭环率低（震荡偏弱跌或单边阴跌）。平均持仓周期可能偏长，建议审视该标的是否已转空入下降通道。'
    adviceType = 'warning'
  } else if (annualizedYield > 15 && closedLoopRate > 60) {
    advice = '策略运行非常健康！年化收益和高抛低吸流转率优秀，该标的展现出了极佳的箱体震荡回测属性，推荐直接使用此参数。'
    adviceType = 'success'
  } else if (totalNetProfit < 0) {
    advice = '当前呈现综合亏损（大多属于网格左侧建仓期的尚未反弹的浮亏）。属于网格交易正常阶段，请确保总防守资金充裕以耐心等待回归。'
    adviceType = 'info'
  } else {
    advice = '策略历史运行表现平稳。可根据个人对资金利用率和预期收益的偏好微调参数：缩小网格间距高频套小利，放宽间距防深跌。'
    adviceType = 'info'
  }

  return {
    buyCount,
    sellCount,
    holdingCount,
    parts,
    totalProfit: totalProfit.toFixed(2),
    floatingPnL: floatingPnL.toFixed(2),
    totalNetProfit: totalNetProfit.toFixed(2),
    avgHoldingDays: avgHoldingDays.toFixed(1),
    closedLoopRate: closedLoopRate.toFixed(1),
    capitalUtilization: capitalUtilization.toFixed(1),
    maxOccupiedCapital: maxOccupiedCapital.toFixed(2),
    totalPotentialCapital: totalPotentialCapital.toFixed(2),
    annualizedYield: annualizedYield.toFixed(2),
    avgProfit: avgProfit.toFixed(2),
    yieldRate: yieldRate.toFixed(2),
    days: backtestPeriod.length,
    basePrice: basePrice.toFixed(3),
    trades,
    advice,
    adviceType
  }
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
  strategyOptions.value = []
  suitabilityConditions.value = []
  maData.value = {}
  marketTrend.value = ''
  stockTrendAdvice.value = ''
  stockTrendType.value = 'info'
  currentOperationAdvice.value = ''
  currentOperationType.value = 'info'
  
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

    // 2. Fetch K-line and Index in parallel
    const [rsKline, indexDataRes] = await Promise.all([
      getKLine(sinaCode.value, 240, 130).catch(() => ({ data: [] })),
      getKLine('sh000001', 240, 30).catch(() => ({ data: [] }))
    ]);

    let marketMult = 1.0;
    if (indexDataRes.data && indexDataRes.data.length > 0) {
      const idxCloses = indexDataRes.data.map(d => parseFloat(d.close));
      const idxCurrent = idxCloses[idxCloses.length - 1];
      const idxMA20 = idxCloses.slice(-20).reduce((a, b) => a + b, 0) / Math.min(20, idxCloses.length);
      
      if (idxCurrent < idxMA20 * 0.98) {
        marketMult = 1.2;
        marketTrend.value = `大盘弱势(上证跌破MA20)，推荐网格拉大防守`;
      } else if (idxCurrent > idxMA20 * 1.02) {
        marketMult = 0.8;
        marketTrend.value = `大盘强势(上证高于MA20)，推荐适当缩小网格`;
      } else {
        marketMult = 1.0;
        marketTrend.value = `大盘进入震荡期`;
      }
    }

    if (rsKline.data && rsKline.data.length > 0) {
      klineList.value = rsKline.data
      analyzeData(rsKline.data, marketMult)
      
      loading.value = false 
      await nextTick()
      drawChart()
    } else {
      loading.value = false
    }
  } catch (e) {
    ElMessage.error('查询失败')
    loading.value = false
  }
}

function analyzeData(kData, marketMult) {
  const closePrices = kData.map(d => parseFloat(d.close));
  const highs = kData.map(d => parseFloat(d.high));
  const lows = kData.map(d => parseFloat(d.low));
  
  const currentPx = closePrices[closePrices.length - 1];
  
  const highest100 = Math.max(...highs.slice(-100));
  const lowest100 = Math.min(...lows.slice(-100));
  max100Data.value = highest100;
  min100Data.value = lowest100;

  const lowest30 = Math.min(...lows.slice(Math.max(0, lows.length - 30)));
  const highest30 = Math.max(...highs.slice(Math.max(0, highs.length - 30)));

  const ma5 = closePrices.slice(-5).reduce((a,b)=>a+b,0) / Math.min(5, closePrices.length);
  const ma10 = closePrices.slice(-10).reduce((a,b)=>a+b,0) / Math.min(10, closePrices.length);
  const ma30 = closePrices.slice(-30).reduce((a,b)=>a+b,0) / Math.min(30, closePrices.length);
  
  maData.value = { ma5, ma10, ma30 };

  const pastClose30 = closePrices.slice(-40, -10);
  const ma30_past = pastClose30.length > 0 ? (pastClose30.reduce((a,b)=>a+b,0) / Math.min(30, pastClose30.length)) : ma30;
  const ma30_slope = ma30_past > 0 ? ((ma30 - ma30_past) / ma30_past) * 100 : 0;
  
  const ma_max = Math.max(ma5, ma10, ma30);
  const ma_min = Math.min(ma5, ma10, ma30);
  const ma_dispersion = ma_min > 0 ? ((ma_max - ma_min) / ma_min) * 100 : 0;

  if (ma_dispersion < 3.5 && Math.abs(ma30_slope) < 1.5) {
    stockTrendAdvice.value = '【极佳建仓点】均线高度粘合(<3.5%)且走平，处于典型的震荡期，完美适合网格交易！';
    stockTrendType.value = 'success';
  } else if (ma5 > ma10 && ma10 > ma30 && ma30_slope > 1.5) {
    stockTrendAdvice.value = '【风险提示】强多头趋势且均线斜率陡峭，网格极易全部卖出从而踏空行情。';
    stockTrendType.value = 'warning';
  } else if (ma5 < ma10 && ma10 < ma30 && ma30_slope < -1.5) {
    stockTrendAdvice.value = '【左侧抄底】处于明确下降趋势中 (阴跌未企稳)。底部深不可测，极易买满被套，必须选[稳健型]将网格间距拉大，用更深的防守位承接！';
    stockTrendType.value = 'error';
  } else if (ma30 > ma5 && ma30 > ma10) {
    stockTrendAdvice.value = '趋势偏弱，价格被MA30压制，处于底部寻找支撑期。';
    stockTrendType.value = 'info';
  } else {
    stockTrendAdvice.value = '宽幅震荡或趋势转换期，适合网格套利，建议参考下方提示设定安全边际。';
    stockTrendType.value = 'info';
  }

  if (currentPx > 0) {
    recommendBasePrice.value = parseFloat(ma30.toFixed(3));
  }
  
  let trSum = 0;
  let validDays = 0;
  const atrRange = 14;
  
  for (let i = 0; i < kData.length; i++) {
    if (i > 0 && i >= kData.length - atrRange) {
      const todayHigh = parseFloat(kData[i].high);
      const todayLow = parseFloat(kData[i].low);
      const preClose = parseFloat(kData[i - 1].close);
      
      const tr1 = todayHigh - todayLow;
      const tr2 = Math.abs(todayHigh - preClose);
      const tr3 = Math.abs(todayLow - preClose);
      trSum += Math.max(tr1, tr2, tr3);
      validDays++;
    }
  }
  
  if (validDays > 0 && currentPx > 0) {
    const atr = trSum / validDays;
    atrValue.value = atr;
    
    // Grid Suitability Conditions
    const atrRatio = (atr / currentPx) * 100;
    
    // MACD calculation
    let ema12 = closePrices[0];
    let ema26 = closePrices[0];
    let dea = 0;
    
    let macdDif = [];
    let macdDea = [];
    let macdHist = [];
    
    for (let i = 0; i < closePrices.length; i++) {
      const c = closePrices[i];
      if (i === 0) {
        macdDif.push(0);
        macdDea.push(0);
        macdHist.push(0);
      } else {
        ema12 = c * (2/13) + ema12 * (11/13);
        ema26 = c * (2/27) + ema26 * (25/27);
        const dif = ema12 - ema26;
        dea = dif * (2/10) + dea * (8/10);
        const hist = (dif - dea) * 2;
        macdDif.push(dif);
        macdDea.push(dea);
        macdHist.push(hist);
      }
    }
    
    const lastDif = macdDif[macdDif.length - 1];
    const lastDea = macdDea[macdDea.length - 1];
    const lastHist = macdHist[macdHist.length - 1];
    const prevDif = macdDif[macdDif.length - 2] || 0;
    const prevDea = macdDea[macdDea.length - 2] || 0;
    const prevHist = macdHist[macdHist.length - 2] || 0;

    let macdPassedStr = '正常';
    let macdPassed = true;
    let macdCrossStr = '';

    if (lastDif > lastDea && prevDif <= prevDea) {
      macdCrossStr = '金叉形成';
    } else if (lastDif < lastDea && prevDif >= prevDea) {
      macdCrossStr = '死叉确立';
    } else if (lastDif > lastDea) {
      macdCrossStr = lastHist > prevHist ? '多头红柱放大' : '多头红柱缩量';
    } else {
      macdCrossStr = lastHist < prevHist ? '空头绿柱发散' : '空头绿柱缩量(探底)';
    }

    // Fail if high-level dead cross or accelerating downward trend under zero axis
    if (lastDif < lastDea && lastHist < prevHist && lastHist < 0) {
      macdPassedStr = '加速下跌中';
      macdPassed = false;
    } else if (lastDif < 0 && lastDea > 0 && lastDif < lastDea) {
      macdPassedStr = '高位水下死叉';
      macdPassed = false;
    }

    // BOLL calculation
    let upStr = '-', mbStr = '-', dnStr = '-', bollDescStatus = '', bollPassed = true, bollPosRatio = 0, bollPositionStr = '-';
    if (closePrices.length >= 20) {
      const recent20 = closePrices.slice(-20);
      const bolMB = recent20.reduce((a, b) => a + b, 0) / 20;
      const bolMD = Math.sqrt(recent20.reduce((a, b) => a + Math.pow(b - bolMB, 2), 0) / 20);
      const bolUP = bolMB + 2 * bolMD;
      const bolDN = bolMB - 2 * bolMD;
      
      const bollPosition = (currentPx - bolDN) / (bolUP - bolDN);
      bollPosRatio = bollPosition;
      upStr = bolUP.toFixed(2);
      mbStr = bolMB.toFixed(2);
      dnStr = bolDN.toFixed(2);
      bollPositionStr = bollPosition.toFixed(2);
      
      if (bollPosition < 0.1) {
        bollDescStatus = '超跌/极佳买点';
        bollPassed = true;
      } else if (bollPosition > 0.9) {
        bollDescStatus = '超买/上轨触顶';
        bollPassed = false;
      } else {
        bollDescStatus = '网格舒适区';
        bollPassed = true;
      }
    }
    
    suitabilityConditions.value = [
      {
        name: '长期下跌风险',
        desc: `当价 > MA30*0.95 且无近期急跌 (最新价: ${currentPx.toFixed(2)}, 均线斜率: ${ma30_slope.toFixed(2)}%)`,
        explanation: '筛除处于长期下降降势（阴跌）的股票。网格依赖价格区间震荡，持续下跌极易导致网格越买越亏、买满被套。',
        passed: currentPx > ma30 * 0.95 && ma30_slope > -2.0
      },
      {
        name: '震荡幅度达标',
        desc: `日均真实波幅/价格 > 1.5% (当前: ${atrRatio.toFixed(2)}%)`,
        explanation: '检测标的日常波动的活跃程度（基于ATR）。波动率过低（变织布机）会导致长时间无法触发网格买卖。',
        passed: atrRatio > 1.5
      },
      {
        name: '非主升浪/单边上涨',
        desc: `当前价格不过分偏离MA30 < MA30*1.15 (防卖飞)`,
        explanation: '防止股票因利好处于狂飙状态。单边大幅上涨期间若继续运行密集网格，容易过早卖光筹码导致踏空。',
        passed: currentPx <= ma30 * 1.15
      },
      {
        name: '均线乖离度',
        desc: `(Max-Min均线)/Min < 5% (当前: ${ma_dispersion.toFixed(2)}%)`,
        explanation: '观测近期各均线是否互相靠近。均线集结缠绕说明多空成本一致，大概率处于或即将进入横盘典型震荡期。',
        passed: ma_dispersion < 5.0
      },
      {
        name: '布林带通道(BOLL)',
        desc: `${bollDescStatus} (UP:${upStr} MB:${mbStr} DN:${dnStr}) 位置系数:${bollPositionStr}`,
        explanation: '借助布林带评估当前价格极值。处于中下轨区间网格安全边际高；若突破上轨（超买）须防变盘或单边主升浪卖飞。',
        passed: bollPassed
      },
      {
        name: 'MACD多空趋势',
        desc: `状态：${macdCrossStr} (DIF:${lastDif.toFixed(2)}, DEA:${lastDea.toFixed(2)}, MACD:${lastHist.toFixed(2)})`,
        explanation: '辅助判断多空动能结构。若处于明显死叉向下发散阶段说明抛压严重，股价极易跌穿网格防御底线。',
        passed: macdPassed
      }
    ];

    let actionTip = '';
    let actionType = 'info';
    let effectiveBoll = closePrices.length >= 20 ? bollPosRatio : 0.5;

    if (ma5 < ma10 && ma10 < ma30 && (ma30_slope < -2.0 || (lastDif < lastDea && lastHist < prevHist))) {
      actionTip = `【持币观望】处于空头排列或MACD向下发散阶段，底不可测，暂不建议重仓抄底或开启标准网格。`;
      actionType = 'error';
    } else if (effectiveBoll > 0.95 || currentPx > ma30 * 1.15) {
      actionTip = '【逢高止盈/减仓】当前价格处于极度超买区域且偏离均线较远，回落压力大，建议将利润落袋为安，避免新建网格。';
      actionType = 'warning';
    } else if (effectiveBoll < 0.05 && ma30_slope > -1.5 && lastHist > prevHist) {
      actionTip = `【分批低吸建仓】股价处于超跌前均线趋稳，且MACD绿柱缩量/红柱放大[${macdCrossStr}]，属于左侧好买点，建议布置网格底仓。`;
      actionType = 'success';
    } else if (lastDif > lastDea && prevDif <= prevDea && ma_dispersion < 8.0) {
      actionTip = `【上涨启动期】MACD刚形成金叉，多头动能转强。网格设定需注意防卖飞，建议保留一定底仓不出。`;
      actionType = 'success';
    } else if (ma_dispersion < 4.0 && Math.abs(ma30_slope) < 1.5) {
      actionTip = `【积极做网套利】典型震荡整理期，均线高度粘合 [当前: ${macdCrossStr}]。这是网格高频套利吃利润的黄金阶段！`;
      actionType = 'success';
    } else if (ma5 > ma10 && ma10 > ma30 && ma30_slope > 1.5) {
      actionTip = '【持股待涨防走飞】多头排列主升浪，顺势持股为主，做网格极易全部卖出导致踏空，建议放大卖出间距。';
      actionType = 'primary';
    } else {
      actionTip = `【常态按计划执行】当前无显著单边或极端特征 [当前: ${macdCrossStr}]，可基于您个人的仓位管理，按既定网格参数常态化稳定运行。`;
      actionType = 'info';
    }
    
    currentOperationAdvice.value = actionTip;
    currentOperationType.value = actionType;

    // Entry Recommendations Generation
    const recs = [];
    recs.push({
      name: '激进型买点 (短期回调)',
      price: ma10.toFixed(3),
      type: 'warning',
      reason: '依托MA10(10日均线)形成的短期支撑。适合多头上攻途中首次回调的试探买入，若有效跌破需警惕短期走弱。'
    });
    recs.push({
      name: '稳健型买点 (中期生命线)',
      price: ma30.toFixed(3),
      type: 'primary',
      reason: '依托MA30(30日均线)的核心支撑。这是主力中期持仓成本区，以此定为网格基准价胜率高、回撤可控。'
    });
    const defPx = dnStr !== '-' ? parseFloat(dnStr) : lowest30;
    const finalDefPx = Math.min(defPx, lowest30);
    recs.push({
      name: '极度防守买点 (左侧极端位)',
      price: finalDefPx.toFixed(3),
      type: 'success',
      reason: '结合布林带下轨与近月极弱前低点。极端情绪宣泄后的超跌建仓区域，安全边际高，建议不突破右侧只做低挂单。'
    });
    entryRecommendations.value = recs;

    // 基于最高/最低真实落差的网格大小计算法
    const rangeAmplitude = ((highest30 - lowest30) / highest30) * 100;
    const dailyVol = (atr / currentPx) * 100;
    
    strategyOptions.value = [
      {
        name: '稳健型',
        desc: `大网格，深底 (覆盖100日最低点：￥${(lowest100 * (1 - 0.05 * marketMult)).toFixed(2)})，网格间距参考近期最大箱体振幅计算`,
        ratio: Math.max(1.0, Math.round((rangeAmplitude / 4) * marketMult * 2) / 2),
        bottom: lowest100 * (1 - 0.05 * marketMult),
        type: 'success'
      },
      {
        name: '平衡型',
        desc: `标准网格，防击穿(￥${(lowest30 * (marketMult > 1 ? 0.95 : 1.0)).toFixed(2)})，网格间距覆盖绝大多数日内震荡噪声`,
        ratio: Math.max(0.5, Math.round(dailyVol * marketMult * 2) / 2),
        bottom: lowest30 * (marketMult > 1 ? 0.95 : 1),
        type: 'primary'
      },
      {
        name: '激进型',
        desc: `小网格获取高频交易，底部保护较浅，网格间距为日内极端波动的1/3，套取更细微的波段`,
        ratio: Math.max(0.4, Math.round((dailyVol / 2.5) * marketMult * 2) / 2),
        bottom: currentPx * (1 - 0.10 * marketMult),
        type: 'warning'
      }
    ];

    strategyOptions.value.forEach(s => {
      let r = s.ratio / 100;
      if (currentPx > s.bottom) {
         let n = Math.log(s.bottom / currentPx) / Math.log(1 - r);
         s.parts = Math.max(3, Math.ceil(n));
         if (s.parts > 100) s.parts = 100;
      } else {
         s.parts = 5;
      }
    });

    let defaultOpt = strategyOptions.value[1];
    editRatio.value = defaultOpt.ratio;
    editParts.value = defaultOpt.parts;
  } else {
    editRatio.value = 3.0;
    atrValue.value = 0;
    editParts.value = 5;
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

  // BOLL channels data
  const upData = []
  const mbData = []
  const dnData = []
  
  for (let i = 0; i < klineList.value.length; i++) {
    if (i < 19) {
      upData.push('-')
      mbData.push('-')
      dnData.push('-')
    } else {
      let sum = 0
      for (let j = i - 19; j <= i; j++) {
        sum += parseFloat(klineList.value[j].close)
      }
      const mb = sum / 20
      
      let sumSq = 0
      for (let j = i - 19; j <= i; j++) {
        const diff = parseFloat(klineList.value[j].close) - mb
        sumSq += diff * diff
      }
      const md = Math.sqrt(sumSq / 20)
      
      upData.push((mb + 2 * md).toFixed(3))
      mbData.push(mb.toFixed(3))
      dnData.push((mb - 2 * md).toFixed(3))
    }
  }

  const markLineData = []
  
  // First Sell line
  const r = editRatio.value / 100
  markLineData.push({
    yAxis: recommendBasePrice.value * (1 + r),
    name: '首档卖出价',
    label: { formatter: '首档卖出: {c}', position: 'end', color: '#E6A23C', fontSize: 10 },
    lineStyle: { color: '#E6A23C', type: 'solid', width: 2 }
  })

  // Base line
  markLineData.push({
    yAxis: recommendBasePrice.value,
    name: '当前基准价',
    label: { formatter: '推荐建仓: {c}', position: 'insideStartTop', color: '#f56c6c' },
    lineStyle: { color: '#f56c6c', type: 'solid', width: 2 }
  })
  
  // History Base line
  if (backtestResult.value?.basePrice && Math.abs(backtestResult.value.basePrice - recommendBasePrice.value) > 0.001) {
    markLineData.push({
      yAxis: backtestResult.value.basePrice,
      name: '回测基准价',
      label: { formatter: '回测基准: {c}', position: 'insideStartBottom', color: '#909399' },
      lineStyle: { color: '#909399', type: 'dashed', width: 1.5, opacity: 0.8 }
    })
  }

  // Grid lines
  let p = recommendBasePrice.value
  for (let i = 1; i <= editParts.value; i++) {
    p = p * (1 - r)
    markLineData.push({
      yAxis: p,
      name: `第${i}档网络`,
      label: { formatter: `第${i}档拦截 {c}`, position: 'end', color: '#409EFF', fontSize: 10 },
      lineStyle: { color: '#409EFF', type: 'dashed', width: 1, opacity: 0.6 }
    })
  }

  const markPointData = [
    { type: 'max', name: '当前显示最高价', valueDim: 'highest', itemStyle: { color: '#F56C6C' }, symbolSize: [70, 45] },
    { type: 'min', name: '当前显示最低价', valueDim: 'lowest', itemStyle: { color: '#14b143' }, symbolRotate: 180, label: { offset: [0, 10] }, symbolSize: [70, 45] }
  ]
  if (backtestResult.value?.trades) {
    for (let t of backtestResult.value.trades) {
        if (t.buyDate) {
          markPointData.push({
            name: '买入',
            coord: [t.buyDate, t.buyPrice],
            value: '买',
            itemStyle: { color: '#409EFF' }
          })
        }
        if (t.sellDate) {
          markPointData.push({
            name: '卖出',
            coord: [t.sellDate, t.sellPrice],
        })
      }
    }
  }

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['日K', 'UP', 'MB', 'DN'] },
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
        },
        markPoint: {
          data: markPointData,
          symbolSize: 40,
          label: {
            color: '#fff',
            fontSize: 10
          }
        }
      },
      {
        name: 'UP',
        type: 'line',
        data: upData,
        smooth: true,
        symbol: 'none',
        lineStyle: { opacity: 0.6, color: '#F56C6C' },
        itemStyle: { color: '#F56C6C' }
      },
      {
        name: 'MB',
        type: 'line',
        data: mbData,
        smooth: true,
        symbol: 'none',
        lineStyle: { opacity: 0.6, type: 'dashed', color: '#E6A23C' },
        itemStyle: { color: '#E6A23C' }
      },
      {
        name: 'DN',
        type: 'line',
        data: dnData,
        smooth: true,
        symbol: 'none',
        lineStyle: { opacity: 0.6, color: '#67C23A' },
        itemStyle: { color: '#67C23A' }
      }
    ]
  }

  chartInstance.setOption(option)
}

function createPlanFromAnalysis() {
  const query = {
    action: 'create',
    code: sinaCode.value,
    name: quoteData.value?.name || '',
    basePrice: recommendBasePrice.value,
    ratio: editRatio.value,
    parts: editParts.value
  }
  router.push({ path: '/plans', query })
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

.index-box {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 16px;
}
.index-name {
  font-size: 14px;
  color: #606266;
  font-weight: bold;
  margin-bottom: 8px;
}
.index-price {
  font-size: 24px;
  font-weight: bold;
}
.index-change {
  font-size: 14px;
  margin-top: 4px;
}
.market-advice {
  margin-top: 8px;
}

.watchlist-sticky-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  background-color: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  padding: 12px 20px;
  margin: -20px -20px 20px -20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
</style>