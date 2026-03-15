<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <h2>opeAnyalyze</h2>
    </div>

    <el-divider>テーブル選択</el-divider>

    <el-button
      type="default"
      size="small"
      :loading="loading"
      @click="schemaStore.loadTables()"
      style="width: 100%; margin-bottom: 8px"
    >
      テーブル一覧を更新
    </el-button>

    <el-select
      v-model="selectedTable"
      placeholder="テーブルを選択"
      style="width: 100%"
      @change="schemaStore.selectTable($event)"
    >
      <el-option v-for="t in tables" :key="t" :value="t" :label="t" />
    </el-select>

    <el-alert v-if="error" :title="error" type="error" :closable="false" style="margin-top: 8px" />

    <template v-if="selectedTable">
      <el-divider>分析設定</el-divider>
      <AnalysisForm />
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSchemaStore } from '@/stores/schemaStore'
import AnalysisForm from '@/components/controls/AnalysisForm.vue'

const schemaStore = useSchemaStore()
const { tables, selectedTable, loading, error } = storeToRefs(schemaStore)

onMounted(() => schemaStore.loadTables())
</script>

<style scoped>
.sidebar {
  padding: 16px;
  height: 100vh;
  overflow-y: auto;
  background: #f5f7fa;
  border-right: 1px solid #dcdfe6;
}
.sidebar-header h2 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #303133;
}
</style>
