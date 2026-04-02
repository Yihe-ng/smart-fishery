<template>
  <div class="forecast-section">
    <div class="forecast-title">未来3小时预报</div>
    <div class="forecast-list">
      <div v-for="item in data" :key="item.time" class="forecast-item">
        <div class="forecast-time">{{ item.time }}</div>
        <ArtSvgIcon :icon="getWeatherIconName(item.weatherCode)" class="forecast-icon" />
        <div class="forecast-temp">{{ item.temperature }}°</div>
        <div class="forecast-humidity">
          <ArtSvgIcon icon="ri:drop-line" class="humidity-icon" />
          <span>{{ item.humidity }}%</span>
        </div>
        <div class="forecast-pressure">{{ item.pressure }} hPa</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { getWeatherIconName } from '@/api/weather'
  import type { HourlyForecast } from '@/types/weather'

  defineOptions({ name: 'ForecastSection' })

  interface Props {
    data: HourlyForecast[]
  }

  defineProps<Props>()
</script>

<style scoped lang="scss">
  .forecast-section {
    display: flex;
    flex-direction: column;
    gap: 10px;

    .forecast-title {
      font-size: 12px;
      font-weight: 500;
      color: var(--art-gray-500);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .forecast-list {
      display: flex;
      gap: 8px;

      .forecast-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 12px 4px;
        background: var(--art-gray-100);
        border-radius: 8px;
        transition: background 0.2s ease;

        &:hover {
          background: var(--art-hover-color);
        }

        .forecast-time {
          font-size: 12px;
          font-weight: 600;
          color: var(--art-gray-700);
        }

        .forecast-icon {
          font-size: 22px;
          color: var(--art-primary);
        }

        .forecast-temp {
          font-size: 16px;
          font-weight: 700;
          color: var(--art-gray-900);
        }

        .forecast-humidity {
          display: flex;
          align-items: center;
          gap: 2px;
          font-size: 11px;
          color: var(--art-gray-500);

          .humidity-icon {
            font-size: 12px;
            color: var(--art-info);
          }
        }

        .forecast-pressure {
          font-size: 10px;
          color: var(--art-gray-500);
        }
      }
    }
  }

  // 深色模式适配
  :global(.dark) {
    .forecast-section {
      .forecast-list {
        .forecast-item {
          background: var(--art-gray-200);

          &:hover {
            background: var(--art-hover-color);
          }

          .forecast-temp {
            color: var(--art-gray-900);
          }
        }
      }
    }
  }
</style>
