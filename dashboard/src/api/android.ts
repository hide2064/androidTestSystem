import axios from 'axios'

const client = axios.create({ baseURL: '/api/analysis' })

export interface AndroidFilters {
  scenarios: string[]
  device_ids: string[]
  results: string[]
  test_sites: string[]
}

export interface AndroidSummary {
  total: number
  pass_count: number
  fail_count: number
  yield_pct: number
}

export interface YieldItem {
  label: string
  pass_count: number
  fail_count: number
  total: number
  yield_pct: number
}

export interface TrendData {
  metric: string
  unit: string
  labels: string[]
  values: number[]
}

export interface ResultItem {
  run_id: string
  scenario: string
  device_id: string
  device_model: string | null
  test_site: string
  result: string
  total: number
  pass_count: number
  fail_count: number
  started_at: string | null
  finished_at: string | null
}

export interface ResultDetail extends ResultItem {
  note: string | null
  steps: {
    step_id: number
    action: string
    description: string | null
    response: string | null
    measured_value: number | null
    unit: string | null
    upper_limit: number | null
    lower_limit: number | null
    pass: boolean
    error_msg: string | null
    executed_at: string | null
  }[]
}

function buildParams(filters: Record<string, string[]>, extra?: Record<string, string>): URLSearchParams {
  const p = new URLSearchParams()
  for (const [key, vals] of Object.entries(filters)) {
    for (const v of vals) p.append(key, v)
  }
  if (extra) {
    for (const [k, v] of Object.entries(extra)) if (v) p.append(k, v)
  }
  return p
}

export async function fetchFilters(): Promise<AndroidFilters> {
  const res = await client.get('/api/v1/android/filters')
  return res.data
}

export async function fetchSummary(
  filters: Record<string, string[]>,
  dateFrom?: string,
  dateTo?: string,
): Promise<AndroidSummary> {
  const p = buildParams(filters, { date_from: dateFrom || '', date_to: dateTo || '' })
  const res = await client.get('/api/v1/android/summary', { params: p })
  return res.data
}

export async function fetchYield(
  groupBy: string,
  filters: Record<string, string[]>,
): Promise<{ group_by: string; items: YieldItem[] }> {
  const p = buildParams(filters, { group_by: groupBy })
  const res = await client.get('/api/v1/android/yield', { params: p })
  return res.data
}

export async function fetchTrend(
  freq: string,
  filters: Record<string, string[]>,
): Promise<TrendData> {
  const p = buildParams(filters, { freq })
  const res = await client.get('/api/v1/android/trend', { params: p })
  return res.data
}

export async function fetchResults(
  filters: Record<string, string[]>,
  limit = 50,
  offset = 0,
): Promise<{ total: number; items: ResultItem[] }> {
  const p = buildParams(filters, { limit: String(limit), offset: String(offset) })
  const res = await client.get('/api/v1/android/results', { params: p })
  return res.data
}

export async function fetchResultDetail(runId: string): Promise<ResultDetail> {
  const res = await client.get(`/api/v1/android/results/${runId}`)
  return res.data
}
