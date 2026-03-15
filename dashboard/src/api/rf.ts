import client from './client'

export interface RfFilters {
  DUT_Model: string[]
  Technology: string[]
  Band: string[]
  Test_Item: string[]
  Temperature_C: string[]
  Supply_Voltage_V: string[]
  Judgment: string[]
  Operator_ID: string[]
  Channel_Position: string[]
}

export interface SummaryData {
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

export interface DistributionStat {
  group: string
  min: number | null
  max: number | null
  avg: number | null
  std: number | null
  count: number
  upper_limit: number | null
  lower_limit: number | null
  unit: string
}

export interface DistributionRaw {
  group: string
  value: number
  judgment: string
}

export interface TrendData {
  test_item: string
  metric: string
  unit: string
  labels: string[]
  values: number[]
}

export interface MarginPoint {
  x: number
  measured: number
  upper_limit: number | null
  lower_limit: number | null
  margin_upper: number | null
  margin_lower: number | null
  judgment: string
  dut_model: string
}

// フィルタをクエリパラメータ配列に変換
function buildParams(filters: Record<string, string[]>, extra?: Record<string, string>): URLSearchParams {
  const p = new URLSearchParams()
  for (const [key, vals] of Object.entries(filters)) {
    for (const v of vals) p.append(key, v)
  }
  if (extra) {
    for (const [key, val] of Object.entries(extra)) p.append(key, val)
  }
  return p
}

export async function fetchFilters(): Promise<RfFilters> {
  const res = await client.get<RfFilters>('/rf/filters')
  return res.data
}

export async function fetchSummary(filters: Record<string, string[]>): Promise<SummaryData> {
  const res = await client.get<SummaryData>('/rf/summary', { params: buildParams(filters) })
  return res.data
}

export async function fetchYield(
  groupBy: string,
  filters: Record<string, string[]>
): Promise<{ group_by: string; items: YieldItem[] }> {
  const p = buildParams(filters, { group_by: groupBy })
  const res = await client.get('/rf/yield', { params: p })
  return res.data
}

export async function fetchDistribution(
  testItem: string,
  groupBy: string,
  filters: Record<string, string[]>
): Promise<{ test_item: string; group_by: string; stats: DistributionStat[]; raw: DistributionRaw[] }> {
  const p = buildParams(filters, { test_item: testItem, group_by: groupBy })
  const res = await client.get('/rf/distribution', { params: p })
  return res.data
}

export async function fetchTrend(
  testItem: string,
  freq: string,
  metric: string,
  filters: Record<string, string[]>
): Promise<TrendData> {
  const p = buildParams(filters, { test_item: testItem, freq, metric })
  const res = await client.get<TrendData>('/rf/trend', { params: p })
  return res.data
}

export async function fetchMargin(
  testItem: string,
  xAxis: string,
  filters: Record<string, string[]>
): Promise<{ test_item: string; x_axis: string; points: MarginPoint[] }> {
  const p = buildParams(filters, { test_item: testItem, x_axis: xAxis })
  const res = await client.get('/rf/margin', { params: p })
  return res.data
}
