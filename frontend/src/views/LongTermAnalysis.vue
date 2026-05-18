<template>
  <div class="long-term-analysis">
    <el-card shadow="hover" style="margin-bottom: 20px;">
      <template #header>
        <div style="font-weight: bold; font-size: 16px; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <el-icon style="margin-right: 4px; vertical-align: -2px;"><DataAnalysis /></el-icon>
            个股长线深度诊断
          </div>
        </div>
      </template>
      
      <!-- 搜索栏 -->
      <div style="margin-bottom: 20px;">
        <el-autocomplete 
          v-model="stockCodeInput"
          :fetch-suggestions="querySearchAsync"
          placeholder="输入代码、拼音或名称搜索股票" 
          style="width: 300px"
          @select="handleSelect"
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
            <el-button type="primary" :loading="loading" @click="analyzeStock">
              长线分析
            </el-button>
          </template>
        </el-autocomplete>
      </div>

      <div v-if="stockCode" class="analysis-content">
        <div style="margin-bottom: 16px;">
          <h3>当前分析标的: {{ selectedStockName ? `${selectedStockName} (${stockCode})` : stockCode }}</h3>
        </div>
        
        <el-row :gutter="20">
          <!-- 200日均线状态 -->
          <el-col :span="8">
            <el-card shadow="never" v-loading="loading">
              <template #header>200日均线状态 (近一年)</template>
              <div class="card-content" v-if="analysisResult">
                <p>200日均线: <b>{{ analysisResult.ma200 }}</b></p>
                <p>均线乖离率: <b>{{ analysisResult.bias }}%</b></p>
                <div style="margin-top: 10px;">
                  <el-tag 
                    v-for="(tag, index) in analysisResult.signals.tags" 
                    :key="index" 
                    :type="tag.type"
                    size="small"
                    style="margin-right: 5px; margin-bottom: 5px;"
                  >
                    {{ tag.text }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 长期估值区间 (PE/PB) -->
          <el-col :span="16">
            <el-card shadow="never" v-loading="loadingValuation">
              <template #header>长期估值区间 (PE/PB 最近250个交易日)</template>
              <div class="card-content" v-if="valuationData">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <div style="margin-bottom: 10px; font-weight: bold; color: #409EFF">市盈率 (PE - 动态)</div>
                    <p>当前 PE: <b>{{ valuationData.currentPE.toFixed(2) }}</b></p>
                    <p>近一年最低: <b>{{ valuationData.minPE.toFixed(2) }}</b> | 最高: <b>{{ valuationData.maxPE.toFixed(2) }}</b></p>
                    <p style="margin-top: 10px;">近一年 PE 分位点: 
                      <el-tag :type="valuationData.pePercentile < 30 ? 'success' : (valuationData.pePercentile > 70 ? 'danger' : 'warning')" size="small">
                        {{ valuationData.pePercentile.toFixed(2) }}%
                      </el-tag>
                    </p>
                    <div style="font-size: 13px; color: #909399; margin-top: 8px; line-height: 1.5;">
                      <el-icon style="vertical-align: -2px;"><InfoFilled /></el-icon>
                      {{ valuationData.pePercentile < 30 ? '估值处于低位，存在潜伏价值，安全边际极高' : (valuationData.pePercentile > 70 ? '估值偏高，注意股价已经透支部分未来业绩' : '估值合理，回归中性区间，处于正常修复阶段') }}
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="margin-bottom: 10px; font-weight: bold; color: #67C23A">市净率 (PB)</div>
                    <p>当前 PB: <b>{{ valuationData.currentPB.toFixed(2) }}</b></p>
                    <p>近一年最低: <b>{{ valuationData.minPB.toFixed(2) }}</b> | 最高: <b>{{ valuationData.maxPB.toFixed(2) }}</b></p>
                    <p style="margin-top: 10px;">近一年 PB 分位点: 
                      <el-tag :type="valuationData.pbPercentile < 30 ? 'success' : (valuationData.pbPercentile > 70 ? 'danger' : 'warning')" size="small">
                        {{ valuationData.pbPercentile.toFixed(2) }}%
                      </el-tag>
                    </p>
                    <div style="font-size: 13px; color: #909399; margin-top: 8px; line-height: 1.5;">
                      <el-icon style="vertical-align: -2px;"><InfoFilled /></el-icon>
                      {{ valuationData.pbPercentile < 30 ? '破净或严重低估区域，具备强支撑抗跌属性' : (valuationData.pbPercentile > 70 ? '市净率溢价较高，对持续高净资产收益率有严苛要求' : '正常波动范围内的常态估值') }}
                    </div>
                  </el-col>
                </el-row>
              </div>
              <div v-else-if="!loadingValuation">
                未能获取到足够估值数据。可能是指数或部分标的暂不支持日级估值分位。
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      <div v-else style="color: #909399; padding: 20px 0;">
        <el-icon style="margin-right: 4px; vertical-align: -2px;"><Pointer /></el-icon> 请在上方搜索框输入股票代码，或从自选股列表点击长线诊断进入。
      </div>
    </el-card>
  </div>
</template>

<script>
import { DataAnalysis, Pointer, InfoFilled } from '@element-plus/icons-vue';
import { getKLine, getDailyBasic, searchStocks } from '../api/index.js';
import { analyzeLongTermSignals } from '../utils/indicators.js';

export default {
  name: 'LongTermAnalysisDetail',
  components: {
    DataAnalysis,
    Pointer,
    InfoFilled
  },
  data() {
    return {
      stockCodeInput: '',
      stockCode: this.$route.query.code || '',
      selectedStockName: '',
      searchTimeout: null,
      loading: false,
      loadingValuation: false,
      analysisResult: null,
      valuationData: null
    }
  },
  watch: {
    '$route.query.code'(newCode) {
      if (newCode && newCode !== this.stockCode) {
        this.stockCode = newCode;
        this.stockCodeInput = newCode;
        this.selectedStockName = ''; // clear out to fetch it again
        this.analyzeStock();
      }
    }
  },
  methods: {
    async querySearchAsync(queryString, cb) {
      if (!queryString) {
        cb([]);
        return;
      }
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }
      this.searchTimeout = setTimeout(async () => {
        try {
          const { data } = await searchStocks(queryString);
          const results = data.map(item => ({
            value: `${item.name} (${item.code})`,
            name: item.name,
            code: item.code,
            sina_code: item.sina_code || item.code
          }));
          cb(results);
        } catch (e) {
          console.error('Search error', e);
          cb([]);
        }
      }, 300);
    },
    handleSelect(item) {
      let sinaCode = item.sina_code;
      if (!sinaCode || !sinaCode.match(/^(sh|sz|bj|hk)/)) {
        let c = item.code;
        if (c.startsWith('sh') || c.startsWith('sz') || c.startsWith('bj') || c.startsWith('hk')) {
          sinaCode = c;
        } else if (/^\d{5}$/.test(c)) {
          sinaCode = 'hk' + c;
        } else if (/^6/.test(c)) {
          sinaCode = 'sh' + c;
        } else if (/^0|^3/.test(c)) {
          sinaCode = 'sz' + c;
        } else if (/^8|^4/.test(c)) {
          sinaCode = 'bj' + c;
        } else {
          sinaCode = c;
        }
      }
      this.stockCode = sinaCode;
      this.selectedStockName = item.name;
      this.stockCodeInput = item.value;
      
      // Update url parameter
      this.$router.replace({ path: '/long-analysis', query: { code: this.stockCode }});
      this.analyzeStock();
    },
    async analyzeStock() {
      if (!this.stockCode) return;
      this.loading = true;
      this.loadingValuation = true;

      // Ensure we have the stock name if loaded from URL parameter
      if (!this.selectedStockName) {
        try {
          // Extract purely the numeric code part for better search matching
          const numericCode = this.stockCode.replace(/^[a-zA-Z]+/, '');
          const { data } = await searchStocks(numericCode || this.stockCode);
          if (data && data.length > 0) {
            const match = data.find(item => 
              (item.sina_code || '').toLowerCase() === this.stockCode.toLowerCase() || 
              item.code.includes(numericCode)
            );
            if (match) {
              this.selectedStockName = match.name;
            } else {
              this.selectedStockName = data[0].name;
            }
          }
        } catch (e) {
          console.error('Failed to fetch stock name', e);
        }
      }
      
      try {
        const { data: kData } = await getKLine(this.stockCode, 101, 260);
        this.analysisResult = analyzeLongTermSignals(kData);
      } catch (err) {
        console.error('Failed to get long term data', err);
        this.$message.error('获取长线K线数据失败');
      } finally {
        this.loading = false;
      }

      try {
        const { data: basicData } = await getDailyBasic(this.stockCode, 250);
        if (basicData && basicData.length > 0) {
          // pe_ttm -> dynamic PE
          const peList = basicData.map(d => d.pe_ttm || d.pe).filter(v => v !== null && v !== undefined && !isNaN(v));
          const pbList = basicData.map(d => d.pb).filter(v => v !== null && v !== undefined && !isNaN(v));
          
          if (peList.length > 0 && pbList.length > 0) {
            const currentPE = peList[peList.length - 1];
            const currentPB = pbList[pbList.length - 1];
            
            const minPE = Math.min(...peList);
            const maxPE = Math.max(...peList);
            const minPB = Math.min(...pbList);
            const maxPB = Math.max(...pbList);
            
            const pePercentile = maxPE === minPE ? 50 : ((currentPE - minPE) / (maxPE - minPE)) * 100;
            const pbPercentile = maxPB === minPB ? 50 : ((currentPB - minPB) / (maxPB - minPB)) * 100;
            
            this.valuationData = {
              currentPE, minPE, maxPE, pePercentile,
              currentPB, minPB, maxPB, pbPercentile
            };
          } else {
            this.valuationData = null;
          }
        } else {
          this.valuationData = null;
        }
      } catch (err) {
        console.error('Failed to get valuation data', err);
        this.$message.error('获取长期估值(PE/PB)失败');
      } finally {
        this.loadingValuation = false;
      }
    }
  },
  mounted() {
    if (this.stockCode) {
      this.stockCodeInput = this.stockCode;
      this.analyzeStock();
    }
  }
}
</script>

<style scoped>
.long-term-analysis {
  padding: 20px;
}
.card-content {
  min-height: 120px;
}
p {
  margin: 5px 0;
  color: #606266;
  font-size: 14px;
}
</style>