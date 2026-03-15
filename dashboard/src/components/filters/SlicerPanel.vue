<template>
  <div class="slicer-panel">
    <div class="slicer-header">
      <span>フィルタ</span>
      <el-button size="small" link @click="clearAll">すべてクリア</el-button>
    </div>

    <div class="slicer-grid">
      <div v-for="item in slicerDefs" :key="item.key" class="slicer-item">
        <div class="slicer-label">{{ item.label }}</div>
        <el-select
          v-model="selected[item.selKey]"
          multiple
          collapse-tags
          collapse-tags-tooltip
          :placeholder="'すべて'"
          size="small"
          style="width: 100%"
          @change="onFilter"
        >
          <el-option
            v-for="v in availableFilters[item.filterKey]"
            :key="v"
            :value="v"
            :label="v"
          />
        </el-select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useRfStore } from '@/stores/rfStore'

const rfStore = useRfStore()
const { availableFilters, selected } = storeToRefs(rfStore)

const slicerDefs = [
  { key: 'dut_model',   selKey: 'dut_models',   filterKey: 'DUT_Model',       label: 'DUTモデル' },
  { key: 'technology',  selKey: 'technologies',  filterKey: 'Technology',      label: 'テクノロジー' },
  { key: 'band',        selKey: 'bands',         filterKey: 'Band',            label: 'バンド' },
  { key: 'temperature', selKey: 'temperatures',  filterKey: 'Temperature_C',   label: '温度 (℃)' },
  { key: 'voltage',     selKey: 'voltages',      filterKey: 'Supply_Voltage_V',label: '電源電圧 (V)' },
  { key: 'judgment',    selKey: 'judgments',     filterKey: 'Judgment',        label: '合否' },
  { key: 'operator',    selKey: 'operators',     filterKey: 'Operator_ID',     label: 'オペレータ' },
] as const

function onFilter() {
  rfStore.refresh()
}

function clearAll() {
  for (const k of Object.keys(selected.value)) {
    selected.value[k] = []
  }
  rfStore.refresh()
}
</script>

<style scoped>
.slicer-panel {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 8px 16px;
}
.slicer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 6px;
}
.slicer-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.slicer-item {
  min-width: 140px;
  flex: 1 1 140px;
  max-width: 220px;
}
.slicer-label {
  font-size: 11px;
  color: #909399;
  margin-bottom: 2px;
}
</style>
