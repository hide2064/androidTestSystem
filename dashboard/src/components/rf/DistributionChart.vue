<template>
  <div class="chart-card">
    <div class="chart-toolbar">
      <span class="chart-title">測定値分布</span>
      <div style="display:flex; gap:8px; flex-wrap:wrap">
        <el-select v-model="localTestItem" size="small" style="width:180px" @change="emit('change-test-item', localTestItem)">
          <el-option v-for="t in testItems" :key="t" :value="t" :label="t" />
        </el-select>
        <el-select v-model="localGroupBy" size="small" style="width:130px" @change="emit('change-group', localGroupBy)">
          <el-option value="DUT_Model"        label="DUTモデル" />
          <el-option value="Technology"       label="テクノロジー" />
          <el-option value="Temperature_C"    label="温度" />
          <el-option value="Supply_Voltage_V" label="電源電圧" />
        </el-select>
      </div>
    </div>
    <v-chart class="chart" :option="option" autoresize />
    <!-- 統計テーブル -->
    <el-table :data="stats" size="small" border stripe style="margin-top:8px">
      <el-table-column prop="group"       label="グループ"  width="120" />
      <el-table-column prop="count"       label="件数"       width="70" />
      <el-table-column prop="avg"         label="平均"       width="90" />
      <el-table-column prop="std"         label="標準偏差"   width="90" />
      <el-table-column prop="min"         label="最小"       width="90" />
      <el-table-column prop="max"         label="最大"       width="90" />
      <el-table-column prop="upper_limit" label="上限"       width="90" />
      <el-table-column prop="lower_limit" label="下限"       width="90" />
      <el-table-column prop="unit"        label="単位"       width="60" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { ScatterChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, ToolboxComponent } from 'echarts/components'
import type { DistributionStat, DistributionRaw } from '@/api/rf'

use([CanvasRenderer, ScatterChart, LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, ToolboxComponent])

const props = defineProps<{
  testItems: string[]
  activeTestItem: string
  activeGroupBy: string
  stats: DistributionStat[]
  raw: DistributionRaw[]
}>()

const emit = defineEmits<{
  (e: 'change-test-item', val: string): void
  (e: 'change-group', val: string): void
}>()

const localTestItem = ref(props.activeTestItem)
const localGroupBy  = ref(props.activeGroupBy)

watch(() => props.activeTestItem, v => { localTestItem.value = v })
watch(() => props.activeGroupBy,  v => { localGroupBy.value = v })

// グループごとに色を割り当て
const COLORS = ['#5470c6','#91cc75','#fac858','#ee6666','#73c0de','#3ba272','#fc8452']

const option = computed(() => {
  const groups = [...new Set(props.raw.map(r => r.group))]
  const unit = props.stats[0]?.unit ?? ''

  // 上下限線
  const upperLimit = props.stats[0]?.upper_limit
  const lowerLimit = props.stats[0]?.lower_limit
  const markLines: { yAxis: number; name: string; lineStyle: { color: string; type: string } }[] = []
  if (upperLimit != null) markLines.push({ yAxis: upperLimit, name: '上限', lineStyle: { color: '#f56c6c', type: 'dashed' } })
  if (lowerLimit != null) markLines.push({ yAxis: lowerLimit, name: '下限', lineStyle: { color: '#e6a23c', type: 'dashed' } })

  return {
    tooltip: {
      trigger: 'item',
      formatter: (p: { seriesName: string; value: [number, number]; data: { judgment: string } }) =>
        `${p.seriesName}<br/>x: ${p.value[0]}<br/>値: ${p.value[1]} ${unit}<br/>判定: ${p.data?.judgment ?? ''}`,
    },
    legend: { data: groups },
    toolbox: { feature: { saveAsImage: {} } },
    xAxis: { type: 'value', name: 'インデックス' },
    yAxis: { type: 'value', name: unit },
    series: [
      ...groups.map((g, gi) => ({
        name: g,
        type: 'scatter' as const,
        symbolSize: (d: { judgment: string }) => d.judgment === 'FAIL' ? 12 : 6,
        data: props.raw
          .filter(r => r.group === g)
          .map((r, i) => ({ value: [i, r.value], judgment: r.judgment })),
        itemStyle: {
          color: COLORS[gi % COLORS.length],
          opacity: 0.7,
        },
      })),
      // マーク用ダミー系列
      markLines.length > 0 ? {
        name: '限界値',
        type: 'line' as const,
        data: [],
        markLine: {
          silent: true,
          data: markLines.map(ml => ([{ yAxis: ml.yAxis, name: ml.name }, { yAxis: ml.yAxis }])),
          lineStyle: { color: '#f56c6c', type: 'dashed' },
          label: { formatter: (p: { name: string; value: number }) => `${p.name}: ${p.value}` },
        },
      } : null,
    ].filter(Boolean),
  }
})
</script>

<style scoped>
.chart-card { background: #fff; border-radius: 8px; padding: 12px; }
.chart-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.chart-title { font-size: 14px; font-weight: 600; color: #303133; }
.chart { width: 100%; height: 280px; }
</style>
