/**
 * 全局 Loading 加载管理模块
 *
 * 提供统一的全屏加载动画管理（石斑鱼 + 泡泡动画）
 *
 * ## 主要功能
 *
 * - 全屏 Loading 显示和隐藏
 * - 自动适配明暗主题背景色
 * - 石斑鱼吐泡泡自定义动画
 * - 单例模式防止重复创建
 * - 锁定页面交互
 *
 * ## 使用场景
 *
 * - 页面初始化加载
 * - 大量数据请求
 * - 路由切换过渡
 * - 异步操作等待
 *
 * @module utils/ui/loading
 * @author GDOUHaiYuanYuYe
 */
import { createApp, type App as VueApp } from 'vue'
import ArtFishLoading from '@/components/core/base/art-fish-loading/index.vue'

interface LoadingInstance {
  close: () => void
}

let loadingInstance: LoadingInstance | null = null

export const loadingService = {
  /**
   * 显示 loading
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
  }
}
