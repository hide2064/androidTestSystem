import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchTables, fetchColumns } from '@/api/schema'
import type { ColumnInfo } from '@/types'

export const useSchemaStore = defineStore('schema', () => {
  const tables = ref<string[]>([])
  const columns = ref<ColumnInfo[]>([])
  const selectedTable = ref<string>('')
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadTables() {
    loading.value = true
    error.value = null
    try {
      tables.value = await fetchTables()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function selectTable(table: string) {
    selectedTable.value = table
    columns.value = []
    loading.value = true
    error.value = null
    try {
      columns.value = await fetchColumns(table)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  return { tables, columns, selectedTable, loading, error, loadTables, selectTable }
})
