<template>
  <div class="android-dashboard">
    <!-- フィルタパネル -->
    <div class="filter-panel">
      <el-card>
        <template #header><span class="card-title">フィルタ</span></template>

        <div class="filter-group">
          <div class="filter-label">シナリオ</div>
          <el-checkbox-group v-model="store.selected.scenarios" @change="store.refresh()">
            <el-checkbox v-for="v in store.availableFilters.scenarios" :key="v" :value="v">{{ v }}</el-checkbox>
          </el-checkbox-group>
        </div>

        <div class="filter-group">
          <div class="filter-label">デバイスID</div>
          <el-checkbox-group v-model="store.selected.device_ids" @change="store.refresh()">
            <el-checkbox v-for="v in store.availableFilters.device_ids" :key="v" :value="v">{{ v }}</el-checkbox>
          </el-checkbox-group>
        </div>

        <div class="filter-group">
          <div class="filter-label">結果</div>
          <el-checkbox-group v-model="store.selected.results" @change="store.refresh()">
            <el-checkbox v-for="v in store.availableFilters.results" :key="v" :value="v">{{ v }}</el-checkbox>
          </el-checkbox-group>
        </div>

        <el-button size="small" @click="clearFilters" style="margin-top:8px; width:100%">フィルタクリア</el-button>
      </el-card>
    </div>

    <!-- メインコンテンツ -->
    <div class="main-content">
      <!-- KPIカード -->
      <div class="kpi-row" v-if="store.summary">
        <div class="kpi-card">
          <div class="kpi-value">{{ store.summary.total }}</div>
          <div class="kpi-label">総試験数</div>
        </div>
        <div class="kpi-card pass">
          <div class="kpi-value">{{ store.summary.pass_count }}</div>
          <div class="kpi-label">PASS</div>
        </div>
        <div class="kpi-card fail">
          <div class="kpi-value">{{ store.summary.fail_count }}</div>
          <div class="kpi-label">FAIL</div>
        </div>
        <div class="kpi-card yield">
          <div class="kpi-value">{{ store.summary.yield_pct.toFixed(1) }}%</div>
          <div class="kpi-label">PASS率</div>
        </div>
      </div>

      <!-- チャート行 -->
      <div class="chart-row">
        <!-- 合否率 棒グラフ -->
        <el-card class="chart-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center">
              <span class="card-title">合否率</span>
              <el-select v-model="store.yieldGroupBy" size="small" style="width:140px" @change="store.refresh()">
                <el-option label="シナリオ別" value="scenario" />
                <el-option label="デバイス別" value="device_id" />
                <el-option label="拠点別"     value="test_site" />
              </el-select>
            </div>
          </template>
          <v-chart :option="yieldChartOption" style="height:240px" autoresize />
        </el-card>

        <!-- 時系列 折れ線 -->
        <el-card class="chart-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center">
              <span class="card-title">PASS率推移</span>
              <el-select v-model="store.trendFreq" size="small" style="width:100px" @change="store.refresh()">
                <el-option label="1時間" value="1h" />
                <el-option label="1日"   value="1D" />
                <el-option label="1週"   value="1W" />
              </el-select>
            </div>
          </template>
          <v-chart :option="trendChartOption" style="height:240px" autoresize />
        </el-card>
      </div>

      <!-- 結果一覧テーブル -->
      <el-card style="margin-top:12px">
        <template #header>
          <span class="card-title">試験結果一覧 ({{ store.results.total }}件)</span>
        </template>
        <el-table
          :data="store.results.items"
          stripe
          size="small"
          style="width:100%"
          @row-click="(row: any) => store.loadDetail(row.run_id)"
        >
          <el-table-column prop="started_at"  label="日時"       width="160" />
          <el-table-column prop="scenario"    label="シナリオ"   min-width="120" />
          <el-table-column prop="device_id"   label="デバイスID" width="120" />
          <el-table-column label="結果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === 'PASS' ? 'success' : 'danger'" size="small">{{ row.result }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Pass/Total" width="100">
            <template #default="{ row }">{{ row.pass_count }}/{{ row.total }}</template>
          </el-table-column>
          <el-table-column prop="test_site" label="拠点" width="100" />
        </el-table>
      </el-card>
    </div>

    <!-- 詳細ドロワー -->
    <el-drawer
      v-model="drawerVisible"
      title="試験結果詳細"
      size="600px"
      direction="rtl"
    >
      <div v-if="store.selectedDetail">
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px">
          <el-descriptions-item label="run_id" :span="2">{{ store.selectedDetail.run_id }}</el-descriptions-item>
          <el-descriptions-item label="シナリオ">{{ store.selectedDetail.scenario }}</el-descriptions-item>
          <el-descriptions-item label="デバイス">{{ store.selectedDetail.device_id }}</el-descriptions-item>
          <el-descriptions-item label="結果">
            <el-tag :type="store.selectedDetail.result === 'PASS' ? 'success' : 'danger'">{{ store.selectedDetail.result }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="PASS率">
            {{ store.selectedDetail.total > 0 ? (store.selectedDetail.pass_count / store.selectedDetail.total * 100).toFixed(1) : 0 }}%
          </el-descriptions-item>
          <el-descriptions-item label="開始">{{ store.selectedDetail.started_at }}</el-descriptions-item>
          <el-descriptions-item label="終了">{{ store.selectedDetail.finished_at }}</el-descriptions-item>
        </el-descriptions>

        <el-table :data="store.selectedDetail.steps" size="small" stripe>
          <el-table-column prop="step_id"     label="#"      width="45" />
          <el-table-column prop="action"      label="アクション" width="120" />
          <el-table-column prop="description" label="説明" min-width="140" show-overflow-tooltip />
          <el-table-column label="結果" width="65">
            <template #default="{ row }">
              <el-tag :type="row.pass ? 'success' : 'danger'" size="small">{{ row.pass ? 'PASS' : 'FAIL' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error_msg" label="エラー" min-width="140" show-overflow-tooltip />
        </el-table>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, onMounted } from 'vue'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { useAndroidStore } from '@/stores/androidStore'

use([BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const store = useAndroidStore()
onMounted(() => store.init())

const drawerVisible = computed({
  get: () => store.selectedDetail !== null,
  set: (v) => { if (!v) store.selectedDetail = null },
})

function clearFilters() {
  store.selected.scenarios  = []
  store.selected.device_ids = []
  store.selected.results    = []
  store.selected.test_sites = []
  store.refresh()
}

const yieldChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['PASS', 'FAIL'], bottom: 0 },
  grid: { left: 8, right: 8, top: 8, bottom: 32, containLabel: true },
  xAxis: { type: 'category', data: store.yieldData.map(d => d.label), axisLabel: { rotate: 20 } },
  yAxis: { type: 'value', max: 100, name: '%' },
  series: [
    {
      name: 'PASS率', type: 'bar',
      data: store.yieldData.map(d => d.yield_pct),
      itemStyle: { color: '#67c23a' },
      label: { show: true, formatter: '{c}%', fontSize: 11 },
    },
  ],
}))

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 8, right: 8, top: 8, bottom: 16, containLabel: true },
  xAxis: { type: 'category', data: store.trendData?.labels || [], axisLabel: { rotate: 20 } },
  yAxis: { type: 'value', max: 100, name: '%' },
  series: [
    {
      name: 'PASS率', type: 'line',
      data: store.trendData?.values || [],
      smooth: true,
      lineStyle: { color: '#409eff' },
      areaStyle: { color: 'rgba(64,158,255,0.15)' },
    },
  ],
}))
</script>

<style scoped>
.android-dashboard {
  display: flex;
  height: 100%;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}
.filter-panel {
  width: 220px;
  flex-shrink: 0;
  overflow-y: auto;
}
.filter-group { margin-bottom: 12px; }
.filter-label { font-size: 12px; font-weight: 600; color: #606266; margin-bottom: 4px; }
.filter-group .el-checkbox { display: block; margin-left: 0; font-size: 12px; }
.main-content { flex: 1; overflow-y: auto; }
.kpi-row { display: flex; gap: 12px; margin-bottom: 12px; }
.kpi-card {
  flex: 1; background: #fff; border-radius: 8px; padding: 16px;
  text-align: center; border: 1px solid #e4e7ed;
}
.kpi-card.pass  { border-top: 3px solid #67c23a; }
.kpi-card.fail  { border-top: 3px solid #f56c6c; }
.kpi-card.yield { border-top: 3px solid #409eff; }
.kpi-value { font-size: 28px; font-weight: 700; color: #303133; }
.kpi-label { font-size: 12px; color: #909399; margin-top: 4px; }
.chart-row { display: flex; gap: 12px; }
.chart-card { flex: 1; }
.card-title { font-weight: 600; }
</style>
