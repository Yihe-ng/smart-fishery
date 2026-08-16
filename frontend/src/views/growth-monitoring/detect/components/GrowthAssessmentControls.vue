<template>
  <el-card class="growth-assessment-controls" shadow="never">
    <div class="controls-row">
      <div class="control-field" :class="{ 'is-error': Boolean(errors.cultureMonth), 'is-flash': flashing }">
        <label class="field-label" for="growth-culture-month">养殖月数（从投苗日起）</label>
        <el-select
          id="growth-culture-month"
          ref="monthSelectRef"
          :model-value="cultureMonth"
          class="field-control"
          placeholder="请选择养殖月数"
          :disabled="disabled"
          @update:model-value="handleMonthChange"
        >
          <el-option v-for="month in MONTH_OPTIONS" :key="month" :label="`第 ${month} 个月`" :value="month" />
          <el-option label="不清楚，仅测量体长" :value="UNKNOWN_CULTURE_MONTH" />
        </el-select>
        <p v-if="errors.cultureMonth" class="field-error">{{ errors.cultureMonth }}</p>
      </div>

      <div
        class="control-field"
        :class="{ 'is-error': Boolean(errors.stockingAvgLengthCm), 'is-flash': flashing }"
      >
        <label class="field-label" for="growth-stocking-length">投苗时平均全长（cm）</label>
        <el-input-number
          id="growth-stocking-length"
          ref="lengthInputRef"
          :model-value="stockingAvgLengthCm ?? undefined"
          class="field-control"
          :min="MIN_STOCKING_LENGTH_CM"
          :max="MAX_STOCKING_LENGTH_CM"
          :step="0.1"
          :precision="1"
          :controls="false"
          placeholder="如 13.0"
          :disabled="disabled || isUnknownMonth"
          @update:model-value="handleLengthChange"
          @blur="emit('commitLength')"
          @keyup.enter="emit('commitLength')"
        />
        <p v-if="errors.stockingAvgLengthCm" class="field-error">
          {{ errors.stockingAvgLengthCm }}
        </p>
        <p v-else-if="isUnknownMonth" class="field-hint">已选择“不清楚”，本次只测量体长</p>
      </div>
    </div>

    <p v-if="referencePreview" class="reference-preview">{{ referencePreview }}</p>
  </el-card>
</template>

<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import {
    MAX_STOCKING_LENGTH_CM,
    MIN_STOCKING_LENGTH_CM,
    MONTH_OPTIONS,
    UNKNOWN_CULTURE_MONTH,
    type CultureMonthSelection,
    type GrowthAssessmentErrors
  } from '../constants/assessmentParams'

  defineOptions({ name: 'GrowthAssessmentControls' })

  const props = withDefaults(
    defineProps<{
      cultureMonth: CultureMonthSelection
      stockingAvgLengthCm: number | null
      /** 上传前的参考范围预览文案，由父级依据后端评价结果生成 */
      referencePreview?: string
      errors?: GrowthAssessmentErrors
      disabled?: boolean
    }>(),
    {
      referencePreview: '',
      errors: () => ({}),
      disabled: false
    }
  )

  const emit = defineEmits<{
    'update:cultureMonth': [value: CultureMonthSelection]
    'update:stockingAvgLengthCm': [value: number | null]
    /** 投苗体长输入失焦或按下回车，父级据此触发轻量重评 */
    commitLength: []
    clearErrors: []
  }>()

  const monthSelectRef = ref<{ focus: () => void }>()
  const lengthInputRef = ref<{ focus: () => void }>()
  const flashing = ref(false)
  let flashTimer: ReturnType<typeof setTimeout> | null = null

  const isUnknownMonth = computed(() => props.cultureMonth === UNKNOWN_CULTURE_MONTH)

  const handleMonthChange = (value: CultureMonthSelection) => {
    emit('update:cultureMonth', value)
    emit('clearErrors')
  }

  const handleLengthChange = (value: number | undefined) => {
    emit('update:stockingAvgLengthCm', typeof value === 'number' ? value : null)
    emit('clearErrors')
  }

  /** 聚焦第一个错误字段，配合上传拦截使用；月份错误优先于投苗体长 */
  const focusFirstError = () => {
    if (props.errors.cultureMonth) {
      monthSelectRef.value?.focus()
      return
    }
    if (props.errors.stockingAvgLengthCm) {
      lengthInputRef.value?.focus()
    }
  }

  /**
   * 触发一次“闪烁两次”的错误提示动画。
   * 动画只是补充信号，红色错误文案始终独立存在，避免只靠动画表达错误。
   */
  const flashErrors = () => {
    if (flashTimer) clearTimeout(flashTimer)
    flashing.value = false
    requestAnimationFrame(() => {
      flashing.value = true
      flashTimer = setTimeout(() => {
        flashing.value = false
        flashTimer = null
      }, 1000)
    })
  }

  watch(
    () => props.errors,
    (value) => {
      if (value.cultureMonth || value.stockingAvgLengthCm) {
        flashErrors()
        focusFirstError()
      }
    },
    { deep: true }
  )

  defineExpose({ focusFirstError, flashErrors })
</script>

<style scoped lang="scss">
  .growth-assessment-controls {
    margin-bottom: 16px;

    :deep(.el-card__body) {
      padding: 14px 16px;
    }

    .controls-row {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
    }

    .control-field {
      display: flex;
      flex: 1 1 240px;
      flex-direction: column;
      gap: 6px;
      min-width: 220px;
      padding: 8px;
      border: 1px solid transparent;
      border-radius: 8px;
      transition: border-color 0.2s ease;
    }

    .field-label {
      font-size: 13px;
      color: var(--el-text-color-regular);
    }

    .field-control {
      width: 100%;
    }

    .field-error {
      margin: 0;
      font-size: 12px;
      color: var(--el-color-danger);
    }

    .field-hint {
      margin: 0;
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }

    .control-field.is-error {
      border-color: var(--el-color-danger);
    }

    .control-field.is-error.is-flash {
      animation: growth-field-flash 0.5s ease-in-out 2;
    }

    .reference-preview {
      margin: 12px 0 0;
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }
  }

  @keyframes growth-field-flash {
    0%,
    100% {
      background: transparent;
    }

    50% {
      background: color-mix(in srgb, var(--el-color-danger) 14%, transparent);
    }
  }
</style>
