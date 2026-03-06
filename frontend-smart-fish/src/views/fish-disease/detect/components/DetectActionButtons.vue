<template>
  <div class="detect-action-buttons">
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png"
      class="hidden-input"
      @change="handleFileChange"
    />
    <el-row :gutter="20">
      <el-col :span="8">
        <el-button
          type="primary"
          size="large"
          class="full-width"
          :disabled="isCameraActive"
          @click="triggerUpload"
        >
          <template #icon>
            <ArtSvgIcon icon="ri:upload-2-line" />
          </template>
          上传图像
        </el-button>
      </el-col>
      <el-col :span="8">
        <el-button
          type="success"
          size="large"
          class="full-width"
          :disabled="isCameraActive"
          @click="emit('start-camera')"
        >
          <template #icon>
            <ArtSvgIcon icon="ri:camera-line" />
          </template>
          开启摄像头
        </el-button>
      </el-col>
      <el-col :span="8">
        <el-button
          type="danger"
          size="large"
          class="full-width"
          :disabled="!isCameraActive"
          @click="emit('stop-detection')"
        >
          <template #icon>
            <ArtSvgIcon icon="ri:stop-circle-line" />
          </template>
          停止检测
        </el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import { ElMessage } from 'element-plus'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

  defineProps<{
    isCameraActive: boolean
  }>()

  const emit = defineEmits<{
    upload: [imgData: string]
    'start-camera': []
    'stop-detection': []
  }>()

  const fileInput = ref<HTMLInputElement>()

  const triggerUpload = () => {
    fileInput.value?.click()
  }

  const handleFileChange = (e: Event) => {
    const target = e.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return

    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      ElMessage.warning('仅支持 JPG/PNG 格式的图片')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.warning('文件大小不能超过 10MB')
      return
    }

    const reader = new FileReader()
    reader.onload = (event) => {
      emit('upload', event.target?.result as string)
    }
    reader.readAsDataURL(file)
    target.value = ''
  }
</script>

<style scoped lang="scss">
  .detect-action-buttons {
    .hidden-input {
      display: none;
    }

    .full-width {
      width: 100%;
    }
  }
</style>
