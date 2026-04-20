<template>
  <div class="watchlist-opportunities">
    <!-- 共振扫描表格 -->
    <el-card class="opportunities-table" shadow="hover" style="margin-bottom: 20px;">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
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
        <el-button type="primary" size="small" @click="scanWatchlist">
          <el-icon><Refresh /></el-icon> 重新扫描
        </el-button>
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
  </div>
</template>

<script>
import { QuestionFilled, Refresh, DataBoard } from '@element-plus/icons-vue';
import { analyzeSignals } from '../utils/indicators.js';
import { getWatchlist, getKLine } from '../api/index.js';

export default {
  name: 'WatchlistOpportunities',
  emits: ['diagnose'],
  components: {
    QuestionFilled,
    Refresh,
    DataBoard
  },
  data() {
    return {
      loading: false,
      opportunitiesList: []
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
    viewDetails(row) {
      this.$emit('diagnose', row.stock_code);
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
