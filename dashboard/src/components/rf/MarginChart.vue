<template>
  <div class="chart-card">
    <div class="chart-toolbar">
      <span class="chart-title">マージン分析</span>
      <el-select v-model="localXAxis" size="small" style="width:140px" @change="emit('change-x', localXAxis)">
        <el-option value="Temperature_C"    label="温度 (℃)" />
        <el-option value="Supply_Voltage_V" label="電源電圧 (V)" />
        <el-option value="UL_Frequency_MHz" label="UL周波数" />
        <el-option value="DL_Frequency_MHz" label="DL周波数" />
      </el-select>
    </div>
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { ScatterChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, ToolboxComponent } from 'echarts/components'
import type { MarginPoint } from '@/api/rf'

use([CanvasRenderer, ScatterChart, LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, ToolboxComponent])

const props = defineProps<{ points: MarginPoint[]; activeXAxis: string }>()
const emit = defineEmits<{ (e: 'change-x', val: string): void }>()

const localXAxis = ref(props.activeXAxis)
watch(() => props.activeXAxis, v => { localXAxis.value = v })

const xLabels: Record<string, string> = {
  Temperature_C: '温度 (℃)',
  Supply_Voltage_V: '電源電圧 (V)',
  UL_Frequency_MHz: 'UL周波数 (MHz)',
  DL_Frequency_MHz: 'DL周波数 (MHz)',
}

const option = computed(() => {
  const pass = props.points.filter(p => p.judgment === 'PASS')
  const fail = props.points.filter(p => p.judgment === 'FAIL')
  const allUpper = props.points.find(p => p.upper_limit != null)?.upper_limit
  const allLower = props.points.find(p => p.lower_limit != null)?.lower_limit

  const markLines = []
  if (allUpper != null) markLines.push({ yAxis: allUpper, name: `上限: ${allUpper}`, lineStyle: { color: '#f56c6c', type: 'dashed' } })
  if (allLower != null) markLines.push({ yAxis: allLower, name: `下限: ${allLower}`, lineStyle: { color: '#e6a23c', type: 'dashed' } })

  return {
    tooltip: {
      formatter: (p: { seriesName: string; value: [number, number]; data: MarginPoint }) => {
        const d = p.data
        return `${p.seriesName}<br/>${xLabels[props.activeXAxis]}: ${d.x}<br/>測定値: ${d.measured}<br/>判定: ${d.judgment}`
      },
    },
    legend: {},
    toolbox: { feature: { saveAsImage: {} } },
    xAxis: { type: 'value', name: xLabels[props.activeXAxis] },
    yAxis: { type: 'value', name: '測定値' },
    series: [
      {
        name: 'PASS',
        type: 'scatter' as const,
        data: pass.map(p => ({ value: [p.x, p.measured], ...p })),
        itemStyle: { color: '#67c23a', opacity: 0.7 },
        symbolSize: 8,
      },
      {
        name: 'FAIL',
        type: 'scatter' as const,
        data: fail.map(p => ({ value: [p.x, p.measured], ...p })),
        itemStyle: { color: '#f56c6c' },
        symbolSize: 12,
        symbol: 'triangle',
      },
      markLines.length > 0 ? {
        name: '限界値',
        type: 'line' as const,
        data: [],
        markLine: {
          silent: true,
          data: markLines.map(ml => [{ yAxis: ml.yAxis, name: ml.name }, { yAxis: ml.yAxis }]),
          lineStyle: { color: '#f56c6c', type: 'dashed' },
          label: { formatter: (p: { name: string }) => p.name },
        },
      } : null,
    ].filter(Boolean),
  }
})
</script>

<style scoped>
.chart-card { background: #fff; border-radius: 8px; padding: 12px; }
.chart-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.chart-title { font-size: 14px; font-weight: 600; color: #303133; }
.chart { width: 100%; height: 280px; }
</style>
