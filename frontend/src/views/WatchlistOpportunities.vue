<template>
  <div class="watchlist-opportunities">
    <el-tabs v-model="activeTab" @tab-click="handleTabClick" style="margin-bottom: 20px;">
      <el-tab-pane label="短线共振查杀" name="shortTerm"></el-tab-pane>
      <el-tab-pane label="长线投资诊断 (200MA)" name="longTerm"></el-tab-pane>
    </el-tabs>

    <!-- 共振扫描表格 -->
    <el-card v-show="activeTab === 'shortTerm'" class="opportunities-table" shadow="hover" style="margin-bottom: 20px;">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <span style="display: flex; align-items: center; font-weight: bold; font-size: 16px;">
          <el-icon style="margin-right: 4px; vertical-align: -2px;"><DataBoard /></el-icon>
          自选股指标共振检测列表
          <el-tooltip effect="dark" placement="right">
            <template #content>
              <div style="line-height: 1.8;">
                <b>技术面共振说明：</b><br>
                1. <b>MACD</b>：判断中线多空趋势，金叉(绿)/死叉(红)为趋势反转信号。<br>
                2. <b>KDJ</b>：判断短线超买超卖，&lt;20(绿)为超卖随时反弹，&gt;80(红)为超买风险。<br>
                3. <b>BOLL</b>：判断震荡通道，触及下轨(绿)有强支撑，触及上轨(红)有阻力。<br>
                <i>注：绿底标签代表看多(建议底仓)，红底标签代表看空(建议减仓)。星星越多共振越强。</i>
              </div>
            </template>
            <el-icon style="margin-left: 5px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
          </el-tooltip>
        </span>
        <div style="display: flex; align-items: center; gap: 10px;">
          <el-autocomplete 
            v-model="stockCodeInput"
            :fetch-suggestions="querySearchAsync"
            placeholder="搜索股票并加入自选" 
            style="width: 250px"
            @select="handleSelect"
            value-key="code"
            clearable
            size="small"
          >
            <template #default="{ item }">
              <div style="display: flex; justify-content: space-between;">
                <span>{{ item.name }}</span>
                <span style="color: #999; font-size: 12px;">{{ item.code }}</span>
              </div>
            </template>
          </el-autocomplete>
          <el-button type="success" size="small" @click="addSelectedToWatchlist" :disabled="!selectedStock" :loading="addingWatchlist">
            <el-icon><Plus /></el-icon> 加入自选
          </el-button>
          <el-button type="primary" size="small" @click="scanWatchlist">
            <el-icon><Refresh /></el-icon> 重新扫描
          </el-button>
        </div>
      </div>
      
      <!-- 搜索出的股票基本信息 -->
      <div v-if="selectedQuote" style="margin-bottom: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 4px; display: flex; align-items: center; gap: 20px;">
        <span style="font-weight: bold; font-size: 16px;">{{ selectedStock.name }} ({{ selectedStock.sina_code }})</span>
        <span>
          最新: 
          <span :class="selectedQuote.price >= selectedQuote.pre_close ? 'up' : 'down'" style="font-weight: bold;">
            {{ selectedQuote.price.toFixed(2) }}
          </span>
        </span>
        <span :class="selectedQuote.price >= selectedQuote.pre_close ? 'up' : 'down'">
          涨跌: {{ (selectedQuote.price - selectedQuote.pre_close).toFixed(2) }} 
          ({{ (((selectedQuote.price - selectedQuote.pre_close) / selectedQuote.pre_close) * 100).toFixed(2) }}%)
        </span>
        <span>今开: {{ selectedQuote.open.toFixed(2) }}</span>
        <span>最高: {{ selectedQuote.high.toFixed(2) }}</span>
        <span>最低: {{ selectedQuote.low.toFixed(2) }}</span>
        <span>成交量: {{ (selectedQuote.volume / 10000).toFixed(2) }} 万手</span>
      </div>

      <el-table
        v-loading="loading"
        :data="opportunitiesList"
        style="width: 100%"
        :default-sort="{prop: 'score', order: 'descending'}"
      >
        <el-table-column prop="stock_code" label="代码" width="100"></el-table-column>
        <el-table-column prop="stock_name" label="名称" width="120"></el-table-column>
        <el-table-column prop="current_price" label="最新价" width="100">
          <template #default="scope">
            <span :class="scope.row.change_percent >= 0 ? 'up' : 'down'">
              {{ scope.row.current_price }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="change_percent" label="涨跌幅" width="100">
          <template #default="scope">
            <span :class="scope.row.change_percent >= 0 ? 'up' : 'down'">
              {{ scope.row.change_percent }}%
            </span>
          </template>
        </el-table-column>

        <!-- 信号标签 -->
        <el-table-column label="技术面共振信号" min-width="250">
          <template #default="scope">
            <el-tag 
              v-for="(tag, index) in scope.row.signals.tags" 
              :key="index" 
              :type="tag.type"
              size="small"
              style="margin-right: 5px; margin-bottom: 5px;"
            >
              {{ tag.text }}
            </el-tag>
            <span v-if="!scope.row.signals.tags || scope.row.signals.tags.length === 0" style="color: #999; font-size: 12px;">无特征信号</span>
          </template>
        </el-table-column>

        <!-- 分数/推荐等级 -->
        <el-table-column prop="score" label="共振强度" width="150" sortable>
          <template #default="scope">
            <el-rate
              v-model="scope.row.stars"
              disabled
              show-score
              text-color="#ff9900"
              score-template="{value}">
            </el-rate>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="viewDetails(scope.row)">行情诊断</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-show="activeTab === 'longTerm'" class="opportunities-table" shadow="hover" style="margin-bottom: 20px;">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <span style="display: flex; align-items: center; font-weight: bold; font-size: 16px;">
          <el-icon style="margin-right: 4px; vertical-align: -2px;"><DataBoard /></el-icon>
          自选股长线诊断列表 (200日均线)
          <el-tooltip effect="dark" placement="right">
            <template #content>
              <div style="line-height: 1.8;">
                <b>长线技术面说明：</b><br>
                1. <b>200日均线 (MA200)</b>：重要牛熊分界线。<br>
                2. <b>趋势判定</b>：股价是否长期处于上升趋势。<br>
                3. <b>操作建议</b>：靠近200日均线时（偏离度在0~5%），绿底标签看多；大幅偏离则红色标签提示风险。
              </div>
            </template>
            <el-icon style="margin-left: 5px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
          </el-tooltip>
        </span>
        <div style="display: flex; align-items: center; gap: 10px;">
          <el-button type="primary" size="small" @click="scanLongTerm">
            <el-icon><Refresh /></el-icon> 重新扫描
          </el-button>
        </div>
      </div>
      
      <el-table
        v-loading="loadingLongTerm"
        :data="longTermList"
        style="width: 100%"
        :default-sort="{prop: 'score', order: 'descending'}"
      >
        <el-table-column prop="stock_code" label="代码" width="100"></el-table-column>
        <el-table-column prop="stock_name" label="名称" width="120"></el-table-column>
        <el-table-column prop="current_price" label="最新价" width="90">
          <template #default="scope">
            <span :class="scope.row.change_percent >= 0 ? 'up' : 'down'">
              {{ scope.row.current_price }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="ma200" label="200日均线" width="100">
          <template #default="scope">
            <span>{{ scope.row.ma200 }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="bias" label="均线乖离率" width="110">
          <template #default="scope">
            <span :class="scope.row.bias >= 0 ? 'up' : 'down'">
              {{ scope.row.bias }}%
            </span>
          </template>
        </el-table-column>

        <!-- 信号标签 -->
        <el-table-column label="长线诊断指标与信号" min-width="250">
          <template #default="scope">
            <el-tag 
              v-for="(tag, index) in scope.row.signals.tags" 
              :key="index" 
              :type="tag.type"
              size="small"
              style="margin-right: 5px; margin-bottom: 5px;"
            >
              {{ tag.text }}
            </el-tag>
            <span v-if="!scope.row.signals.tags || scope.row.signals.tags.length === 0" style="color: #999; font-size: 12px;">无特征信号</span>
          </template>
        </el-table-column>

        <!-- 分数/推荐等级 -->
        <el-table-column prop="score" label="配置价值" width="120" sortable>
          <template #default="scope">
            <el-rate
              v-model="scope.row.stars"
              disabled
              show-score
              text-color="#ff9900"
              score-template="{value}">
            </el-rate>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button size="small" @click="viewLongTermDetails(scope.row)">长线分析</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { QuestionFilled, Refresh, DataBoard, Plus } from '@element-plus/icons-vue';
import { analyzeSignals, analyzeLongTermSignals } from '../utils/indicators.js';
import { getWatchlist, getKLine, searchStocks, addWatchlist, getQuotes } from '../api/index.js';

export default {
  name: 'WatchlistOpportunities',
  components: {
    QuestionFilled,
    Refresh,
    DataBoard,
    Plus
  },
  data() {
    return {
      activeTab: 'shortTerm',
      loading: false,
      loadingLongTerm: false,
      addingWatchlist: false,
      opportunitiesList: [],
      longTermList: [],
      stockCodeInput: '',
      selectedStock: null,
      selectedQuote: null,
      searchTimeout: null
    }
  },
  methods: {
    async scanWatchlist() {
      this.loading = true;
      try {
        const { data: watchlist } = await getWatchlist();
        const list = [];
        
        for (let idx = 0; idx < watchlist.length; idx++) {
          const stock = watchlist[idx];
          try {
            // Get daily kline, assuming scale=101 means daily or relying on default scale 60
            const { data: kData } = await getKLine(stock.stock_code, 101, 100);
            
            // Analyze the signals
            const signals = analyzeSignals(kData);
            
            // Add basic formatting mapping fields for display
            // Some recent close price vs previous close price
            const current_price = kData.length > 0 ? parseFloat(kData[kData.length - 1].close).toFixed(2) : '-';
            let change_percent = 0;
            if (kData.length >= 2) {
              const prev_close = parseFloat(kData[kData.length - 2].close);
              const curr_close = parseFloat(kData[kData.length - 1].close);
              change_percent = (((curr_close - prev_close) / prev_close) * 100).toFixed(2);
            }
            
            list.push({
              stock_code: stock.stock_code,
              stock_name: stock.stock_name,
              current_price: current_price,
              change_percent: change_percent,
              signals: signals,
              stars: this.calculateStars(signals.score),
              score: signals.score
            });
          } catch(err) {
            console.error('Failed to analyze', stock.stock_code, err);
          }
        }
        
        this.opportunitiesList = list;
        // 缓存扫描结果到本地，避免每次进入页面都重新加载
        localStorage.setItem('watchlistOppsCache', JSON.stringify({
          timestamp: new Date().getTime(),
          data: list
        }));
        this.$message.success('共振扫描完成');
      } catch (e) {
        this.$message.error('扫描失败');
        console.error(e);
      } finally {
        this.loading = false;
      }
    },
    calculateStars(score) {
      if (score >= 4) return 5;
      if (score === 3) return 4;
      if (score > 0) return 3;
      if (score === 0) return 0;
      return 0;
    },
    calculateLongTermStars(score) {
      if (score >= 4) return 5;
      if (score === 3) return 4;
      if (score > 0) return 3;
      if (score === 0) return 2;
      return 1;
    },
    async scanLongTerm() {
      this.loadingLongTerm = true;
      try {
        const { data: watchlist } = await getWatchlist();
        const list = [];
        
        for (let idx = 0; idx < watchlist.length; idx++) {
          const stock = watchlist[idx];
          try {
            // Get 260 daily kline
            const { data: kData } = await getKLine(stock.stock_code, 101, 260);
            
            const current_price = kData.length > 0 ? parseFloat(kData[kData.length - 1].close).toFixed(2) : '-';
            let change_percent = 0;
            if (kData.length >= 2) {
              const prev_close = parseFloat(kData[kData.length - 2].close);
              const curr_close = parseFloat(kData[kData.length - 1].close);
              change_percent = (((curr_close - prev_close) / prev_close) * 100).toFixed(2);
            }
            
            const analysis = analyzeLongTermSignals(kData);
            
            list.push({
              stock_code: stock.stock_code,
              stock_name: stock.stock_name,
              current_price: current_price,
              change_percent: change_percent,
              ma200: analysis.ma200,
              bias: analysis.bias === '-' ? '-' : Number(analysis.bias),
              signals: analysis.signals,
              stars: this.calculateLongTermStars(analysis.signals.score),
              score: analysis.signals.score
            });
          } catch(err) {
            console.error('Failed to analyze', stock.stock_code, err);
          }
        }
        
        this.longTermList = list;
        localStorage.setItem('longTermAnalysisCache', JSON.stringify({
          timestamp: new Date().getTime(),
          data: list
        }));
        this.$message.success('长线分析扫描完成');
      } catch (e) {
        this.$message.error('长线扫描失败');
        console.error(e);
      } finally {
        this.loadingLongTerm = false;
      }
    },
    viewDetails(row) {
      this.$router.push('/analysis?code=' + row.stock_code);
    },
    viewLongTermDetails(row) {
      this.$router.push('/long-analysis?code=' + row.stock_code);
    },
    handleTabClick(tab) {
      if (tab.paneName === 'longTerm' && this.longTermList.length === 0) {
        this.loadLongTermCache();
      }
    },
    loadLongTermCache() {
      const cachedStr = localStorage.getItem('longTermAnalysisCache');
      if (cachedStr) {
        try {
          const cache = JSON.parse(cachedStr);
          this.longTermList = cache.data;
          const timeDiff = Math.floor((new Date().getTime() - cache.timestamp) / 1000 / 60);
          this.$message.success(`已加载长线本地缓存数据（${timeDiff} 分钟前刷新）`);
        } catch (e) {
          console.error("Failed to parse cache", e);
        }
      } else {
        this.scanLongTerm();
      }
    },
    loadFromCache() {
      const cachedStr = localStorage.getItem('watchlistOppsCache');
      if (cachedStr) {
        try {
          const cache = JSON.parse(cachedStr);
          this.opportunitiesList = cache.data;
          
          const timeDiff = Math.floor((new Date().getTime() - cache.timestamp) / 1000 / 60);
          this.$message.success(`已加载本地缓存数据（${timeDiff} 分钟前刷新）`);
        } catch (e) {
          console.error("Failed to parse cache", e);
        }
      }
    },
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
    async handleSelect(item) {
      this.selectedStock = item;
      this.stockCodeInput = item.value;
      this.selectedQuote = null;
      try {
        let sinaCode = item.sina_code;
        if (!sinaCode || !sinaCode.match(/^(sh|sz|bj|hk)/)) {
          let c = item.code;
          if (c.startsWith('sh') || c.startsWith('sz') || c.startsWith('bj') || c.startsWith('hk')) sinaCode = c;
          else if (/^\d{5}$/.test(c)) sinaCode = 'hk' + c;
          else if (/^6/.test(c)) sinaCode = 'sh' + c;
          else if (/^0|^3/.test(c)) sinaCode = 'sz' + c;
          else if (/^8|^4/.test(c)) sinaCode = 'bj' + c;
          else sinaCode = c;
        }
        item.sina_code = sinaCode;
        const { data } = await getQuotes(sinaCode);
        if (data && data[sinaCode]) {
          this.selectedQuote = data[sinaCode];
        }
      } catch (e) {
        console.error('Failed to fetch quote', e);
      }
    },
    async addSelectedToWatchlist() {
      if (!this.selectedStock) return;
      this.addingWatchlist = true;
      try {
        let sinaCode = this.selectedStock.sina_code;
        if (!sinaCode || !sinaCode.match(/^(sh|sz|bj|hk)/)) {
          let c = this.selectedStock.code;
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
        
        await addWatchlist({
          stock_code: sinaCode,
          stock_name: this.selectedStock.name
        });
        
        this.$message.success('加入自选成功');
        this.selectedStock = null;
        this.selectedQuote = null;
        this.stockCodeInput = '';
        
        // 重新扫描以展现最新自选股
        this.scanWatchlist();
      } catch (e) {
        console.error('Failed to add watchlist', e);
        if (e.response && e.response.status === 400) {
          this.$message.warning('该股票已在自选列表中');
        } else {
          this.$message.error('加入自选失败');
        }
      } finally {
        this.addingWatchlist = false;
      }
    }
  },
  mounted() {
    this.loadFromCache();
  }
}
</script>

<style scoped>
.watchlist-opportunities {
  padding: 20px;
}
.dashboard-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 4px;
}
.dashboard-item .label {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}
.dashboard-item .value {
  font-size: 20px;
  font-weight: bold;
}
.up {
  color: #67c23a; /* 绿色代表利好(上涨) */
}
.down {
  color: #f56c6c; /* 红色代表风险(下跌) */
}
</style>
