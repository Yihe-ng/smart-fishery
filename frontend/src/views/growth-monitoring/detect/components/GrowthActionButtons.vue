<template>
  <div class="detect-action-buttons">
    <input
      ref="imageInputRef"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      class="hidden-input"
      @change="handleImageChange"
    />
    <input
      ref="videoInputRef"
      type="file"
      accept="video/mp4,video/webm,video/quicktime,video/x-msvideo,.mp4,.mov,.webm,.avi,.mkv"
      class="hidden-input"
      @change="handleVideoChange"
    />

    <el-row :gutter="20">
      <el-col :span="8">
        <el-button
          type="primary"
          size="large"
          class="full-width"
          :loading="processing"
          :disabled="processing"
          @click="triggerImageUpload"
        >
          <template #icon>
            <ArtSvgIcon icon="ri:upload-2-line" />
          </template>
          {{ hasImage ? '重新识别图片' : '上传图片' }}
        </el-button>
      </el-col>

      <el-col :span="8">
        <el-button
          type="success"
          size="large"
          class="full-width"
          :loading="processing"
          :disabled="processing"
          @click="triggerVideoUpload"
        >
          <template #icon>
            <ArtSvgIcon icon="ri:video-upload-line" />
          </template>
          上传视频
        </el-button>
      </el-col>

      <el-col :span="8">
        <el-button
          type="danger"
          size="large"
          class="full-width"
          :disabled="processing || !hasImage"
          @click="emit('clear')"
        >
          <template #icon>
            <ArtSvgIcon icon="ri:delete-bin-line" />
          </template>
          清空结果
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
    processing: boolean
    hasImage: boolean
  }>()

  const emit = defineEmits<{
    uploadImage: [imgData: string]
    uploadVideo: [file: File]
    clear: []
  }>()

  const imageInputRef = ref<HTMLInputElement>()
  const videoInputRef = ref<HTMLInputElement>()

  const triggerImageUpload = () => {
    imageInputRef.value?.click()
  }

  const triggerVideoUpload = () => {
    videoInputRef.value?.click()
  }

  const handleImageChange = (event: Event) => {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      ElMessage.warning('仅支持 JPG、PNG、WEBP 格式图片')
      target.value = ''
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      ElMessage.warning('图片大小不能超过 10MB')
      target.value = ''
      return
    }

    const reader = new FileReader()
    reader.onload = (loadEvent) => {
      emit('uploadImage', loadEvent.target?.result as string)
    }
    reader.readAsDataURL(file)
    target.value = ''
  }

  const handleVideoChange = (event: Event) => {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return

    const allowedTypes = [
      'video/mp4',
      'video/webm',
      'video/quicktime',
      'video/x-msvideo',
      'video/x-matroska'
    ]
    const hasValidExtension = /\.(mp4|mov|webm|avi|mkv)$/i.test(file.name)
    if ((file.type && !allowedTypes.includes(file.type)) || !hasValidExtension) {
      ElMessage.warning('仅支持 MP4、MOV、WEBM、AVI、MKV 格式视频')
      target.value = ''
      return
    }

    if (file.size > 50 * 1024 * 1024) {
      ElMessage.warning('视频大小不能超过 50MB')
      target.value = ''
      return
    }

    emit('uploadVideo', file)
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
