<template>
  <div class="video-monitoring-page art-full-height">
    <page-content>
      <el-row :gutter="16">
        <el-col :span="18">
          <el-card shadow="never" header="实时视频流">
            <div class="aspect-video bg-black rounded-lg flex-center text-white">
              <ArtSvgIcon icon="ri:video-line" class="text-6xl opacity-20" />
              <span class="ml-4">视频加载中...</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" header="摄像头控制">
            <div class="grid grid-cols-3 gap-2">
              <el-button v-for="i in 9" :key="i" plain class="!m-0">
                <ArtSvgIcon :icon="getIcon(i)" />
              </el-button>
            </div>
            <div class="mt-4">
              <el-slider v-model="zoom" :min="1" :max="10" />
              <div class="text-center text-xs text-gray-400 mt-1">变倍 (Zoom)</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </page-content>
  </div>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  const zoom = ref(1)
  const getIcon = (i: number) => {
    const icons = [
      '',
      'ri:arrow-left-up-line',
      'ri:arrow-up-line',
      'ri:arrow-right-up-line',
      'ri:arrow-left-line',
      'ri:stop-circle-line',
      'ri:arrow-right-line',
      'ri:arrow-left-down-line',
      'ri:arrow-down-line',
      'ri:arrow-right-down-line'
    ]
    return icons[i]
  }
</script>
