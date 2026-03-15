import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/analysis'
import type {
  AnalysisType,
  AnalysisResponse,
  StatisticsRequest,
  TimeseriesRequest,
  DistributionRequest,
  CorrelationRequest,
  GroupbyRequest,
} from '@/types'

export const useAnalysisStore = defineStore('analysis', () => {
  const currentType = ref<AnalysisType>('statistics')
  const result = ref<AnalysisResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function runAnalysis(
    type: AnalysisType,
    req: StatisticsRequest | TimeseriesRequest | DistributionRequest | CorrelationRequest | GroupbyRequest
  ) {
    loading.value = true
    error.value = null
    result.value = null
    currentType.value = type

    try {
      switch (type) {
        case 'statistics':
          result.value = await api.runStatistics(req as StatisticsRequest)
          break
        case 'timeseries':
          result.value = await api.runTimeseries(req as TimeseriesRequest)
          break
        case 'distribution':
          result.value = await api.runDistribution(req as DistributionRequest)
          break
        case 'correlation':
          result.value = await api.runCorrelation(req as CorrelationRequest)
          break
        case 'groupby':
          result.value = await api.runGroupby(req as GroupbyRequest)
          break
      }
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  return { currentType, result, loading, error, runAnalysis }
})
