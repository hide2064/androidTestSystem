<template>
  <div class="chart-card">
    <div class="chart-toolbar">
      <span class="chart-title">合否率（グループ別）</span>
      <el-select v-model="groupBy" size="small" style="width: 160px" @change="emit('change-group', groupBy)">
        <el-option v-for="g in groups" :key="g.value" :value="g.value" :label="g.label" />
      </el-select>
    </div>
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, ToolboxComponent } from 'echarts/components'
import type { YieldItem } from '@/api/rf'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent, ToolboxComponent])

const props = defineProps<{ items: YieldItem[]; modelGroupBy: string }>()
const emit = defineEmits<{ (e: 'change-group', val: string): void }>()

const groupBy = ref(props.modelGroupBy)

const groups = [
  { value: 'Test_Item',       label: 'テスト項目' },
  { value: 'DUT_Model',       label: 'DUTモデル' },
  { value: 'Technology',      label: 'テクノロジー' },
  { value: 'Band',            label: 'バンド' },
  { value: 'Temperature_C',   label: '温度' },
  { value: 'Supply_Voltage_V',label: '電源電圧' },
  { value: 'Operator_ID',     label: 'オペレータ' },
]

const option = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params: { seriesName: string; value: number; name: string }[]) => {
      const label = params[0]?.name ?? ''
      const pass = params.find(p => p.seriesName === 'PASS')?.value ?? 0
      const fail = params.find(p => p.seriesName === 'FAIL')?.value ?? 0
      const total = pass + fail
      const yld = total > 0 ? ((pass / total) * 100).toFixed(1) : '0'
      return `${label}<br/>PASS: ${pass}<br/>FAIL: ${fail}<br/>歩留り: ${yld}%`
    },
  },
  legend: {},
  toolbox: { feature: { saveAsImage: {} } },
  xAxis: {
    type: 'category',
    data: props.items.map(i => i.label),
    axisLabel: { rotate: 30, fontSize: 11 },
  },
  yAxis: { type: 'value', name: '件数' },
  series: [
    {
      name: 'PASS',
      type: 'bar',
      stack: 'total',
      data: props.items.map(i => i.pass_count),
      itemStyle: { color: '#67c23a' },
    },
    {
      name: 'FAIL',
      type: 'bar',
      stack: 'total',
      data: props.items.map(i => i.fail_count),
      itemStyle: { color: '#f56c6c' },
    },
  ],
}))
</script>

<style scoped>
.chart-card { background: #fff; border-radius: 8px; padding: 12px; }
.chart-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.chart-title { font-size: 14px; font-weight: 600; color: #303133; }
.chart { width: 100%; height: 320px; }
</style>
