<template>
  <el-card shadow="never" class="weather-card">
    <template #header>
      <div class="flex-cb">
        <div class="flex-c gap-2">
          <ArtSvgIcon icon="ri:cloud-line" class="text-primary" />
          <span class="font-bold">实时气象</span>
        </div>
        <span class="text-sm text-g-500">{{ weatherData.location }}</span>
      </div>
    </template>

    <div v-if="loading" class="loading-container flex-cc">
      <ArtSvgIcon
        icon="ri:loader-4-line"
        class="animate-spin text-primary"
        style="font-size: 24px"
      />
      <span class="text-g-500 mt-2">加载中...</span>
    </div>

    <div v-else-if="error" class="error-container flex-cc">
      <ArtSvgIcon icon="ri:error-warning-line" class="text-error" style="font-size: 24px" />
      <span class="text-g-500 mt-2">{{ error }}</span>
    </div>

    <template v-else>
      <!-- 当前天气 -->
      <CurrentWeatherSection :data="weatherData.current" />

      <!-- 分隔线 -->
      <div class="divider" />

      <!-- 预报 -->
      <ForecastSection :data="weatherData.forecast" />

      <!-- 更新时间 -->
      <div class="update-time">更新于 {{ weatherData.updateTime }}</div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import CurrentWeatherSection from './CurrentWeatherSection.vue'
  import ForecastSection from './ForecastSection.vue'
  import { getWeatherData } from '@/api/weather'
  import type { WeatherData } from '@/types/weather'

  defineOptions({ name: 'WeatherCard' })

  // 状态
  const loading = ref(false)
  const error = ref('')
  const weatherData = ref<WeatherData>({
    current: {
      temperature: 0,
      pressure: 0,
      windSpeed: 0,
      humidity: 0,
      weatherCode: 0
    },
    forecast: [],
    location: '广东阳西',
    updateTime: '--:--'
  })

  // 定时器
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  // 加载天气数据
  const loadWeatherData = async () => {
    loading.value = true
    error.value = ''
    try {
      const data = await getWeatherData()
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
  .weather-card {
    display: flex;
    flex-direction: column;
    height: 100%;

    :deep(.el-card__header) {
      flex-shrink: 0;
      padding: 12px 16px;
      border-bottom: 1px solid var(--default-border);
    }

    :deep(.el-card__body) {
      display: flex;
      flex-direction: column;
      flex: 1;
      padding: 16px;
      overflow: hidden;
    }
  }

  .loading-container,
  .error-container {
    flex: 1;
    flex-direction: column;
  }

  .divider {
    height: 1px;
    background: var(--default-border);
    margin: 12px 0;
  }

  .update-time {
    margin-top: auto;
    padding-top: 10px;
    font-size: 11px;
    color: var(--art-gray-500);
    text-align: center;
  }

  // 深色模式适配
  :global(.dark) {
    .weather-card {
      :deep(.el-card__header) {
        border-bottom-color: var(--art-card-border);
      }

      .divider {
        background: var(--art-card-border);
      }
    }
  }
</style>
