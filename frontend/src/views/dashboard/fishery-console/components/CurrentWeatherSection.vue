<template>
  <div class="current-weather">
    <!-- 左侧：图标和温度 -->
    <div class="weather-left">
      <ArtSvgIcon :icon="weatherIcon" class="weather-icon" />
      <span class="temperature">{{ data.temperature }}°C</span>
    </div>

    <!-- 右侧：数据指标横向紧凑排布 -->
    <div class="weather-metrics">
      <div class="metric-item">
        <ArtSvgIcon icon="ri:bar-chart-box-line" class="metric-icon" />
        <span class="metric-value">{{ data.pressure }}<span class="metric-unit">hPa</span></span>
      </div>
      <div class="metric-item">
        <ArtSvgIcon icon="ri:windy-line" class="metric-icon" />
        <span class="metric-value">{{ data.windSpeed }}<span class="metric-unit">m/s</span></span>
      </div>
      <div class="metric-item">
        <ArtSvgIcon icon="ri:drop-line" class="metric-icon" />
        <span class="metric-value">{{ data.humidity }}<span class="metric-unit">%</span></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { getWeatherIconName } from '@/api/weather'
  import type { CurrentWeather } from '@/types/weather'

  defineOptions({ name: 'CurrentWeatherSection' })

  interface Props {
    data: CurrentWeather
  }

  const props = defineProps<Props>()

  const weatherIcon = computed(() => getWeatherIconName(props.data.weatherCode))
</script>

<style scoped lang="scss">
  .current-weather {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;

    .weather-left {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;

      .weather-icon {
        font-size: 36px;
        color: var(--art-warning);
      }

      .temperature {
        font-size: 28px;
        font-weight: 700;
        color: var(--art-gray-900);
        line-height: 1;
      }
    }

    .weather-metrics {
      display: flex;
      gap: 4px;
      flex: 1;
      justify-content: flex-end;

      .metric-item {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        background: var(--art-gray-100);
        border-radius: 4px;
        transition: background 0.2s ease;

        &:hover {
          background: var(--art-hover-color);
        }

        .metric-icon {
          font-size: 14px;
          color: var(--art-gray-500);
          flex-shrink: 0;
        }

        .metric-value {
          font-size: 12px;
          font-weight: 600;
          color: var(--art-gray-700);
          white-space: nowrap;

          .metric-unit {
            font-size: 10px;
            color: var(--art-gray-500);
            margin-left: 2px;
          }
        }
      }
    }
  }

  // 深色模式适配
  :global(.dark) {
    .current-weather {
      .weather-left {
        .temperature {
          color: var(--art-gray-900);
        }
      }

      .weather-metrics {
        .metric-item {
          background: var(--art-gray-200);

          &:hover {
            background: var(--art-hover-color);
          }

          .metric-value {
            color: var(--art-gray-700);
          }
        }
      }
    }
  }
</style>
