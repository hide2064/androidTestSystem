// --- Schema types ---
export interface ColumnInfo {
  name: string
  type: string
  nullable: boolean
}

// --- Filter ---
export type FilterOp = 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in'

export interface FilterCondition {
  column: string
  op: FilterOp
  value: string | number | string[]
}

// --- Analysis types ---
export type AnalysisType = 'statistics' | 'timeseries' | 'distribution' | 'correlation' | 'groupby'

export interface StatisticsRequest {
  table: string
  columns: string[]
  filters: FilterCondition[]
}

export interface TimeseriesRequest {
  table: string
  time_column: string
  value_column: string
  agg_func: 'sum' | 'mean' | 'count'
  freq: string
  filters: FilterCondition[]
}

export interface DistributionRequest {
  table: string
  column: string
  bins: number
  filters: FilterCondition[]
}

export interface CorrelationRequest {
  table: string
  columns: string[]
  method: 'pearson' | 'spearman'
  filters: FilterCondition[]
}

export interface GroupbyRequest {
  table: string
  group_columns: string[]
  agg_column: string
  agg_func: 'sum' | 'mean' | 'count' | 'max' | 'min'
  filters: FilterCondition[]
  limit: number
}

// --- Analysis results ---
export interface AnalysisResponse {
  type: string
  data: unknown
}

export interface StatisticsData {
  [column: string]: {
    count: number
    mean?: number
    std?: number
    min?: number
    q25?: number
    median?: number
    q75?: number
    max?: number
    null_count: number
    unique?: number
    top_values?: Record<string, number>
  }
}

export interface TimeseriesData {
  labels: string[]
  series: { name: string; values: number[] }[]
}

export interface DistributionData {
  bin_edges: number[]
  bin_centers: number[]
  counts: number[]
  total: number
  null_count: number
}

export interface CorrelationData {
  columns: string[]
  matrix: number[][]
}

export interface GroupbyData {
  columns: string[]
  rows: (string | null)[][]
}
