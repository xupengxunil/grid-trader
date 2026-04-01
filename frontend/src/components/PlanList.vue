<template>
  <div>
    <!-- Page header -->
    <div class="page-header">
      <h2>交易计划列表</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        新建计划
      </el-button>
    </div>

    <!-- Recommended Watchlist Cards -->
    <el-card class="recommend-card" shadow="hover" style="margin-bottom: 20px;">
      <template #header>
        <div style="font-weight: 600; display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-icon color="#e6a23c"><Star /></el-icon>
            <span>自选股智能发掘: 网格建仓形态</span>
            <el-tooltip content="点击按钮扫描您的自选股，发掘具备良好网格建仓形态的标的。" placement="right">
              <el-icon size="14" color="#909399"><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
          <el-button v-if="!hasScanned && !loadingWatchlist" type="primary" size="small" plain @click="fetchRecommendedWatchlist">扫描自选股</el-button>
          <el-button v-else-if="loadingWatchlist" type="primary" size="small" plain loading>扫描中...</el-button>
          <el-button v-else type="primary" size="small" plain @click="fetchRecommendedWatchlist">重新扫描</el-button>
        </div>
      </template>
      
      <div v-if="loadingWatchlist" v-loading="loadingWatchlist" element-loading-text="正在分析自选股形态..." style="height: 40px; border-radius: 4px;"></div>
      
      <div v-else-if="!hasScanned" style="color: #909399; font-size: 14px; text-align: center; padding: 10px 0;">
        点击右上角按钮开始分析自选股
      </div>

      <div v-else-if="hasScanned && recommendedWatchlist.length === 0" style="color: #909399; font-size: 14px; text-align: center; padding: 10px 0;">
        暂未发现具备典型网格建仓形态的自选股。
      </div>

      <div v-else class="recommend-tags">
        <el-tag
          v-for="item in recommendedWatchlist"
          :key="item.stock_code"
          type="success"
          effect="light"
          round
          style="margin-right: 12px; margin-bottom: 8px; cursor: pointer; padding: 4px 12px; height: auto;"
          @click="jumpToAnalysis(item.stock_code)"
        >
          <div style="display: flex; align-items: center; gap: 4px;">
            <span style="font-size: 14px; font-weight: 600;">{{ item.stock_name }}</span>
            <span style="font-size: 12px; color: #909399;">{{ item.stock_code }}</span>
            <el-icon style="margin-left: 4px;"><Promotion /></el-icon>
          </div>
        </el-tag>
      </div>
    </el-card>

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
        
        <!-- 智能策略推荐 -->
        <el-form-item v-if="strategyOptions.length > 0" label="智能推荐队">
          <div style="width: 100%">
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              <el-tooltip
                v-for="opt in strategyOptions"
                :key="opt.name"
                :content="opt.desc"
                placement="top"
              >
                <el-button :type="opt.type" plain size="small" @click="applyStrategy(opt)">
                  {{ opt.name }} ({{ opt.ratio }}% | {{ opt.parts }}档)
                </el-button>
              </el-tooltip>
            </div>
            <div style="font-size: 12px; color: #909399; margin-top: 4px; line-height: 1.2;">
              均线参考: MA5 <span :class="{'loss-text': maData.ma5<form.base_price}">￥{{ maData.ma5?.toFixed(2) }}</span> | 
              MA10 <span :class="{'loss-text': maData.ma10<form.base_price}">￥{{ maData.ma10?.toFixed(2) }}</span> | 
              MA30 <span :class="{'loss-text': maData.ma30<form.base_price}">￥{{ maData.ma30?.toFixed(2) }}</span>
              <span v-if="marketTrend" style="margin-left: 8px; padding-left: 8px; border-left: 1px solid #dcdfe6; color: #e6a23c;">
                {{ marketTrend }}
              </span>
            </div>
            <el-alert
              v-if="stockTrendAdvice"
              :title="stockTrendAdvice"
              :type="stockTrendType"
              :closable="false"
              style="margin-top: 8px; padding: 4px 8px;"
            />
          </div>
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
              如果需要覆盖下潜防守位(¥{{ lowestPx?.toFixed(2) }})防破网，建议档数为 {{ recommendedParts }} 档。
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
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Warning, Box, CopyDocument, Star, InfoFilled, Promotion } from '@element-plus/icons-vue'
import { getPlans, createPlan, deletePlan, updatePlan, getQuotes, getKLine, searchStocks, getWatchlist } from '../api/index.js'
import { analyzeStockSuitability } from '../utils/indicators.js'

const router = useRouter()
const route = useRoute()
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

const strategyOptions = ref([])
const maData = ref({})
const marketTrend = ref('')
const stockTrendAdvice = ref('')
const stockTrendType = ref('info')

function applyStrategy(opt) {
  ratioPercent.value = opt.ratio
  form.value.part_count = opt.parts
  recommendedRatio.value = opt.ratio
  recommendedParts.value = opt.parts
  ElMessage.success(`已应用 ${opt.name} 策略参数`)
}

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
    const { data } = await getQuotes(sinaCode); // 获取实时行情只是为了拿股票名字
    if (data && data[sinaCode]) {
      const quote = data[sinaCode];
      form.value.stock_name = quote.name;
    }
    
    // Fetch K-line to recommend grid size based on ATR
    recommendedRatio.value = null;
    recommendedParts.value = null;
    strategyOptions.value = [];
    maData.value = {};
    marketTrend.value = '';
    stockTrendAdvice.value = '';
    stockTrendType.value = 'info';
    
    // 并发获取股票数据和上证指数数据(sh000001)
    const [kDataRes, indexDataRes] = await Promise.all([
      getKLine(sinaCode, 240, 100).catch(() => ({ data: [] })),
      getKLine('sh000001', 240, 30).catch(() => ({ data: [] }))
    ]);
    
    const kData = kDataRes;
    
    // 评估大盘环境，用作策略的调整系数
    let marketMult = 1.0;
    if (indexDataRes.data && indexDataRes.data.length > 0) {
      const idxCloses = indexDataRes.data.map(d => parseFloat(d.close));
      const idxCurrent = idxCloses[idxCloses.length - 1];
      const idxMA20 = idxCloses.slice(-20).reduce((a, b) => a + b, 0) / Math.min(20, idxCloses.length);
      
      if (idxCurrent < idxMA20 * 0.98) {
        marketMult = 1.2; // 跌势，网格需变大，底部防守位下移
        marketTrend.value = `大盘弱势(上证跌破MA20)，推荐网格拉大防守`;
      } else if (idxCurrent > idxMA20 * 1.02) {
        marketMult = 0.8; // 涨势，网格可微缩，增加资金利用率
        marketTrend.value = `大盘强势(上证高于MA20)，推荐适当缩小网格`;
      } else {
        marketMult = 1.0;
        marketTrend.value = `大盘进入震荡期`;
      }
    }

    if (kData.data && kData.data.length > 0) {
      let trSum = 0;
      let validDays = 0;
      let lowest100 = Infinity;
      
      const atrRange = 14;
      const closePrices = kData.data.map(d => parseFloat(d.close));
      const lows = kData.data.map(d => parseFloat(d.low));
      
      lowest100 = Math.min(...lows);
      const lowest30 = Math.min(...lows.slice(Math.max(0, lows.length - 30)));
      
      // Calculate Moving Averages
      const ma5 = closePrices.slice(-5).reduce((a,b)=>a+b,0) / Math.min(5, closePrices.length);
      const ma10 = closePrices.slice(-10).reduce((a,b)=>a+b,0) / Math.min(10, closePrices.length);
      const ma30 = closePrices.slice(-30).reduce((a,b)=>a+b,0) / Math.min(30, closePrices.length);
      
      // 1. Calculate MA30 slope (Rate of change over the last 10 days)
      const pastClose30 = closePrices.slice(-40, -10); // 10天之前的30天数据
      const ma30_past = pastClose30.length > 0 ? (pastClose30.reduce((a,b)=>a+b,0) / Math.min(30, pastClose30.length)) : ma30;
      const ma30_slope = ma30_past > 0 ? ((ma30 - ma30_past) / ma30_past) * 100 : 0;
      
      // 2. Calculate MA dispersion (均线粘合度)
      const ma_max = Math.max(ma5, ma10, ma30);
      const ma_min = Math.min(ma5, ma10, ma30);
      const ma_dispersion = ma_min > 0 ? ((ma_max - ma_min) / ma_min) * 100 : 0;

      maData.value = { ma5, ma10, ma30 };
      
      // Stock Trend Advice Based on Advanced MAs & Slope
      if (ma_dispersion < 3.5 && Math.abs(ma30_slope) < 1.5) {
        stockTrendAdvice.value = '【极佳建仓点】均线高度粘合(<3.5%)且MA30走平，处于典型的箱体震荡期，完美适合网格交易！';
        stockTrendType.value = 'success';
      } else if (ma5 > ma10 && ma10 > ma30 && ma30_slope > 1.5) {
        stockTrendAdvice.value = '【风险提示】强多头趋势且均线斜率陡峭，网格极易被全部卖出从而踏空大行情，不建议做震荡网格！';
        stockTrendType.value = 'warning';
      } else if (ma5 < ma10 && ma10 < ma30 && ma30_slope < -1.5) {
        stockTrendAdvice.value = '【左侧抄底】处于明确的下降趋势中 (阴跌未企稳)。底部深不可测，极易买满被套，必须选[稳健型]将网格间距拉大，用更深的防守位承接！';
        stockTrendType.value = 'error';
      } else if (ma30 > ma5 && ma30 > ma10) {
        stockTrendAdvice.value = '趋势偏弱阶段，价格在 MA30 压制下，处于底部寻找支撑期，可尝试网格左侧定投建仓。';
        stockTrendType.value = 'info';
      } else {
        stockTrendAdvice.value = '行情处于宽幅震荡或趋势转换期，适合网格套利，建议参考下方提示设定安全边际。';
        stockTrendType.value = 'info';
      }
      
      const currentPx = closePrices[closePrices.length - 1];

      // 将基准价初始化为 MA30 (不直接使用当前价)
      // 保留两位小数
      if (currentPx > 0) {
        form.value.base_price = parseFloat(ma30.toFixed(3));
      }
      
      for (let i = 0; i < kData.data.length; i++) {
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
      
      lowestPx.value = lowest100;
            
      if (validDays > 0 && currentPx > 0) {
        const atr = trSum / validDays;
        atrVal.value = atr;
        
        // --- 基于最高/最低真实落差的网格大小计算法 ---
        // 获取近 30 天的最高点和最低点
        const highs30 = kData.data.slice(-30).map(d => parseFloat(d.high));
        const highest30 = Math.max(...highs30);
        
        // 计算近期真实的最大回撤幅度 (Max Drawdown Amplitude)
        const rangeAmplitude = ((highest30 - lowest30) / highest30) * 100;
        
        // 日均波动率 (每天正常波动的百分比)
        const dailyVol = (atr / currentPx) * 100;
        
        // Define Quant Strategies (非简单乘数，基于不同振幅因子)
        strategyOptions.value = [
          {
            name: '稳健型',
            desc: `大网格，深底 (覆盖100日最低点：￥${(lowest100 * (1 - 0.05 * marketMult)).toFixed(2)})，网格间距参考近期最大箱体振幅计算`,
            // 稳健型：用 30 天的大振幅切分成的网格。例如30天振幅是 15%，我们希望他在这个大箱体内只交易4-5次
            ratio: Math.max(1.0, Math.round((rangeAmplitude / 4) * marketMult * 2) / 2),
            bottom: lowest100 * (1 - 0.05 * marketMult), // 防击穿
            type: 'success'
          },
          {
            name: '平衡型',
            desc: `标准网格，防击穿(￥${(lowest30 * (marketMult > 1 ? 0.95 : 1.0)).toFixed(2)})，网格间距覆盖绝大多数日内震荡噪声`,
            // 平衡型：间距大小刚好约等于 1 个交易日的平均正常波动 (ATR)，滤除噪音
            ratio: Math.max(0.5, Math.round(dailyVol * marketMult * 2) / 2),
            bottom: lowest30 * (marketMult > 1 ? 0.95 : 1), // 如果大盘弱，平衡型也下潜防守
            type: 'primary'
          },
          {
            name: '激进型',
            desc: `小网格获取高频交易，底部保护较浅，网格间距为日内极端波动的1/3，套取更细微的波段`,
            // 激进型：通过吃日内的毛刺来获利，网格应当比日内正常波动更小 (如 ATR 的 1/3 ~ 1/2)
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
             if (s.parts > 100) s.parts = 100; // max reasonable limit
          } else {
             s.parts = 5;
          }
        });
        
        // 默认自动应用“平衡型”
        let defaultOpt = strategyOptions.value[1];
        recommendedRatio.value = defaultOpt.ratio;
        recommendedParts.value = defaultOpt.parts;
        ratioPercent.value = defaultOpt.ratio; 
        form.value.part_count = defaultOpt.parts; 
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

const recommendedWatchlist = ref([])
const loadingWatchlist = ref(false)
const hasScanned = ref(false)

async function fetchRecommendedWatchlist() {
  loadingWatchlist.value = true
  hasScanned.value = true
  try {
    const res = await getWatchlist()
    const watchlistStr = res.data || []
    const recommended = []
    
    // Process items sequentially to avoid slamming the API too hard
    for (const item of watchlistStr) {
      if (!item.stock_code) continue
      try {
        const klineRes = await getKLine(item.stock_code, 240, 100)
        if (klineRes.data && klineRes.data.length > 0) {
          const isSuitable = analyzeStockSuitability(klineRes.data)
          if (isSuitable) {
            recommended.push({
              stock_code: item.stock_code,
              stock_name: item.stock_name
            })
          }
        }
      } catch (e) {
        console.error(`Failed to analyze ${item.stock_code}`, e)
      }
    }
    recommendedWatchlist.value = recommended
    localStorage.setItem('grid_recommended_watchlist', JSON.stringify(recommended))
  } catch (e) {
    console.error('Failed to fetch watchlist', e)
  } finally {
    loadingWatchlist.value = false
  }
}

function jumpToAnalysis(code) {
  router.push(`/analysis?code=${code}`)
}

onMounted(() => {
  fetchPlans()

  // 尝试从本地缓存中加载已扫描的推荐自选股
  const cachedWatchlist = localStorage.getItem('grid_recommended_watchlist')
  if (cachedWatchlist) {
    try {
      recommendedWatchlist.value = JSON.parse(cachedWatchlist)
      hasScanned.value = true
    } catch (e) {
      console.error('Failed to parse cached watchlist', e)
    }
  }

  if (route.query.action === 'create') {
    showCreateDialog.value = true
    setTimeout(() => {
      form.value.stock_code = route.query.code || ''
      form.value.stock_name = route.query.name || ''
      if (route.query.basePrice) form.value.base_price = parseFloat(route.query.basePrice)
      if (route.query.ratio) ratioPercent.value = parseFloat(route.query.ratio)
      if (route.query.parts) form.value.part_count = parseInt(route.query.parts)
    }, 100)
    router.replace('/plans')
  }
})
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
