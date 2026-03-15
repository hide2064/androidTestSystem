import client from './client'
import type {
  AnalysisResponse,
  StatisticsRequest,
  TimeseriesRequest,
  DistributionRequest,
  CorrelationRequest,
  GroupbyRequest,
} from '@/types'

export async function runStatistics(req: StatisticsRequest): Promise<AnalysisResponse> {
  const res = await client.post<AnalysisResponse>('/analysis/statistics', req)
  return res.data
}

export async function runTimeseries(req: TimeseriesRequest): Promise<AnalysisResponse> {
  const res = await client.post<AnalysisResponse>('/analysis/timeseries', req)
  return res.data
}

export async function runDistribution(req: DistributionRequest): Promise<AnalysisResponse> {
  const res = await client.post<AnalysisResponse>('/analysis/distribution', req)
  return res.data
}

export async function runCorrelation(req: CorrelationRequest): Promise<AnalysisResponse> {
  const res = await client.post<AnalysisResponse>('/analysis/correlation', req)
  return res.data
}

export async function runGroupby(req: GroupbyRequest): Promise<AnalysisResponse> {
  const res = await client.post<AnalysisResponse>('/analysis/groupby', req)
  return res.data
}
