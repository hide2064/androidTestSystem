<template>
  <div class="dashboard">
    <!-- スライサーパネル -->
    <SlicerPanel />

    <!-- ローディング / エラー -->
    <div v-if="loading" class="overlay-loading">
      <el-icon class="is-loading" :size="48"><Loading /></el-icon>
    </div>
    <el-alert v-if="error" :title="error" type="error" :closable="false" style="margin: 8px 16px" />

    <div class="dashboard-body">
      <!-- KPIカード -->
      <KpiCards :summary="summary" />

      <!-- チャートグリッド -->
      <div class="chart-grid">

        <!-- 合否率（横幅広め） -->
        <div class="chart-col span-2">
          <YieldChart
            :items="yieldData"
            :model-group-by="yieldGroupBy"
            @change-group="onYieldGroupChange"
          />
        </div>

        <!-- 時系列 -->
        <div class="chart-col">
          <TrendChart
            :data="trendData"
            :active-freq="trendFreq"
            :active-metric="trendMetric"
            @change-freq="onTrendFreqChange"
            @change-metric="onTrendMetricChange"
          />
        </div>

        <!-- 測定値分布（横幅全体） -->
        <div class="chart-col span-3">
          <DistributionChart
            :test-items="availableFilters.Test_Item"
            :active-test-item="activeTestItem"
            :active-group-by="distGroupBy"
            :stats="distStats"
            :raw="distRaw"
            @change-test-item="onDistTestItemChange"
            @change-group="onDistGroupChange"
          />
        </div>

        <!-- マージン分析 -->
        <div class="chart-col span-2">
          <MarginChart
            :points="marginData"
            :active-x-axis="marginXAxis"
            @change-x="onMarginXChange"
          />
        </div>

        <!-- FAILリスト -->
        <div class="chart-col">
          <div class="chart-card">
            <div class="chart-title">FAIL一覧</div>
            <el-table :data="failList" border stripe size="small" max-height="280">
              <el-table-column prop="label"      label="グループ"   min-width="120" />
              <el-table-column prop="fail_count" label="FAIL数"     width="80" />
              <el-table-column prop="total"      label="総数"       width="80" />
              <el-table-column prop="yield_pct"  label="歩留り(%)"  width="100">
                <template #default="{ row }">
                  <el-tag :type="row.yield_pct < 95 ? 'danger' : 'success'" size="small">
                    {{ row.yield_pct.toFixed(1) }}%
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { Loading } from '@element-plus/icons-vue'
import { useRfStore } from '@/stores/rfStore'
import SlicerPanel      from '@/components/filters/SlicerPanel.vue'
import KpiCards         from '@/components/rf/KpiCards.vue'
import YieldChart       from '@/components/rf/YieldChart.vue'
import TrendChart       from '@/components/rf/TrendChart.vue'
import DistributionChart from '@/components/rf/DistributionChart.vue'
import MarginChart      from '@/components/rf/MarginChart.vue'

const rfStore = useRfStore()
const {
  availableFilters, activeTestItem,
  summary, yieldData, distStats, distRaw, trendData, marginData,
  yieldGroupBy, distGroupBy, trendFreq, trendMetric, marginXAxis,
  loading, error,
} = storeToRefs(rfStore)

const failList = computed(() =>
  [...rfStore.yieldData].filter(i => i.fail_count > 0).sort((a, b) => b.fail_count - a.fail_count)
)

onMounted(async () => {
  await rfStore.loadFilters()
  await rfStore.refresh()
})

function onYieldGroupChange(val: string) {
  rfStore.yieldGroupBy = val
  rfStore.refresh()
}
function onTrendFreqChange(val: string) {
  rfStore.trendFreq = val
  rfStore.refresh()
}
function onTrendMetricChange(val: string) {
  rfStore.trendMetric = val
  rfStore.refresh()
}
function onDistTestItemChange(val: string) {
  rfStore.distTestItem = val
  rfStore.refresh()
}
function onDistGroupChange(val: string) {
  rfStore.distGroupBy = val
  rfStore.refresh()
}
function onMarginXChange(val: string) {
  rfStore.marginXAxis = val
  rfStore.refresh()
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.overlay-loading {
  position: fixed;
  inset: 0;
  background: rgba(255,255,255,.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}
.dashboard-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  background: #f0f2f5;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chart-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.chart-col { min-width: 0; }
.chart-col.span-2 { grid-column: span 2; }
.chart-col.span-3 { grid-column: span 3; }

.chart-card { background: #fff; border-radius: 8px; padding: 12px; }
.chart-title { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 8px; }

@media (max-width: 1100px) {
  .chart-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-col.span-2 { grid-column: span 2; }
  .chart-col.span-3 { grid-column: span 2; }
}
@media (max-width: 700px) {
  .chart-grid { grid-template-columns: 1fr; }
  .chart-col.span-2, .chart-col.span-3 { grid-column: span 1; }
}
</style>
