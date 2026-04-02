<template>
  <el-card shadow="never" class="weather-card-compact">
    <template #header>
      <div class="flex-cb">
        <div class="flex-c gap-2">
          <ArtSvgIcon icon="ri:cloud-line" class="text-primary" />
          <span class="font-bold">实时气象</span>
        </div>
        <el-tag :type="pressureRiskType" size="small" effect="light" class="risk-tag">
          气压{{ weatherData.pressureRisk?.text || '低风险' }}
        </el-tag>
      </div>
    </template>

    <div v-if="loading" class="loading-container flex-cc">
      <ArtSvgIcon
        icon="ri:loader-4-line"
        class="animate-spin text-primary"
        style="font-size: 18px"
      />
    </div>

    <div v-else-if="error" class="error-container flex-cc">
      <ArtSvgIcon icon="ri:error-warning-line" class="text-error" style="font-size: 18px" />
    </div>

    <template v-else>
      <!-- 三行布局 -->
      <div class="weather-body">
        <!-- 第一行：图标、温度、地点 -->
        <div class="weather-first-row">
          <div class="weather-icon-temp">
            <ArtSvgIcon :icon="weatherIcon" class="weather-icon" />
            <span class="temperature">{{ weatherData.current?.temperature }}°C</span>
          </div>
          <span class="location">{{ weatherData.location }}</span>
        </div>

        <!-- 第二行：三个指标小卡片 -->
        <div class="weather-metrics-row">
          <div class="metric-card" :class="pressureMetricClass">
            <ArtSvgIcon icon="ri:bar-chart-box-line" class="metric-icon" />
            <div class="metric-info">
              <span class="metric-value">{{ weatherData.current?.pressure }}</span>
              <span class="metric-unit">hPa</span>
            </div>
          </div>
          <div class="metric-card">
            <ArtSvgIcon icon="ri:windy-line" class="metric-icon" />
            <div class="metric-info">
              <span class="metric-value">{{ weatherData.current?.windSpeed }}</span>
              <span class="metric-unit">m/s</span>
            </div>
          </div>
          <div class="metric-card">
            <ArtSvgIcon icon="ri:drop-line" class="metric-icon" />
            <div class="metric-info">
              <span class="metric-value">{{ weatherData.current?.humidity }}</span>
              <span class="metric-unit">%</span>
            </div>
          </div>
        </div>

        <!-- 第三行：更新时间 -->
        <div class="update-time-row">更新于 {{ weatherData.updateTime }}</div>
      </div>

      <!-- 气压风险提示 -->
      <div
        v-if="weatherData.pressureRisk?.level !== 'low'"
        class="risk-alert"
        :class="`risk-${weatherData.pressureRisk?.level}`"
      >
        <ArtSvgIcon icon="ri:alert-line" class="alert-icon" />
        <span class="alert-text">{{ weatherData.pressureRisk?.description }}</span>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
  import { ref, onMounted, onUnmounted, computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { getWeatherDataFromBackend, getWeatherIconName } from '@/api/weather'
  import type { WeatherData, PressureRisk } from '@/types/weather'

  defineOptions({ name: 'WeatherCardCompact' })

  // 扩展WeatherData类型以包含pressureRisk
  interface WeatherDataWithRisk extends WeatherData {
    pressureRisk?: PressureRisk
  }

  // 状态
  const loading = ref(false)
  const error = ref('')
  const weatherData = ref<WeatherDataWithRisk>({
    current: {
      temperature: 0,
      pressure: 0,
      windSpeed: 0,
      humidity: 0,
      weatherCode: 0
    },
    forecast: [],
    location: '广东阳西',
    updateTime: '--:--',
    pressureRisk: {
      level: 'low',
      text: '低风险',
      description: '气压正常，适合正常投喂',
      feedingSuggestion: '可按正常计划投喂',
      pressure: 1013
    }
  })

  // 定时器
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  // 计算天气图标
  const weatherIcon = computed(() => {
    return getWeatherIconName(weatherData.value.current?.weatherCode || 0)
  })

  // 气压风险标签类型
  const pressureRiskType = computed(() => {
    const level = weatherData.value.pressureRisk?.level
    if (level === 'high') return 'danger'
    if (level === 'medium') return 'warning'
    return 'success'
  })

  // 气压指标样式类
  const pressureMetricClass = computed(() => {
    const level = weatherData.value.pressureRisk?.level
    if (level === 'high') return 'metric-danger'
    if (level === 'medium') return 'metric-warning'
    return ''
  })

  // 加载天气数据
  const loadWeatherData = async () => {
    loading.value = true
    error.value = ''
    try {
      const data = await getWeatherDataFromBackend()
      weatherData.value = data
    } catch (err) {
      console.error('获取天气数据失败:', err)
      error.value = '获取天气数据失败'
    } finally {
      loading.value = false
    }
  }

  // 组件挂载时加载数据并设置定时器
  onMounted(() => {
    loadWeatherData()
    // 每30分钟刷新一次
    refreshTimer = setInterval(loadWeatherData, 30 * 60 * 1000)
  })

  // 组件卸载时清除定时器
  onUnmounted(() => {
    if (refreshTimer) {
      clearInterval(refreshTimer)
    }
  })
</script>

<style scoped lang="scss">
  .weather-card-compact {
    display: flex;
    flex-direction: column;
    height: 100%;

    :deep(.el-card__header) {
      flex-shrink: 0;
      padding: 6px 8px;
      border-bottom: 1px solid var(--default-border);
    }

    :deep(.el-card__body) {
      display: flex;
      flex-direction: column;
      flex: 1;
      padding: 8px;
      overflow: hidden;
    }

    .risk-tag {
      font-size: 9px;
      height: 18px;
      line-height: 16px;
      padding: 0 4px;
    }
  }

  .loading-container,
  .error-container {
    flex: 1;
    flex-direction: column;
    min-height: 50px;
  }

  // 三行布局
  .weather-body {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 8px;

    // 第一行：图标、温度、地点
    .weather-first-row {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .weather-icon-temp {
        display: flex;
        align-items: center;
        gap: 6px;

        .weather-icon {
          font-size: 20px;
          color: var(--art-warning);
        }

        .temperature {
          font-size: 20px;
          font-weight: 700;
          color: var(--art-gray-900);
          line-height: 1;
        }
      }

      .location {
        font-size: 11px;
        color: var(--art-gray-500);
      }
    }

    // 第二行：三个指标小卡片
    .weather-metrics-row {
      display: flex;
      gap: 6px;
      justify-content: space-between;
      flex: 1;

      .metric-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        flex: 1;
        padding: 6px 4px;
        background: var(--art-gray-100);
        border-radius: 6px;

        &.metric-warning {
          background: var(--el-color-warning-light-9);
        }

        &.metric-danger {
          background: var(--el-color-danger-light-9);
        }

        .metric-icon {
          font-size: 14px;
          color: var(--art-gray-500);
        }

        .metric-info {
          display: flex;
          flex-direction: column;
          align-items: center;
          line-height: 1.2;

          .metric-value {
            font-size: 12px;
            font-weight: 600;
            color: var(--art-gray-700);
          }

          .metric-unit {
            font-size: 9px;
            color: var(--art-gray-500);
          }
        }
      }
    }

    // 第三行：更新时间
    .update-time-row {
      font-size: 9px;
      color: var(--art-gray-400);
      text-align: center;
      flex-shrink: 0;
    }
  }

  .risk-alert {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 6px;
    padding: 4px 6px;
    border-radius: 4px;
    font-size: 10px;
    flex-shrink: 0;

    &.risk-high {
      background: var(--el-color-danger-light-9);
      color: var(--el-color-danger);
    }

    &.risk-medium {
      background: var(--el-color-warning-light-9);
      color: var(--el-color-warning-dark);
    }

    .alert-icon {
      font-size: 12px;
      flex-shrink: 0;
    }

    .alert-text {
      line-height: 1.3;
    }
  }

  // 深色模式适配
  :global(.dark) {
    .weather-card-compact {
      :deep(.el-card__header) {
        border-bottom-color: var(--art-card-border);
      }
    }

    .weather-body {
      .weather-metrics-row {
        .metric-card {
          background: var(--art-gray-200);
        }
      }
    }
  }
</style>
