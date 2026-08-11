<script setup lang="ts">
  import { onBeforeUnmount, onMounted, ref } from 'vue'

  defineOptions({ name: 'GrowthProcessAnimation' })

  /** 超过该时长后切换辅助提示文案 */
  const HINT_SWITCH_DELAY = 15_000

  const MODEL_LOADING_HINT = '首次识别可能需要加载模型，请稍候'
  const PROCESSING_HINT = '模型正在处理中，请继续稍候'

  const hintText = ref(MODEL_LOADING_HINT)
  let hintTimer: number | null = null

  onMounted(() => {
    hintTimer = window.setTimeout(() => {
      hintText.value = PROCESSING_HINT
    }, HINT_SWITCH_DELAY)
  })

  onBeforeUnmount(() => {
    if (hintTimer !== null) {
      window.clearTimeout(hintTimer)
      hintTimer = null
    }
  })
</script>

<template>
  <div class="growth-process-animation" role="status" aria-live="polite">
    <p class="process-title">正在分析鱼群图像</p>

    <div class="process-stages">
      <span class="process-stage stage-1">实例分割</span>
      <span class="process-arrow" aria-hidden="true">→</span>
      <span class="process-stage stage-2">可测性判断</span>
      <span class="process-arrow" aria-hidden="true">→</span>
      <span class="process-stage stage-3">体长估算</span>
    </div>

    <p class="process-hint">{{ hintText }}</p>
  </div>
</template>

<style scoped lang="scss">
  .growth-process-animation {
    position: fixed;
    top: calc(50% + 118px); /* 石斑鱼 Loading 图标（200px）正下方 */
    left: 50%;
    z-index: 3110; /* 高于全局 Loading 遮罩 3100 */
    display: flex;
    flex-direction: column;
    gap: 10px;
    align-items: center;
    pointer-events: none;
    transform: translateX(-50%);
    text-align: center;
  }

  .process-title {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    letter-spacing: 0.5px;
    animation: process-breathe 2.4s ease-in-out infinite;
  }

  .process-stages {
    display: flex;
    gap: 10px;
    align-items: center;
    white-space: nowrap;
  }

  /* 三个阶段依次循环高亮：周期 4.8s，负延迟错开 1.6s（实例分割 → 可测性判断 → 体长估算） */
  .process-stage {
    position: relative;
    padding: 3px 12px;
    font-size: 12px;
    color: var(--el-text-color-primary);
    border: 1px solid rgb(24 144 255 / 40%);
    border-radius: 999px;
    animation: stage-glow 4.8s linear infinite;
  }

  /* 未高亮时的淡蓝底：与毛玻璃背景区分，保证胶囊轮廓清晰 */
  .process-stage::after {
    position: absolute;
    inset: 0;
    z-index: -2;
    content: '';
    background: rgb(24 144 255 / 12%);
    border-radius: inherit;
  }

  /* 渐变高亮背景独立放在伪元素上，避免 gradient 突变，随 opacity 平滑过渡 */
  .process-stage::before {
    position: absolute;
    inset: -1px;
    z-index: -1;
    content: '';
    background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
    border-radius: inherit;
    box-shadow: 0 2px 10px rgb(24 144 255 / 35%);
    opacity: 0;
    animation: stage-bg-glow 4.8s linear infinite;
  }

  .stage-2,
  .stage-2::before {
    animation-delay: -3.2s;
  }

  .stage-3,
  .stage-3::before {
    animation-delay: -1.6s;
  }

  .process-arrow {
    font-size: 12px;
    color: var(--el-text-color-placeholder);
  }

  .process-hint {
    margin: 0;
    font-size: 12px;
    line-height: 1.6;
    color: var(--el-text-color-secondary);
    opacity: 0.85;
  }

  /* 轻微呼吸动画（标题） */
  @keyframes process-breathe {
    0%,
    100% {
      opacity: 1;
    }

    50% {
      opacity: 0.72;
    }
  }

  /* 阶段文字高亮态 */
  @keyframes stage-glow {
    0%,
    12% {
      opacity: 0.95;
      color: var(--el-text-color-primary);
      border-color: rgb(24 144 255 / 40%);
    }

    16%,
    42% {
      opacity: 1;
      color: #fff;
      border-color: transparent;
    }

    46%,
    100% {
      opacity: 0.95;
      color: var(--el-text-color-primary);
      border-color: rgb(24 144 255 / 40%);
    }
  }

  /* 阶段渐变背景高亮态 */
  @keyframes stage-bg-glow {
    0%,
    12% {
      opacity: 0;
    }

    16%,
    42% {
      opacity: 1;
    }

    46%,
    100% {
      opacity: 0;
    }
  }

  /* 移动端紧凑适配 */
  @media (width <= 480px) {
    .growth-process-animation {
      gap: 8px;
    }

    .process-title {
      font-size: 14px;
    }

    .process-stage {
      padding: 2px 10px;
      font-size: 11px;
    }

    .process-stages {
      gap: 6px;
    }

    .process-arrow {
      font-size: 11px;
    }

    .process-hint {
      font-size: 11px;
    }
  }
</style>
