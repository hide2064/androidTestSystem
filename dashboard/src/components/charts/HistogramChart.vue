<template>
  <v-chart class="chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, ToolboxComponent } from 'echarts/components'
import type { DistributionData } from '@/types'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, ToolboxComponent])

const props = defineProps<{ data: DistributionData; column: string }>()

const option = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params: unknown[]) => {
      const p = (params as { dataIndex: number; value: number }[])[0]
      const i = p.dataIndex
      const left = props.data.bin_edges[i].toFixed(2)
      const right = props.data.bin_edges[i + 1].toFixed(2)
      return `${left} ~ ${right}<br/>件数: ${p.value}`
    },
  },
  toolbox: { feature: { saveAsImage: {} } },
  xAxis: {
    type: 'category',
    data: props.data.bin_centers.map((c) => c.toFixed(2)),
    name: props.column,
    axisLabel: { rotate: 30 },
  },
  yAxis: { type: 'value', name: '件数' },
  series: [
    {
      type: 'bar',
      data: props.data.counts,
      barWidth: '99%',
      itemStyle: { color: '#5470c6' },
    },
  ],
}))
</script>

<style scoped>
.chart { width: 100%; height: 400px; }
</style>
