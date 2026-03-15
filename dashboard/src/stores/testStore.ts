import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/orchestrator'

export interface LogEntry {
  level: string
  message: string
  step_id?: number
  pass?: boolean
  ts?: string
}

export const useTestStore = defineStore('test', () => {
  const scenarios = ref<api.Scenario[]>([])
  const status = ref<api.TestStatus>({ status: 'idle', scenario: null, device: null, start_time: null, elapsed: null, current_step: null })
  const logs = ref<LogEntry[]>([])
  const selectedScenario = ref('')
  const deviceId = ref('device-001')
  const loading = ref(false)
  const error = ref<string | null>(null)

  let ws: WebSocket | null = null
  let pollTimer: ReturnType<typeof setInterval> | null = null

  const isRunning = computed(() => status.value.status === 'running')

  async function loadScenarios() {
    try {
      scenarios.value = await api.fetchScenarios()
      if (scenarios.value.length > 0 && !selectedScenario.value) {
        selectedScenario.value = scenarios.value[0].name
      }
    } catch (e: any) {
      error.value = `シナリオ取得失敗: ${e.message}`
    }
  }

  async function refreshStatus() {
    try {
      status.value = await api.fetchStatus()
    } catch (_) {}
  }

  function connectWebSocket() {
    if (ws) return
    const wsUrl = window.location.hostname === 'localhost'
      ? 'ws://localhost:8000/ws/log'
      : `ws://${window.location.host}/api/orchestrator/ws/log`
    ws = new WebSocket(wsUrl)
    ws.onmessage = (ev) => {
      try {
        const entry: LogEntry = JSON.parse(ev.data)
        logs.value.push(entry)
        if (logs.value.length > 500) logs.value.shift()
      } catch (_) {}
    }
    ws.onclose = () => {
      ws = null
      // 切断時は3秒後に再接続
      setTimeout(connectWebSocket, 3000)
    }
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(refreshStatus, 2000)
  }

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  }

  async function startTest() {
    if (!selectedScenario.value) return
    loading.value = true
    error.value = null
    logs.value = []
    try {
      await api.startTest(selectedScenario.value, deviceId.value)
      await refreshStatus()
    } catch (e: any) {
      error.value = `試験開始失敗: ${e.response?.data?.detail || e.message}`
    } finally {
      loading.value = false
    }
  }

  async function stopTest() {
    try {
      await api.stopTest()
      await refreshStatus()
    } catch (e: any) {
      error.value = `停止失敗: ${e.response?.data?.detail || e.message}`
    }
  }

  function init() {
    loadScenarios()
    refreshStatus()
    connectWebSocket()
    startPolling()
  }

  function destroy() {
    stopPolling()
    if (ws) { ws.close(); ws = null }
  }

  return {
    scenarios, status, logs, selectedScenario, deviceId,
    loading, error, isRunning,
    init, destroy, startTest, stopTest, refreshStatus,
  }
})
