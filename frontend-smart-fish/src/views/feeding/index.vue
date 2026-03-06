<template>
  <div class="feeding-page page-container">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="8">
        <el-card shadow="never" class="mb-5">
          <template #header>
            <div class="flex-cb">
              <span class="font-bold">投喂参数配置</span>
              <ArtSvgIcon icon="ri:settings-4-line" class="text-blue-500" />
            </div>
          </template>
          <el-form :model="config" label-position="top">
            <el-form-item label="饲料系数 (Feed Coefficient)">
              <el-slider
                v-model="config.feedCoefficient"
                :min="1.4"
                :max="1.8"
                :step="0.1"
                show-input
              />
              <p class="text-xs text-[var(--el-text-color-secondary)] mt-1"
                >根据鱼体大小和水温自动建议或手动调整</p
              >
            </el-form-item>
            <el-form-item label="投喂频次 (Frequency)">
              <el-input-number v-model="config.frequency" :min="1" :max="8" class="w-full" />
            </el-form-item>
            <el-form-item label="饲料粒径 (Feed Size)">
              <el-select v-model="config.feedSize" class="w-full">
                <el-option label="1.0mm (幼鱼)" value="1.0mm" />
                <el-option label="1.5mm (中鱼)" value="1.5mm" />
                <el-option label="2.0mm (成鱼)" value="2.0mm" />
              </el-select>
            </el-form-item>
            <el-form-item label="模糊PID权重预留">
              <el-switch v-model="pidEnabled" active-text="开启自动优化" />
            </el-form-item>
            <div class="mt-6">
              <el-button type="primary" class="w-full" @click="saveConfig">保存并应用</el-button>
            </div>
          </el-form>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <span class="font-bold">快速投喂</span>
          </template>
          <div class="text-center py-4">
            <el-input-number v-model="manualAmount" :min="100" :step="100" class="mb-4 w-full" />
            <el-button
              type="success"
              size="large"
              class="w-full"
              icon="ri:hand-coin-line"
              @click="handleManualFeed"
            >
              立即投喂 ({{ manualAmount }}g)
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="16">
        <el-card shadow="never">
          <template #header>
            <div class="flex-cb">
              <span class="font-bold">投喂执行日志</span>
              <el-button link type="primary">清除日志</el-button>
            </div>
          </template>
          <el-table :data="logs" border>
            <el-table-column prop="feedTime" label="投喂时间" width="180" />
            <el-table-column prop="amount" label="投喂量 (g)" align="center" />
            <el-table-column prop="triggerType" label="触发方式" align="center">
              <template #default="{ row }">
                <el-tag :type="row.triggerType === 'auto' ? 'primary' : 'info'" size="small">
                  {{ row.triggerType === 'auto' ? '自动' : '手动' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                  {{ row.status === 'completed' ? '已完成' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="mt-4 flex justify-end">
            <el-pagination layout="prev, pager, next" :total="total" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import {
    getFeedingConfig,
    updateFeedingConfig,
    getFeedingLogs,
    manualFeeding
  } from '@/api/feeding'
  import type { FeedingConfig, FeedingLog } from '@/types/feeding'
  import { ElMessage } from 'element-plus'

  const config = reactive<FeedingConfig>({
    feedCoefficient: 1.6,
    frequency: 3,
    feedSize: '2.0mm'
  })
  const pidEnabled = ref(true)
  const manualAmount = ref(500)
  const logs = ref<FeedingLog[]>([])
  const total = ref(0)

  const loadData = async () => {
    try {
      const [cfg, logRes] = await Promise.all([
        getFeedingConfig(),
        getFeedingLogs({ current: 1, size: 10 })
      ])
      Object.assign(config, cfg)
      logs.value = logRes.list
      total.value = logRes.total
    } catch (error) {
      console.error('Failed to load feeding data:', error)
    }
  }

  const saveConfig = async () => {
    try {
      await updateFeedingConfig(config)
      ElMessage.success('配置已保存并同步至设备')
    } catch (error) {
      console.error('Failed to save config:', error)
      ElMessage.error('配置保存失败')
    }
  }

  const handleManualFeed = async () => {
    try {
      await manualFeeding(manualAmount.value)
      ElMessage.success(`手动投喂指令已发送: ${manualAmount.value}g`)
      loadData()
    } catch (error) {
      console.error('Failed to send feeding command:', error)
      ElMessage.error('指令发送失败')
    }
  }

  onMounted(loadData)
</script>

<style scoped lang="scss">
  .feeding-page {
    padding: 20px;
  }
</style>
