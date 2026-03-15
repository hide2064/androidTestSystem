<template>
  <div class="app">
    <div class="nav-bar">
      <span class="nav-logo">TestSystem</span>
      <el-tabs v-model="activeTab" class="nav-tabs">
        <el-tab-pane label="試験実行"     name="control"  />
        <el-tab-pane label="Android分析"  name="android"  />
        <el-tab-pane label="RF分析"       name="rf"       />
        <el-tab-pane label="汎用分析"     name="general"  />
      </el-tabs>
    </div>

    <div class="app-content">
      <TestControlView      v-if="activeTab === 'control'"  />
      <AndroidDashboardView v-if="activeTab === 'android'"  />
      <RfDashboardView      v-if="activeTab === 'rf'"       />
      <el-container         v-if="activeTab === 'general'"  style="height:100%">
        <el-aside width="320px"><AppSidebar /></el-aside>
        <el-main style="padding:0; overflow:hidden"><AnalysisView /></el-main>
      </el-container>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppSidebar           from '@/components/layout/AppSidebar.vue'
import AnalysisView         from '@/views/AnalysisView.vue'
import RfDashboardView      from '@/views/RfDashboardView.vue'
import TestControlView      from '@/views/TestControlView.vue'
import AndroidDashboardView from '@/views/AndroidDashboardView.vue'

const activeTab = ref('control')
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #f0f2f5; }
.app { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.nav-bar {
  display: flex; align-items: center;
  background: #fff; border-bottom: 1px solid #e4e7ed;
  padding: 0 16px; height: 48px; flex-shrink: 0; gap: 16px;
}
.nav-logo { font-size: 16px; font-weight: 700; color: #409eff; white-space: nowrap; }
.nav-tabs { flex: 1; }
.nav-tabs :deep(.el-tabs__header) { margin: 0; }
.nav-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.app-content { flex: 1; overflow: hidden; }
</style>
