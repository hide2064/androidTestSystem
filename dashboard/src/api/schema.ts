import client from './client'
import type { ColumnInfo } from '@/types'

export async function fetchTables(): Promise<string[]> {
  const res = await client.get<{ tables: string[] }>('/tables')
  return res.data.tables
}

export async function fetchColumns(table: string): Promise<ColumnInfo[]> {
  const res = await client.get<{ table: string; columns: ColumnInfo[] }>(
    `/tables/${table}/columns`
  )
  return res.data.columns
}
