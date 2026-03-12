/**
 * 全局 Loading 加载管理模块
 *
 * 提供统一的全屏加载动画管理（石斑鱼 + 泡泡动画 + 骨架屏）
 *
 * ## 主要功能
 *
 * - 全屏 Loading 显示和隐藏
 * - 自动适配明暗主题背景色
 * - 石斑鱼吐泡泡自定义动画
 * - 骨架屏预加载效果
 * - 单例模式防止重复创建
 * - 锁定页面交互
 *
 * ## 使用场景
 *
 * - 页面初始化加载
 * - 大量数据请求
 * - 路由切换过渡
 * - 异步操作等待
 * - 内容预加载骨架屏
 *
 * @module utils/ui/loading
 * @author GDOUHaiYuanYuYe
 */
import { createApp, type App as VueApp } from 'vue'
import ArtFishLoading from '@/components/core/base/art-fish-loading/index.vue'
import ArtSkeleton from '@/components/core/base/art-skeleton/index.vue'

interface LoadingInstance {
  close: () => void
}

interface SkeletonInstance {
  close: () => void
}

let loadingInstance: LoadingInstance | null = null
let skeletonInstance: SkeletonInstance | null = null

export const loadingService = {
  /**
   * 显示 loading（石斑鱼动画）
   * @returns 关闭 loading 的函数
   */
  showLoading(): () => void {
    if (!loadingInstance) {
      const container = document.createElement('div')
      document.body.appendChild(container)
      // 锁定页面滚动
      document.body.style.overflow = 'hidden'

      const app: VueApp = createApp(ArtFishLoading)
      app.mount(container)

      loadingInstance = {
        close: () => {
          app.unmount()
          container.remove()
          document.body.style.overflow = ''
        }
      }
    }
    return () => this.hideLoading()
  },

  /**
   * 隐藏 loading
   */
  hideLoading(): void {
    if (loadingInstance) {
      loadingInstance.close()
      loadingInstance = null
    }
  },

  /**
   * 显示骨架屏
   * @param options 骨架屏配置
   * @returns 关闭骨架屏的函数
   */
  showSkeleton(options: {
    type?: 'card' | 'list' | 'table' | 'dashboard'
    rows?: number
    container?: HTMLElement
  } = {}): () => void {
    const { type = 'dashboard', rows = 5, container: parentContainer } = options

    if (!skeletonInstance) {
      const container = parentContainer || document.createElement('div')
      if (!parentContainer) {
        container.className = 'skeleton-overlay'
        document.body.appendChild(container)
      }

      const app: VueApp = createApp(ArtSkeleton, {
        type,
        rows,
        animated: true
      })
      app.mount(container)

      skeletonInstance = {
        close: () => {
          app.unmount()
          if (!parentContainer) {
            container.remove()
          }
        }
      }
    }
    return () => this.hideSkeleton()
  },

  /**
   * 隐藏骨架屏
   */
  hideSkeleton(): void {
    if (skeletonInstance) {
      skeletonInstance.close()
      skeletonInstance = null
    }
  },

  /**
   * 智能加载：先显示骨架屏，再显示 Loading
   * 用于页面初始化场景
   * @param options 配置选项
   */
  async smartLoading<T>(
    promise: Promise<T>,
    options: {
      skeletonType?: 'card' | 'list' | 'table' | 'dashboard'
      skeletonDuration?: number
      showLoading?: boolean
    } = {}
  ): Promise<T> {
    const {
      skeletonType = 'dashboard',
      skeletonDuration = 300,
      showLoading = true
    } = options

    // 先显示骨架屏
    const closeSkeleton = this.showSkeleton({ type: skeletonType })

    try {
      // 等待数据加载
      const result = await promise

      // 延迟关闭骨架屏，让用户看到内容已加载
      await new Promise(resolve => setTimeout(resolve, skeletonDuration))
      closeSkeleton()

      return result
    } catch (error) {
      closeSkeleton()
      throw error
    }
  }
}

export default loadingService