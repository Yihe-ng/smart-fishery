<template>
  <div class="production-page page-container">
    <el-row :gutter="20" class="mb-5">
      <el-col v-for="kpi in kpis" :key="kpi.label" :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="flex-cb">
            <div class="icon-box" :style="{ color: kpi.color, backgroundColor: kpi.color + '15' }">
              <ArtSvgIcon :icon="kpi.icon" />
            </div>
            <div class="text-right">
              <div class="text-xs text-[var(--el-text-color-regular)]">{{ kpi.label }}</div>
              <div class="text-xl font-bold text-[var(--el-text-color-primary)]"
                >{{ kpi.value }}{{ kpi.unit }}</div
              >
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-[var(--art-border-color)] flex-cb text-xs">
            <span class="text-[var(--el-text-color-secondary)]">环比昨日</span>
            <span :class="kpi.trend > 0 ? 'text-green-500' : 'text-red-500'">
              {{ kpi.trend > 0 ? '+' : '' }}{{ kpi.trend }}%
              <ArtSvgIcon
                :icon="kpi.trend > 0 ? 'ri:arrow-right-up-line' : 'ri:arrow-right-down-line'"
              />
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="never" class="mb-5">
          <template #header>
            <span class="font-bold">生长趋势分析</span>
          </template>
          <div
            class="h-80 flex-center bg-[var(--default-box-color)] border border-[var(--art-border-color)] rounded"
          >
            <el-empty description="生长曲线图表加载中..." />
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <span class="font-bold">投喂转化率 (FCR) 记录</span>
          </template>
          <el-table :data="fcrData" border>
            <el-table-column prop="date" label="统计日期" width="150" />
            <el-table-column prop="fishWeight" label="平均体重 (g)" align="center" />
            <el-table-column prop="feedTotal" label="累计投喂 (kg)" align="center" />
            <el-table-column prop="fcr" label="当前FCR" align="center">
              <template #default="{ row }">
                <el-tag :type="row.fcr < 1.6 ? 'success' : 'warning'" size="small">{{
                  row.fcr
                }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="mb-5">
          <template #header>
            <span class="font-bold">规格分布预估</span>
          </template>
          <div
            class="h-64 flex-center bg-[var(--default-box-color)] border border-[var(--art-border-color)] rounded"
          >
            <el-empty description="规格分布饼图加载中..." />
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <span class="font-bold">最近盘点记录</span>
          </template>
          <el-timeline>
            <el-timeline-item timestamp="2024-03-15" type="primary">
              <p class="text-sm font-bold text-g-900">常规盘点</p>
              <p class="text-xs text-g-500">存栏: 12,500尾, 均重: 450g</p>
            </el-timeline-item>
            <el-timeline-item timestamp="2024-02-15">
              <p class="text-sm font-bold text-g-900">常规盘点</p>
              <p class="text-xs text-g-500">存栏: 12,550尾, 均重: 380g</p>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

  const kpis = ref([
    {
      label: '预估存栏',
      value: '12,500',
      unit: '尾',
      icon: 'ri:group-line',
      color: 'var(--art-info)',
      trend: -0.2
    },
    {
      label: '平均体重',
      value: '450',
      unit: 'g',
      icon: 'ri:scales-line',
      color: 'var(--art-success)',
      trend: 1.5
    },
    {
      label: '今日死亡',
      value: '2',
      unit: '尾',
      icon: 'ri:alarm-warning-line',
      color: 'var(--art-danger)',
      trend: -50
    },
    {
      label: '投喂总量',
      value: '1,600',
      unit: 'g',
      icon: 'ri:restaurant-line',
      color: 'var(--art-warning)',
      trend: 5.2
    }
  ])

  const fcrData = ref([
    { date: '2024-03-20', fishWeight: 450, feedTotal: 125.5, fcr: 1.55 },
    { date: '2024-03-13', fishWeight: 435, feedTotal: 118.2, fcr: 1.58 },
    { date: '2024-03-06', fishWeight: 420, feedTotal: 112.4, fcr: 1.62 }
  ])
</script>

<style scoped lang="scss">
  .production-page {
    padding: 20px;
    background-color: var(--default-bg-color);

    .kpi-card {
      border: 1px solid var(--art-border-color);

      .icon-box {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        font-size: 22px;
        border-radius: 10px;
      }
    }
  }
</style>
