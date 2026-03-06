<template>
  <el-card shadow="never" class="feeding-panel">
    <template #header>
      <div class="flex-cb">
        <span class="font-bold">精准投喂控制</span>
        <el-button type="primary" size="small">
          <template #icon>
            <ArtSvgIcon icon="ri:hand-coin-line" />
          </template>
          手动投喂
        </el-button>
      </div>
    </template>

    <div class="p-4">
      <el-tabs v-model="activeTab">
        <el-tab-pane name="config">
          <template #label>
            <div class="flex-c gap-1"><ArtSvgIcon icon="ri:settings-4-line" />参数配置</div>
          </template>
          <el-form :model="config" label-width="80px" size="small">
            <el-form-item label="饲料系数">
              <el-slider
                v-model="config.feedCoefficient"
                :min="1.4"
                :max="1.8"
                :step="0.1"
                show-input
              />
            </el-form-item>
            <el-form-item label="投喂频次">
              <el-input-number v-model="config.frequency" :min="1" :max="10" />
              <span class="ml-2 text-[var(--el-text-color-regular)]">次/日</span>
            </el-form-item>
            <el-form-item label="饲料粒径">
              <el-select v-model="config.feedSize" placeholder="选择粒径">
                <el-option label="1.0mm" value="1.0mm" />
                <el-option label="1.5mm" value="1.5mm" />
                <el-option label="2.0mm" value="2.0mm" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" class="w-full">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane name="logs">
          <template #label>
            <div class="flex-c gap-1"><ArtSvgIcon icon="ri:history-line" />投喂日志</div>
          </template>
          <el-timeline class="mt-4 px-4">
            <el-timeline-item
              v-for="log in logs"
              :key="log.id"
              :timestamp="log.feedTime"
              :type="log.status === 'completed' ? 'success' : 'warning'"
            >
              <div class="flex-cb">
                <span class="text-[var(--el-text-color-primary)]"
                  >{{ log.amount }}g ({{ log.triggerType === 'auto' ? '自动' : '手动' }})</span
                >
                <el-tag :type="log.status === 'completed' ? 'success' : 'info'" size="small">
                  {{ log.status === 'completed' ? '已完成' : '执行中' }}
                </el-tag>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>
      </el-tabs>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { ref, reactive } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { FeedingConfig, FeedingLog } from '@/types/feeding'

  const activeTab = ref('config')

  const config = reactive<FeedingConfig>({
    feedCoefficient: 1.6,
    frequency: 3,
    feedSize: '2.0mm'
  })

  const logs = ref<FeedingLog[]>([
    { id: '1', feedTime: '08:00', amount: 500, status: 'completed', triggerType: 'auto' },
    { id: '2', feedTime: '12:00', amount: 500, status: 'completed', triggerType: 'auto' },
    { id: '3', feedTime: '18:00', amount: 600, status: 'pending', triggerType: 'manual' }
  ])
</script>

<style scoped lang="scss">
  .feeding-panel {
    border: 1px solid var(--art-border-color);

    :deep(.el-card__body) {
      padding: 0;
    }
  }
</style>
