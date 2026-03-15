<template>
  <div class="chart-card">
    <div class="chart-toolbar">
      <span class="chart-title">時系列推移</span>
      <div style="display:flex; gap:8px; flex-wrap:wrap">
        <el-select v-model="localMetric" size="small" style="width:130px" @change="emit('change-metric', localMetric)">
          <el-option value="yield"     label="歩留り (%)" />
          <el-option value="avg_value" label="測定値 (平均)" />
        </el-select>
        <el-select v-model="localFreq" size="small" style="width:100px" @change="emit('change-freq', localFreq)">
          <el-option value="1h"  label="1時間" />
          <el-option value="1D"  label="1日" />
          <el-option value="1W"  label="1週間" />
          <el-option value="1ME" label="1ヶ月" />
        </el-select>
      </div>
    </div>
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, MarkLineComponent, DataZoomComponent, ToolboxComponent } from 'echarts/components'
import type { TrendData } from '@/api/rf'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, MarkLineComponent, DataZoomComponent, ToolboxComponent])

const props = defineProps<{ data: TrendData | null; activeFreq: string; activeMetric: string }>()
const emit = defineEmits<{
  (e: 'change-freq',   val: string): void
  (e: 'change-metric', val: string): void
}>()

const localFreq   = ref(props.activeFreq)
const localMetric = ref(props.activeMetric)
watch(() => props.activeFreq,   v => { localFreq.value = v })
watch(() => props.activeMetric, v => { localMetric.value = v })

const option = computed(() => {
  const d = props.data
  const isYield = d?.metric === 'yield'
  return {
    tooltip: { trigger: 'axis' },
    toolbox: { feature: { saveAsImage: {}, dataZoom: {} } },
    dataZoom: [{ type: 'inside' }, { type: 'slider' }],
    xAxis: {
      type: 'category',
      data: d?.labels ?? [],
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: isYield ? '歩留り (%)' : '測定値',
      min: isYield ? 0 : undefined,
      max: isYield ? 100 : undefined,
    },
    series: [
      {
        name: isYield ? '歩留り' : '測定値 (平均)',
        type: 'line',
        data: d?.values ?? [],
        smooth: true,
        markLine: isYield ? {
          silent: true,
          data: [{ yAxis: 95, name: '目標 95%', lineStyle: { color: '#e6a23c', type: 'dashed' } }],
          label: { formatter: '{b}' },
        } : undefined,
      },
    ],
  }
})
</script>

<style scoped>
.chart-card { background: #fff; border-radius: 8px; padding: 12px; }
.chart-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.chart-title { font-size: 14px; font-weight: 600; color: #303133; }
.chart { width: 100%; height: 260px; }
</style>
