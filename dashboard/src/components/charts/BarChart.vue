<template>
  <v-chart class="chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, ToolboxComponent, DataZoomComponent } from 'echarts/components'
import type { GroupbyData } from '@/types'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent, ToolboxComponent, DataZoomComponent])

const props = defineProps<{ data: GroupbyData }>()

const option = computed(() => {
  const labelCol = props.data.columns[props.data.columns.length - 2] ?? props.data.columns[0]
  const valueCol = props.data.columns[props.data.columns.length - 1]
  const labelIdx = props.data.columns.indexOf(labelCol)
  const valueIdx = props.data.columns.indexOf(valueCol)

  // グループカラムが複数ある場合は結合してラベルにする
  const groupCols = props.data.columns.slice(0, props.data.columns.length - 1)
  const labels = props.data.rows.map((row) =>
    groupCols.map((_, i) => row[i] ?? '').join(' / ')
  )
  const values = props.data.rows.map((row) => Number(row[valueIdx]))

  return {
    tooltip: { trigger: 'axis' },
    toolbox: { feature: { saveAsImage: {} } },
    dataZoom: [{ type: 'inside', orient: 'horizontal' }],
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: valueCol },
    series: [
      {
        type: 'bar',
        name: valueCol,
        data: values,
        itemStyle: { color: '#91cc75' },
      },
    ],
  }
})
</script>

<style scoped>
.chart { width: 100%; height: 400px; }
</style>
