<!-- 通知组件 -->
<template>
  <div
    class="art-notification-panel art-card-sm !shadow-xl"
    :style="{
      transform: show ? 'scaleY(1)' : 'scaleY(0.9)',
      opacity: show ? 1 : 0
    }"
    v-show="visible"
    @click.stop
  >
    <div class="flex-cb px-3.5 mt-3.5">
      <span class="text-base font-medium text-g-800">{{ $t('notice.title') }}</span>
      <span class="text-xs text-g-800 px-1.5 py-1 c-p select-none rounded hover:bg-g-200">
        {{ $t('notice.btnRead') }}
      </span>
    </div>

    <ul class="box-border flex items-end w-full h-12.5 px-3.5 border-b-d">
      <li
        v-for="(item, index) in barList"
        :key="index"
        class="h-12 leading-12 mr-5 overflow-hidden text-[13px] text-g-700 c-p select-none"
        :class="{ 'bar-active': barActiveIndex === index }"
        @click="changeBar(index)"
      >
        {{ item.name }} ({{ item.num }})
      </li>
    </ul>

    <div class="w-full h-[calc(100%-95px)]">
      <div class="h-[calc(100%-60px)] overflow-y-scroll scrollbar-thin">
        <!-- 通知 -->
        <ul v-show="barActiveIndex === 0">
          <li
            v-for="(item, index) in noticeList"
            :key="index"
            class="box-border flex-c px-3.5 py-3.5 c-p last:border-b-0 hover:bg-g-200/60"
          >
            <div
              class="size-9 leading-9 text-center rounded-lg flex-cc"
              :class="[getNoticeStyle(item.type).iconClass]"
            >
              <ArtSvgIcon class="text-lg !bg-transparent" :icon="getNoticeStyle(item.type).icon" />
            </div>
            <div class="w-[calc(100%-45px)] ml-3.5">
              <h4 class="text-sm font-normal leading-5.5 text-g-900">{{ item.title }}</h4>
              <p class="mt-1.5 text-xs text-g-500">{{ item.time }}</p>
            </div>
          </li>
        </ul>

        <!-- 消息 -->
        <ul v-show="barActiveIndex === 1">
          <li
            v-for="(item, index) in msgList"
            :key="index"
            class="box-border flex-c px-3.5 py-3.5 c-p last:border-b-0 hover:bg-g-200/60"
          >
            <div class="w-9 h-9">
              <img :src="item.avatar" class="w-full h-full rounded-lg" />
            </div>
            <div class="w-[calc(100%-45px)] ml-3.5">
              <h4 class="text-xs font-normal leading-5.5">{{ item.title }}</h4>
              <p class="mt-1.5 text-xs text-g-500">{{ item.time }}</p>
            </div>
          </li>
        </ul>

        <!-- 待办 -->
        <ul v-show="barActiveIndex === 2">
          <li
            v-for="(item, index) in pendingList"
            :key="index"
            class="box-border px-5 py-3.5 last:border-b-0"
          >
            <h4>{{ item.title }}</h4>
            <p class="text-xs text-g-500">{{ item.time }}</p>
          </li>
        </ul>

        <!-- 空状态 -->
        <div
          v-show="currentTabIsEmpty"
          class="relative top-25 h-full text-g-500 text-center !bg-transparent"
        >
          <ArtSvgIcon icon="system-uicons:inbox" class="text-5xl" />
          <p class="mt-3.5 text-xs !bg-transparent"
            >{{ $t('notice.text[0]') }}{{ barList[barActiveIndex].name }}</p
          >
        </div>
      </div>

      <div class="relative box-border w-full px-3.5">
        <ElButton class="w-full mt-3" @click="handleViewAll" v-ripple>
          {{ $t('notice.viewAll') }}
        </ElButton>
      </div>
    </div>

    <div class="h-25"></div>
  </div>
</template>

<script setup lang="ts">
  import { computed, ref, watch, type ComputedRef } from 'vue'
  import { useI18n } from 'vue-i18n'

  // 导入头像图片
  import avatar from '@/assets/images/avatar/avatar.webp'

  defineOptions({ name: 'ArtNotification' })

  interface NoticeItem {
    /** 标题 */
    title: string
    /** 时间 */
    time: string
    /** 类型 */
    type: NoticeType
  }

  interface MessageItem {
    /** 标题 */
    title: string
    /** 时间 */
    time: string
    /** 头像 */
    avatar: string
  }

  interface PendingItem {
    /** 标题 */
    title: string
    /** 时间 */
    time: string
  }

  interface BarItem {
    /** 名称 */
    name: ComputedRef<string>
    /** 数量 */
    num: number
  }

  interface NoticeStyle {
    /** 图标 */
    icon: string
    /** icon 样式 */
    iconClass: string
  }

  type NoticeType = 'email' | 'message' | 'collection' | 'user' | 'notice'

  const { t } = useI18n()

  const props = defineProps<{
    value: boolean
  }>()

  const emit = defineEmits<{
    'update:value': [value: boolean]
  }>()

  const show = ref(false)
  const visible = ref(false)
  const barActiveIndex = ref(0)

  const useNotificationData = () => {
    // 通知数据
    const noticeList = ref<NoticeItem[]>([
      {
        title: '新增国际化',
        time: '2024-6-13 0:10',
        type: 'notice'
      },
      {
        title: '冷月呆呆给你发了一条消息',
        time: '2024-4-21 8:05',
        type: 'message'
      },
      {
        title: '小肥猪关注了你',
        time: '2020-3-17 21:12',
        type: 'collection'
      },
      {
        title: '新增使用文档',
        time: '2024-02-14 0:20',
        type: 'notice'
      },
      {
        title: '小肥猪给你发了一封邮件',
        time: '2024-1-20 0:15',
        type: 'email'
      },
      {
        title: '菜单mock本地真实数据',
        time: '2024-1-17 22:06',
        type: 'notice'
      }
    ])

    // 消息数据
    const msgList = ref<MessageItem[]>([
      {
        title: '池不胖 关注了你',
        time: '2021-2-26 23:50',
        avatar: avatar
      },
      {
        title: '唐不苦 关注了你',
        time: '2021-2-21 8:05',
        avatar: avatar
      },
      {
        title: '中小鱼 关注了你',
        time: '2020-1-17 21:12',
        avatar: avatar
      },
      {
        title: '何小荷 关注了你',
        time: '2021-01-14 0:20',
        avatar: avatar
      },
      {
        title: '誶誶淰 关注了你',
        time: '2020-12-20 0:15',
        avatar: avatar
      },
      {
        title: '冷月呆呆 关注了你',
        time: '2020-12-17 22:06',
        avatar: avatar
      }
    ])

    // 待办数据
    const pendingList = ref<PendingItem[]>([])

    // 标签栏数据
    const barList = computed<BarItem[]>(() => [
      {
        name: computed(() => t('notice.bar[0]')),
        num: noticeList.value.length
      },
      {
        name: computed(() => t('notice.bar[1]')),
        num: msgList.value.length
      },
      {
        name: computed(() => t('notice.bar[2]')),
        num: pendingList.value.length
      }
    ])

    return {
      noticeList,
      msgList,
      pendingList,
      barList
    }
  }

  // 样式管理
  const useNotificationStyles = () => {
    const noticeStyleMap: Record<NoticeType, NoticeStyle> = {
      email: {
        icon: 'ri:mail-line',
        iconClass: 'bg-warning/12 text-warning'
      },
      message: {
        icon: 'ri:volume-down-line',
        iconClass: 'bg-success/12 text-success'
      },
      collection: {
        icon: 'ri:heart-3-line',
        iconClass: 'bg-danger/12 text-danger'
      },
      user: {
        icon: 'ri:volume-down-line',
        iconClass: 'bg-info/12 text-info'
      },
      notice: {
        icon: 'ri:notification-3-line',
        iconClass: 'bg-theme/12 text-theme'
      }
    }

    const getNoticeStyle = (type: NoticeType): NoticeStyle => {
      const defaultStyle: NoticeStyle = {
        icon: 'ri:arrow-right-circle-line',
        iconClass: 'bg-theme/12 text-theme'
      }

      return noticeStyleMap[type] || defaultStyle
    }

    return {
      getNoticeStyle
    }
  }

  // 面板显示状态管理
  const usePanelVisibility = () => {
    // 监听 props.value 变化，控制面板显示
    watch(
      () => props.value,
      (val) => {
        show.value = val
        if (val) {
          // 显示时，立即设置为可见
          visible.value = true
        } else {
          // 隐藏时，延迟 300ms 设置为不可见（等待动画结束）
          setTimeout(() => {
            visible.value = false
          }, 300)
        }
      }
    )

    // 点击外部关闭面板
    const closePanel = () => {
      if (show.value) {
        emit('update:value', false)
      }
    }

    return {
      closePanel
    }
  }

  // 标签栏切换管理
  const useTabSwitch = () => {
    const changeBar = (index: number) => {
      barActiveIndex.value = index
    }

    const currentTabIsEmpty = computed(() => {
      const { noticeList, msgList, pendingList } = useNotificationData()
      if (barActiveIndex.value === 0) return noticeList.value.length === 0
      if (barActiveIndex.value === 1) return msgList.value.length === 0
      if (barActiveIndex.value === 2) return pendingList.value.length === 0
      return true
    })

    return {
      changeBar,
      currentTabIsEmpty
    }
  }

  // 初始化所有逻辑
  const { noticeList, msgList, pendingList, barList } = useNotificationData()
  const { getNoticeStyle } = useNotificationStyles()
  const { closePanel } = usePanelVisibility()
  const { changeBar, currentTabIsEmpty } = useTabSwitch()

  // 暴露给模板
  const handleViewAll = () => {
    // 处理查看全部的逻辑
  }

  // 监听点击事件，关闭面板
  // 注意：需要确保父组件传递了 click-outside 事件或在全局处理点击
  if (typeof window !== 'undefined') {
    window.addEventListener('click', closePanel)
  }
</script>

<style lang="scss" scoped>
  .art-notification-panel {
    position: absolute;
    top: 55px;
    right: -50px;
    z-index: 9999;
    box-sizing: border-box;
    width: 320px;
    height: 420px;
    overflow: hidden;
    background: var(--art-bg-color);
    border: 1px solid var(--art-border-dashed-color);
    border-radius: 12px;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    transform-origin: top right;

    @media only screen and (width <= 768px) {
      position: fixed;
      top: 60px;
      right: 0;
      left: 0;
      width: 90%;
      margin: 0 auto;
    }

    .bar-active {
      position: relative;
      font-weight: 500;
      color: var(--art-text-gray-900);

      &::after {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        content: '';
        background: var(--el-color-primary);
      }
    }
  }
</style>
