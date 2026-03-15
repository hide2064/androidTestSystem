<template>
  <div class="result-area">
    <!-- ローディング -->
    <div v-if="loading" class="center-message">
      <el-icon class="is-loading" :size="48"><Loading /></el-icon>
      <p>分析中...</p>
    </div>

    <!-- エラー -->
    <el-alert v-else-if="error" :title="error" type="error" :closable="false" />

    <!-- 結果なし -->
    <div v-else-if="!result" class="center-message">
      <el-empty description="左のパネルでテーブルと分析種別を選択して「分析実行」してください" />
    </div>

    <!-- 基本統計 -->
    <template v-else-if="result.type === 'statistics'">
      <h3>基本統計</h3>
      <div v-for="(stat, col) in (result.data as StatisticsData)" :key="col" class="stat-card">
        <h4>{{ col }}</h4>
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="件数">{{ stat.count }}</el-descriptions-item>
          <el-descriptions-item label="欠損">{{ stat.null_count }}</el-descriptions-item>
          <template v-if="stat.mean !== undefined">
            <el-descriptions-item label="平均">{{ stat.mean }}</el-descriptions-item>
            <el-descriptions-item label="標準偏差">{{ stat.std }}</el-descriptions-item>
            <el-descriptions-item label="最小">{{ stat.min }}</el-descriptions-item>
            <el-descriptions-item label="25%tile">{{ stat.q25 }}</el-descriptions-item>
            <el-descriptions-item label="中央値">{{ stat.median }}</el-descriptions-item>
            <el-descriptions-item label="75%tile">{{ stat.q75 }}</el-descriptions-item>
            <el-descriptions-item label="最大">{{ stat.max }}</el-descriptions-item>
          </template>
          <template v-else-if="stat.unique !== undefined">
            <el-descriptions-item label="ユニーク数">{{ stat.unique }}</el-descriptions-item>
          </template>
        </el-descriptions>
        <div v-if="stat.top_values" class="top-values">
          <p>上位値:</p>
          <el-tag v-for="(cnt, val) in stat.top_values" :key="val" style="margin: 2px">
            {{ val }}: {{ cnt }}
          </el-tag>
        </div>
      </div>
    </template>

    <!-- 時系列 -->
    <template v-else-if="result.type === 'timeseries'">
      <h3>時系列分析</h3>
      <LineChart :data="(result.data as TimeseriesData)" />
    </template>

    <!-- 分布 -->
    <template v-else-if="result.type === 'distribution'">
      <h3>分布（ヒストグラム）</h3>
      <HistogramChart :data="(result.data as DistributionData)" :column="''" />
      <p class="summary">総件数: {{ (result.data as DistributionData).total }} / 欠損: {{ (result.data as DistributionData).null_count }}</p>
    </template>

    <!-- 相関 -->
    <template v-else-if="result.type === 'correlation'">
      <h3>相関行列</h3>
      <HeatmapChart :data="(result.data as CorrelationData)" />
    </template>

    <!-- グループ集計 -->
    <template v-else-if="result.type === 'groupby'">
      <h3>グループ集計</h3>
      <BarChart :data="(result.data as GroupbyData)" style="margin-bottom: 16px" />
      <el-table :data="tableRows" border stripe size="small" max-height="400">
        <el-table-column
          v-for="col in (result.data as GroupbyData).columns"
          :key="col"
          :prop="col"
          :label="col"
          sortable
        />
      </el-table>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useAnalysisStore } from '@/stores/analysisStore'
import { Loading } from '@element-plus/icons-vue'
import LineChart from '@/components/charts/LineChart.vue'
import HistogramChart from '@/components/charts/HistogramChart.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import type {
  StatisticsData, TimeseriesData, DistributionData, CorrelationData, GroupbyData
} from '@/types'

const analysisStore = useAnalysisStore()
const { result, loading, error } = storeToRefs(analysisStore)

const tableRows = computed(() => {
  if (result.value?.type !== 'groupby') return []
  const data = result.value.data as GroupbyData
  return data.rows.map((row: (string | null)[]) => {
    const obj: Record<string, string | null> = {}
    data.columns.forEach((col: string, i: number) => { obj[col] = row[i] })
    return obj
  })
})
</script>

<style scoped>
.result-area {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}
.center-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  color: #909399;
}
.stat-card {
  margin-bottom: 20px;
  padding: 12px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
}
.stat-card h4 {
  margin: 0 0 8px 0;
  color: #303133;
}
.top-values {
  margin-top: 8px;
}
.summary {
  margin-top: 8px;
  color: #606266;
  font-size: 13px;
}
</style>
