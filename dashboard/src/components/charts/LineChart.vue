<template>
  <v-chart class="chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, ToolboxComponent, DataZoomComponent } from 'echarts/components'
import type { TimeseriesData } from '@/types'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, ToolboxComponent, DataZoomComponent])

const props = defineProps<{ data: TimeseriesData }>()

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: props.data.series.map((s: { name: string; values: number[] }) => s.name) },
  toolbox: { feature: { saveAsImage: {} } },
  dataZoom: [{ type: 'inside' }, { type: 'slider' }],
  xAxis: {
    type: 'category',
    data: props.data.labels,
    axisLabel: { rotate: 30 },
  },
  yAxis: { type: 'value' },
  series: props.data.series.map((s: { name: string; values: number[] }) => ({
    name: s.name,
    type: 'line',
    data: s.values,
    smooth: true,
  })),
}))
</script>

<style scoped>
.chart { width: 100%; height: 400px; }
</style>
