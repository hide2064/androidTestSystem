<template>
  <div class="test-control">
    <!-- 左ペイン：制御パネル -->
    <div class="control-panel">
      <el-card class="panel-card">
        <template #header><span class="card-title">試験設定</span></template>

        <el-form label-position="top" size="small">
          <el-form-item label="シナリオ">
            <el-select v-model="store.selectedScenario" style="width:100%" placeholder="選択してください">
              <el-option
                v-for="s in store.scenarios"
                :key="s.name"
                :label="s.display_name || s.name"
                :value="s.name"
              />
            </el-select>
            <div v-if="selectedScenarioInfo" class="scenario-desc">
              {{ selectedScenarioInfo.description }} ({{ selectedScenarioInfo.step_count }} ステップ)
            </div>
          </el-form-item>

          <el-form-item label="デバイスID">
            <el-input v-model="store.deviceId" placeholder="例: device-001" />
          </el-form-item>
        </el-form>

        <div class="control-buttons">
          <el-button
            type="primary"
            :disabled="store.isRunning || !store.selectedScenario"
            :loading="store.loading"
            @click="store.startTest()"
            style="width:100%"
          >
            ▶ 試験開始
          </el-button>
          <el-button
            type="danger"
            :disabled="!store.isRunning"
            @click="store.stopTest()"
            style="width:100%; margin-top:8px"
          >
            ■ 中断
          </el-button>
        </div>

        <el-alert v-if="store.error" :title="store.error" type="error" :closable="false" style="margin-top:12px" />
      </el-card>

      <!-- ステータスカード -->
      <el-card class="panel-card" style="margin-top:12px">
        <template #header><span class="card-title">ステータス</span></template>
        <div class="status-row">
          <el-tag :type="statusType" size="large">{{ statusLabel }}</el-tag>
        </div>
        <div v-if="store.status.scenario" class="status-detail">
          <div><b>シナリオ:</b> {{ store.status.scenario }}</div>
          <div><b>デバイス:</b> {{ store.status.device }}</div>
          <div v-if="store.status.elapsed"><b>経過時間:</b> {{ store.status.elapsed }}</div>
          <div v-if="store.status.current_step">
            <b>現在ステップ:</b> [{{ store.status.current_step.id }}] {{ store.status.current_step.description }}
          </div>
        </div>
      </el-card>
    </div>

    <!-- 右ペイン：リアルタイムログ -->
    <div class="log-panel">
      <el-card class="log-card">
        <template #header>
          <div style="display:flex; justify-content:space-between; align-items:center">
            <span class="card-title">リアルタイムログ</span>
            <el-button size="small" @click="store.logs.length = 0">クリア</el-button>
          </div>
        </template>
        <div ref="logContainer" class="log-container">
          <div
            v-for="(log, idx) in store.logs"
            :key="idx"
            :class="['log-line', `log-${log.level?.toLowerCase()}`]"
          >
            <span class="log-ts">{{ log.ts || '' }}</span>
            <span v-if="log.step_id" class="log-step">[Step {{ log.step_id }}]</span>
            <el-tag v-if="log.pass === true"  size="small" type="success" style="margin:0 4px">PASS</el-tag>
            <el-tag v-if="log.pass === false" size="small" type="danger"  style="margin:0 4px">FAIL</el-tag>
            <span class="log-msg">{{ log.message }}</span>
          </div>
          <div v-if="store.logs.length === 0" class="log-empty">試験を開始するとログが表示されます</div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useTestStore } from '@/stores/testStore'

const store = useTestStore()
const logContainer = ref<HTMLElement | null>(null)

onMounted(() => store.init())
onUnmounted(() => store.destroy())

const selectedScenarioInfo = computed(() =>
  store.scenarios.find(s => s.name === store.selectedScenario) || null
)

const statusType = computed(() => {
  if (store.status.status === 'running') return 'warning'
  if (store.status.status === 'error')   return 'danger'
  return 'info'
})

const statusLabel = computed(() => {
  if (store.status.status === 'running') return '実行中'
  if (store.status.status === 'error')   return 'エラー'
  return 'アイドル'
})

// ログが追加されたら自動スクロール
watch(() => store.logs.length, async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
})
</script>

<style scoped>
.test-control {
  display: flex;
  height: 100%;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}
.control-panel {
  width: 280px;
  flex-shrink: 0;
  overflow-y: auto;
}
.log-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.panel-card, .log-card { height: fit-content; }
.log-card { flex: 1; display: flex; flex-direction: column; }
.log-card :deep(.el-card__body) { flex: 1; padding: 0; overflow: hidden; }
.card-title { font-weight: 600; }
.scenario-desc { font-size: 12px; color: #909399; margin-top: 4px; }
.control-buttons { margin-top: 16px; }
.status-row { margin-bottom: 8px; }
.status-detail { font-size: 13px; line-height: 1.8; color: #606266; }
.log-container {
  height: 100%;
  min-height: 400px;
  overflow-y: auto;
  padding: 8px 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: #1e1e1e;
  color: #d4d4d4;
}
.log-line { padding: 2px 0; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.log-ts   { color: #6a9955; font-size: 11px; flex-shrink: 0; }
.log-step { color: #569cd6; flex-shrink: 0; }
.log-msg  { flex: 1; word-break: break-all; }
.log-info    .log-msg { color: #d4d4d4; }
.log-warning .log-msg { color: #dcdcaa; }
.log-error   .log-msg { color: #f44747; }
.log-debug   .log-msg { color: #808080; }
.log-empty { color: #555; text-align: center; padding: 20px; }
</style>
