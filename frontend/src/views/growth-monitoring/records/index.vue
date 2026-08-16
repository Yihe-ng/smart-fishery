<template>
  <div class="page-container growth-records-page">
    <el-card shadow="never">
      <template #header>
        <div class="flex-cb">
          <div class="flex-c gap-2">
            <ArtSvgIcon icon="ri:file-list-3-line" class="text-theme" />
            <span class="font-bold">生长识别记录</span>
          </div>
          <el-button size="small" @click="goDetect">
            <template #icon>
              <ArtSvgIcon icon="ri:scales-3-line" />
            </template>
            去识别
          </el-button>
        </div>
      </template>

      <div class="mb-4">
        <ArtSearchBar
          :model-value="searchQuery"
          :items="searchItems"
          :show-expand="false"
          @update:model-value="handleSearchModelUpdate"
          @search="handleSearch"
          @reset="handleReset"
        />
      </div>

      <el-table v-loading="loading" :data="tableData" border style="width: 100%">
        <el-table-column label="识别时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.recognizedAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="pondId" label="池塘" align="center" min-width="90" />
        <el-table-column label="来源" align="center" min-width="100">
          <template #default="{ row }">
            <el-tag :type="row.sourceType === 'video' ? 'primary' : 'success'" size="small">
              {{ row.sourceType === 'video' ? '视频识别' : '图片识别' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="样本数 (尾)" align="center" min-width="110">
          <template #default="{ row }">{{ row.measurableCount }}</template>
        </el-table-column>
        <el-table-column label="月龄" align="center" min-width="90">
          <template #default="{ row }">
            {{ row.cultureMonth ? `第 ${row.cultureMonth} 月` : '未选择' }}
          </template>
        </el-table-column>
        <el-table-column label="投苗原长 (cm)" align="center" min-width="120">
          <template #default="{ row }">{{ formatNumber(row.stockingAvgLengthCm) }}</template>
        </el-table-column>
        <el-table-column label="平均全长 (cm)" align="center" min-width="120">
          <template #default="{ row }">{{ formatNumber(row.avgBodyLengthCm) }}</template>
        </el-table-column>
        <el-table-column label="平均体重 (g)" align="center" min-width="110">
          <template #default="{ row }">{{ formatNumber(row.avgWeightG) }}</template>
        </el-table-column>
        <el-table-column label="群体状态" align="center" min-width="100">
          <template #default="{ row }">
            <el-tag :type="getGrowthCohortTagType(row.cohortStatus)" size="small">
              {{ cohortLabel(row.cohortStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" align="center" width="220">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDetail(row)">详情</el-button>
            <el-button type="primary" link size="small" @click="goFeeding">投喂建议</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 记录详情抽屉 -->
    <el-drawer v-model="detailVisible" title="识别记录详情" size="420px">
      <el-descriptions v-if="detailRecord" :column="1" border>
        <el-descriptions-item label="识别时间">
          {{ formatDateTime(detailRecord.recognizedAt) }}
        </el-descriptions-item>
        <el-descriptions-item label="池塘">{{ detailRecord.pondId }}</el-descriptions-item>
        <el-descriptions-item label="来源">
          {{ detailRecord.sourceType === 'video' ? '视频识别' : '图片识别' }}
        </el-descriptions-item>
        <el-descriptions-item label="样本数（可测尾数）">
          {{ detailRecord.measurableCount }} 尾
        </el-descriptions-item>
        <el-descriptions-item label="养殖月龄">
          {{ detailRecord.cultureMonth ? `第 ${detailRecord.cultureMonth} 月` : '未选择' }}
        </el-descriptions-item>
        <el-descriptions-item label="投苗原长">
          {{ formatNumber(detailRecord.stockingAvgLengthCm) }} cm
        </el-descriptions-item>
        <el-descriptions-item label="平均全长">
          {{ formatNumber(detailRecord.avgBodyLengthCm) }} cm
        </el-descriptions-item>
        <el-descriptions-item label="平均体重">
          {{ formatNumber(detailRecord.avgWeightG) }} g
        </el-descriptions-item>
        <el-descriptions-item label="群体状态">
          <el-tag :type="getGrowthCohortTagType(detailRecord.cohortStatus)" size="small">
            {{ cohortLabel(detailRecord.cohortStatus) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态说明">
          {{ detailRecord.cohortStatus ? GROWTH_COHORT_STATUS_TEXT[detailRecord.cohortStatus] : '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="管理建议">
          {{ detailRecord.advice || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="落库时间">
          {{ formatDateTime(detailRecord.createdAt) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(detailRecord.updatedAt) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
  import { onActivated, onMounted, reactive, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import ArtSearchBar from '@/components/core/forms/art-search-bar/index.vue'
  import { deleteGrowthRecord, getGrowthRecords } from '@/api/growth-monitoring/records'
  import type { SearchFormItem } from '@/components/core/forms/art-search-bar/index.vue'
  import type {
    GrowthCohortStatus,
    GrowthRecordItem,
    GrowthRecordSourceType
  } from '@/types/growth-monitoring'
  import {
    GROWTH_COHORT_STATUS_LABEL,
    GROWTH_COHORT_STATUS_TEXT,
    getGrowthCohortTagType
  } from '@/views/growth-monitoring/detect/constants/statusColors'

  defineOptions({ name: 'GrowthRecords' })

  const router = useRouter()

  const loading = ref(false)
  const tableData = ref<GrowthRecordItem[]>([])
  const currentPage = ref(1)
  const pageSize = ref(10)
  const total = ref(0)

  // KeepAlive 缓存下首次激活会同时触发 onMounted 与 onActivated，用该标记避免重复加载
  let isFirstActivation = true

  const searchQuery = reactive({
    pondId: '',
    sourceType: '' as GrowthRecordSourceType | '',
    dateRange: [] as string[]
  })

  const handleSearchModelUpdate = (value: Partial<typeof searchQuery>) => {
    Object.assign(searchQuery, value)
  }

  const searchItems: SearchFormItem[] = [
    {
      label: '池塘',
      key: 'pondId',
      type: 'input',
      props: { placeholder: '请输入池塘编号', clearable: true }
    },
    {
      label: '来源',
      key: 'sourceType',
      type: 'select',
      props: {
        placeholder: '请选择来源',
        clearable: true,
        options: [
          { label: '图片识别', value: 'image' },
          { label: '视频识别', value: 'video' }
        ]
      }
    },
    {
      label: '识别时间',
      key: 'dateRange',
      type: 'daterange',
      props: {
        rangeSeparator: '至',
        startPlaceholder: '开始日期',
        endPlaceholder: '结束日期',
        valueFormat: 'YYYY-MM-DD'
      },
      span: 12
    }
  ]

  /** 详情抽屉 */
  const detailVisible = ref(false)
  const detailRecord = ref<GrowthRecordItem | null>(null)

  const formatDateTime = (value: string | null | undefined): string => {
    if (!value) return '--'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatNumber = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '--'
    return String(value)
  }

  const toUtcBoundary = (value: string, endOfDay: boolean): string => {
    const suffix = endOfDay ? 'T23:59:59.999' : 'T00:00:00'
    return new Date(`${value}${suffix}`).toISOString()
  }

  const cohortLabel = (status: GrowthCohortStatus | null | undefined): string => {
    return status ? GROWTH_COHORT_STATUS_LABEL[status] : '未评估'
  }

  const loadData = async () => {
    loading.value = true
    try {
      const res = await getGrowthRecords({
        pageNum: currentPage.value,
        pageSize: pageSize.value,
        pondId: searchQuery.pondId || undefined,
        sourceType: searchQuery.sourceType || undefined,
        startTime:
          searchQuery.dateRange.length === 2
            ? toUtcBoundary(searchQuery.dateRange[0], false)
            : undefined,
        endTime:
          searchQuery.dateRange.length === 2
            ? toUtcBoundary(searchQuery.dateRange[1], true)
            : undefined
      })
      total.value = res.total
      tableData.value = res.list
    } finally {
      loading.value = false
    }
  }

  const handleSearch = () => {
    currentPage.value = 1
    loadData()
  }

  const handleReset = () => {
    searchQuery.pondId = ''
    searchQuery.sourceType = ''
    searchQuery.dateRange = []
    currentPage.value = 1
    loadData()
  }

  const handleSizeChange = (value: number) => {
    pageSize.value = value
    loadData()
  }

  const handleCurrentChange = (value: number) => {
    currentPage.value = value
    loadData()
  }

  const openDetail = (row: GrowthRecordItem) => {
    detailRecord.value = row
    detailVisible.value = true
  }

  const handleDelete = async (row: GrowthRecordItem) => {
    try {
      await ElMessageBox.confirm('确定要删除该识别记录吗？删除后无法恢复', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
    } catch {
      return
    }

    await deleteGrowthRecord(row.id)
    ElMessage.success('删除成功')
    // 当前页删空时回退一页，避免停在空页
    if (tableData.value.length === 1 && currentPage.value > 1) {
      currentPage.value -= 1
    }
    loadData()
  }

  /** 联动：跳转生长识别页继续识别 */
  const goDetect = () => {
    router.push('/fishery/growth')
  }

  /** 联动：跳转精准投喂页查看投喂建议 */
  const goFeeding = () => {
    router.push('/fishery/feeding')
  }

  onMounted(() => {
    loadData()
  })

  onActivated(() => {
    // 页面被 KeepAlive 缓存，从标签页切回时不会重新挂载（onMounted 不触发）。
    // 首次激活已由 onMounted 加载，之后每次切回都重新拉取，保证新识别记录立即可见。
    if (isFirstActivation) {
      isFirstActivation = false
      return
    }
    loadData()
  })
</script>

<style scoped lang="scss">
  .growth-records-page {
    padding: 20px;
  }
</style>
