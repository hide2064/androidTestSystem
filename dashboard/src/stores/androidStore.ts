import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/android'

export const useAndroidStore = defineStore('android', () => {
  // フィルタ選択肢
  const availableFilters = ref<api.AndroidFilters>({
    scenarios: [], device_ids: [], results: [], test_sites: [],
  })

  // ユーザー選択フィルタ
  const selected = ref<Record<string, string[]>>({
    scenarios: [], device_ids: [], results: [], test_sites: [],
  })

  // ダッシュボード設定
  const yieldGroupBy = ref('scenario')
  const trendFreq = ref('1D')

  // 結果データ
  const summary = ref<api.AndroidSummary | null>(null)
  const yieldData = ref<api.YieldItem[]>([])
  const trendData = ref<api.TrendData | null>(null)
  const results = ref<{ total: number; items: api.ResultItem[] }>({ total: 0, items: [] })
  const selectedDetail = ref<api.ResultDetail | null>(null)

  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadFilters() {
    try {
      availableFilters.value = await api.fetchFilters()
    } catch (e: any) {
      error.value = `フィルタ取得失敗: ${e.message}`
    }
  }

  async function refresh() {
    loading.value = true
    error.value = null
    try {
      const [s, y, t, r] = await Promise.all([
        api.fetchSummary(selected.value),
        api.fetchYield(yieldGroupBy.value, selected.value),
        api.fetchTrend(trendFreq.value, selected.value),
        api.fetchResults(selected.value),
      ])
      summary.value = s
      yieldData.value = y.items
      trendData.value = t
      results.value = r
    } catch (e: any) {
      error.value = `データ取得失敗: ${e.message}`
    } finally {
      loading.value = false
    }
  }

  async function loadDetail(runId: string) {
    try {
      selectedDetail.value = await api.fetchResultDetail(runId)
    } catch (e: any) {
      error.value = `詳細取得失敗: ${e.message}`
    }
  }

  async function init() {
    await loadFilters()
    await refresh()
  }

  return {
    availableFilters, selected,
    yieldGroupBy, trendFreq,
    summary, yieldData, trendData, results, selectedDetail,
    loading, error,
    init, refresh, loadDetail,
  }
})
