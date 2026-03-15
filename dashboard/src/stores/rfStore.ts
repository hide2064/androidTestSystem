import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/rf'
import type { RfFilters, SummaryData, YieldItem, DistributionStat, DistributionRaw, TrendData, MarginPoint } from '@/api/rf'

export const useRfStore = defineStore('rf', () => {
  // --- 選択肢 ---
  const availableFilters = ref<RfFilters>({
    DUT_Model: [], Technology: [], Band: [], Test_Item: [],
    Temperature_C: [], Supply_Voltage_V: [], Judgment: [],
    Operator_ID: [], Channel_Position: [],
  })

  // --- 選択中フィルタ (スライサー) ---
  const selected = ref<Record<string, string[]>>({
    dut_models:   [],
    technologies: [],
    bands:        [],
    test_items:   [],
    temperatures: [],
    voltages:     [],
    judgments:    [],
    operators:    [],
  })

  // ダッシュボード設定
  const yieldGroupBy = ref('Test_Item')
  const distTestItem = ref('')
  const distGroupBy  = ref('DUT_Model')
  const trendFreq    = ref('1D')
  const trendMetric  = ref('yield')
  const marginXAxis  = ref('Temperature_C')

  // --- 結果データ ---
  const summary    = ref<SummaryData | null>(null)
  const yieldData  = ref<YieldItem[]>([])
  const distStats  = ref<DistributionStat[]>([])
  const distRaw    = ref<DistributionRaw[]>([])
  const trendData  = ref<TrendData | null>(null)
  const marginData = ref<MarginPoint[]>([])

  const loading = ref(false)
  const error   = ref<string | null>(null)

  // --- activeTestItem: distTestItem が未設定なら最初のTest_Itemを使う ---
  const activeTestItem = computed(() =>
    distTestItem.value || availableFilters.value.Test_Item[0] || ''
  )

  async function loadFilters() {
    try {
      availableFilters.value = await api.fetchFilters()
      if (!distTestItem.value && availableFilters.value.Test_Item.length > 0) {
        distTestItem.value = availableFilters.value.Test_Item[0]
      }
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  async function refresh() {
    loading.value = true
    error.value = null
    const f = selected.value

    try {
      const [sum, yld, dist, trend, margin] = await Promise.all([
        api.fetchSummary(f),
        api.fetchYield(yieldGroupBy.value, f),
        activeTestItem.value
          ? api.fetchDistribution(activeTestItem.value, distGroupBy.value, f)
          : null,
        activeTestItem.value
          ? api.fetchTrend(activeTestItem.value, trendFreq.value, trendMetric.value, f)
          : null,
        activeTestItem.value
          ? api.fetchMargin(activeTestItem.value, marginXAxis.value, f)
          : null,
      ])

      summary.value    = sum
      yieldData.value  = yld.items
      distStats.value  = dist?.stats ?? []
      distRaw.value    = dist?.raw ?? []
      trendData.value  = trend ?? null
      marginData.value = margin?.points ?? []
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  return {
    availableFilters, selected,
    yieldGroupBy, distTestItem, distGroupBy, trendFreq, trendMetric, marginXAxis,
    activeTestItem,
    summary, yieldData, distStats, distRaw, trendData, marginData,
    loading, error,
    loadFilters, refresh,
  }
})
