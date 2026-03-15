<template>
  <el-form label-position="top" @submit.prevent="submit">

    <!-- 分析種別 -->
    <el-form-item label="分析種別">
      <el-select v-model="analysisType" style="width: 100%">
        <el-option value="statistics" label="基本統計" />
        <el-option value="timeseries" label="時系列" />
        <el-option value="distribution" label="分布（ヒストグラム）" />
        <el-option value="correlation" label="相関行列" />
        <el-option value="groupby" label="グループ集計" />
      </el-select>
    </el-form-item>

    <!-- 基本統計 -->
    <template v-if="analysisType === 'statistics'">
      <el-form-item label="対象カラム（複数可）">
        <el-select v-model="statsColumns" multiple style="width: 100%">
          <el-option v-for="c in columns" :key="c.name" :value="c.name" :label="`${c.name} (${c.type})`" />
        </el-select>
      </el-form-item>
    </template>

    <!-- 時系列 -->
    <template v-else-if="analysisType === 'timeseries'">
      <el-form-item label="時間カラム">
        <el-select v-model="tsTimeCol" style="width: 100%">
          <el-option v-for="c in columns" :key="c.name" :value="c.name" :label="`${c.name} (${c.type})`" />
        </el-select>
      </el-form-item>
      <el-form-item label="値カラム">
        <el-select v-model="tsValueCol" style="width: 100%">
          <el-option v-for="c in columns" :key="c.name" :value="c.name" :label="`${c.name} (${c.type})`" />
        </el-select>
      </el-form-item>
      <el-form-item label="集計関数">
        <el-select v-model="tsAggFunc" style="width: 100%">
          <el-option value="sum" label="合計 (sum)" />
          <el-option value="mean" label="平均 (mean)" />
          <el-option value="count" label="件数 (count)" />
        </el-select>
      </el-form-item>
      <el-form-item label="集計期間">
        <el-select v-model="tsFreq" style="width: 100%">
          <el-option value="1h" label="1時間" />
          <el-option value="1D" label="1日" />
          <el-option value="1W" label="1週間" />
          <el-option value="1ME" label="1ヶ月" />
        </el-select>
      </el-form-item>
    </template>

    <!-- 分布 -->
    <template v-else-if="analysisType === 'distribution'">
      <el-form-item label="対象カラム">
        <el-select v-model="distColumn" style="width: 100%">
          <el-option v-for="c in columns" :key="c.name" :value="c.name" :label="`${c.name} (${c.type})`" />
        </el-select>
      </el-form-item>
      <el-form-item label="ビン数">
        <el-input-number v-model="distBins" :min="2" :max="200" />
      </el-form-item>
    </template>

    <!-- 相関 -->
    <template v-else-if="analysisType === 'correlation'">
      <el-form-item label="対象カラム（2つ以上）">
        <el-select v-model="corrColumns" multiple style="width: 100%">
          <el-option v-for="c in columns" :key="c.name" :value="c.name" :label="`${c.name} (${c.type})`" />
        </el-select>
      </el-form-item>
      <el-form-item label="相関係数の種類">
        <el-select v-model="corrMethod" style="width: 100%">
          <el-option value="pearson" label="ピアソン (Pearson)" />
          <el-option value="spearman" label="スピアマン (Spearman)" />
        </el-select>
      </el-form-item>
    </template>

    <!-- グループ集計 -->
    <template v-else-if="analysisType === 'groupby'">
      <el-form-item label="グループカラム">
        <el-select v-model="gbGroupCols" multiple style="width: 100%">
          <el-option v-for="c in columns" :key="c.name" :value="c.name" :label="`${c.name} (${c.type})`" />
        </el-select>
      </el-form-item>
      <el-form-item label="集計カラム">
        <el-select v-model="gbAggCol" style="width: 100%">
          <el-option v-for="c in columns" :key="c.name" :value="c.name" :label="`${c.name} (${c.type})`" />
        </el-select>
      </el-form-item>
      <el-form-item label="集計関数">
        <el-select v-model="gbAggFunc" style="width: 100%">
          <el-option value="sum" label="合計 (sum)" />
          <el-option value="mean" label="平均 (mean)" />
          <el-option value="count" label="件数 (count)" />
          <el-option value="max" label="最大 (max)" />
          <el-option value="min" label="最小 (min)" />
        </el-select>
      </el-form-item>
      <el-form-item label="上位件数">
        <el-input-number v-model="gbLimit" :min="1" :max="5000" />
      </el-form-item>
    </template>

    <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%; margin-top: 8px">
      分析実行
    </el-button>
  </el-form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSchemaStore } from '@/stores/schemaStore'
import { useAnalysisStore } from '@/stores/analysisStore'
import { storeToRefs } from 'pinia'
import type { AnalysisType, FilterCondition } from '@/types'

const schemaStore = useSchemaStore()
const analysisStore = useAnalysisStore()
const { columns, selectedTable } = storeToRefs(schemaStore)
const { loading } = storeToRefs(analysisStore)

const analysisType = ref<AnalysisType>('statistics')

// statistics
const statsColumns = ref<string[]>([])

// timeseries
const tsTimeCol = ref('')
const tsValueCol = ref('')
const tsAggFunc = ref<'sum' | 'mean' | 'count'>('sum')
const tsFreq = ref('1D')

// distribution
const distColumn = ref('')
const distBins = ref(30)

// correlation
const corrColumns = ref<string[]>([])
const corrMethod = ref<'pearson' | 'spearman'>('pearson')

// groupby
const gbGroupCols = ref<string[]>([])
const gbAggCol = ref('')
const gbAggFunc = ref<'sum' | 'mean' | 'count' | 'max' | 'min'>('sum')
const gbLimit = ref(100)

function submit() {
  const table = selectedTable.value
  const filters: FilterCondition[] = []

  switch (analysisType.value) {
    case 'statistics':
      analysisStore.runAnalysis('statistics', { table, columns: statsColumns.value, filters })
      break
    case 'timeseries':
      analysisStore.runAnalysis('timeseries', {
        table, time_column: tsTimeCol.value, value_column: tsValueCol.value,
        agg_func: tsAggFunc.value, freq: tsFreq.value, filters,
      })
      break
    case 'distribution':
      analysisStore.runAnalysis('distribution', { table, column: distColumn.value, bins: distBins.value, filters })
      break
    case 'correlation':
      analysisStore.runAnalysis('correlation', { table, columns: corrColumns.value, method: corrMethod.value, filters })
      break
    case 'groupby':
      analysisStore.runAnalysis('groupby', {
        table, group_columns: gbGroupCols.value, agg_column: gbAggCol.value,
        agg_func: gbAggFunc.value, filters, limit: gbLimit.value,
      })
      break
  }
}
</script>
