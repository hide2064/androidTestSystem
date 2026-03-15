<template>
  <v-chart class="chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { HeatmapChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import type { CorrelationData } from '@/types'

use([CanvasRenderer, HeatmapChart, GridComponent, TooltipComponent, VisualMapComponent])

const props = defineProps<{ data: CorrelationData }>()

const option = computed(() => {
  const cols = props.data.columns
  const heatData: [number, number, number][] = []
  for (let i = 0; i < cols.length; i++) {
    for (let j = 0; j < cols.length; j++) {
      heatData.push([j, i, props.data.matrix[i][j]])
    }
  }
  return {
    tooltip: {
      formatter: (p: { value: [number, number, number] }) =>
        `${cols[p.value[1]]} × ${cols[p.value[0]]}: ${p.value[2].toFixed(3)}`,
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      inRange: { color: ['#d73027', '#ffffff', '#1a9850'] },
    },
    xAxis: { type: 'category', data: cols, axisLabel: { rotate: 30 } },
    yAxis: { type: 'category', data: cols },
    series: [
      {
        type: 'heatmap',
        data: heatData,
        label: { show: true, formatter: (p: { value: [number, number, number] }) => p.value[2].toFixed(2) },
      },
    ],
  }
})
</script>

<style scoped>
.chart { width: 100%; height: 500px; }
</style>
