<template>
  <el-card class="detect-control-panel">
    <template #header>
      <div class="card-header">
        <ArtSvgIcon icon="ri:settings-4-line" />
        <span>检测置信度</span>
      </div>
    </template>
    <div class="control-content">
      <el-slider v-model="localValue" :min="30" :max="90" show-stops />
      <div class="input-wrapper">
        <el-input-number v-model="localValue" :min="30" :max="90" :step="1" />
        <span class="unit">%</span>
      </div>
    </div>
    <el-text type="info" size="small">
      提示：置信度越高，检测结果越严谨（建议范围：50-80%）
    </el-text>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

  const props = defineProps<{
    modelValue: number
  }>()

  const emit = defineEmits<{
    'update:modelValue': [value: number]
  }>()

  const localValue = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
  })
</script>

<style scoped lang="scss">
  .detect-control-panel {
    .card-header {
      display: flex;
      gap: 8px;
      align-items: center;
      font-weight: bold;
    }

    .control-content {
      margin-bottom: 12px;

      .input-wrapper {
        display: flex;
        gap: 8px;
        align-items: center;
        justify-content: center;
        margin-top: 12px;

        .unit {
          color: var(--el-text-color-secondary);
        }
      }
    }
  }
</style>
