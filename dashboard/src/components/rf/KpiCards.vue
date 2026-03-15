<template>
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-label">総測定数</div>
      <div class="kpi-value">{{ fmt(summary?.total) }}</div>
    </div>
    <div class="kpi-card pass">
      <div class="kpi-label">PASS</div>
      <div class="kpi-value">{{ fmt(summary?.pass_count) }}</div>
    </div>
    <div class="kpi-card fail">
      <div class="kpi-label">FAIL</div>
      <div class="kpi-value">{{ fmt(summary?.fail_count) }}</div>
    </div>
    <div class="kpi-card yield" :class="{ warn: (summary?.yield_pct ?? 100) < 95 }">
      <div class="kpi-label">歩留り</div>
      <div class="kpi-value">{{ summary ? summary.yield_pct.toFixed(1) + ' %' : '-' }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SummaryData } from '@/api/rf'
defineProps<{ summary: SummaryData | null }>()
const fmt = (n?: number) => n != null ? n.toLocaleString() : '-'
</script>

<style scoped>
.kpi-row { display: flex; gap: 12px; flex-wrap: wrap; }
.kpi-card {
  flex: 1 1 100px;
  padding: 12px 16px;
  border-radius: 8px;
  background: #f5f7fa;
  border-left: 4px solid #dcdfe6;
}
.kpi-card.pass  { border-color: #67c23a; background: #f0f9eb; }
.kpi-card.fail  { border-color: #f56c6c; background: #fef0f0; }
.kpi-card.yield { border-color: #409eff; background: #ecf5ff; }
.kpi-card.yield.warn { border-color: #e6a23c; background: #fdf6ec; }
.kpi-label { font-size: 12px; color: #909399; margin-bottom: 4px; }
.kpi-value { font-size: 24px; font-weight: 700; color: #303133; }
</style>
