import { defineAsyncComponent } from 'vue'

export interface GlobalComponentConfig {
  name: string
  key: string
  component: any
  enabled?: boolean
  description?: string
}

export const globalComponentsConfig: GlobalComponentConfig[] = [
  {
    name: '全局设置面板',
    key: 'settings-panel',
    component: defineAsyncComponent(
      () => import('@/components/core/layouts/art-settings-panel/index.vue')
    ),
    enabled: true,
    description: '系统外观与布局配置入口'
  },
  {
    name: '全局搜索',
    key: 'global-search',
    component: defineAsyncComponent(
      () => import('@/components/core/layouts/art-global-search/index.vue')
    ),
    enabled: true,
    description: '全局页面搜索与快速跳转'
  },
  {
    name: '锁屏',
    key: 'screen-lock',
    component: defineAsyncComponent(
      () => import('@/components/core/layouts/art-screen-lock/index.vue')
    ),
    enabled: true,
    description: '系统锁屏组件'
  },
  {
    name: '水印',
    key: 'watermark',
    component: defineAsyncComponent(
      () => import('@/components/core/others/art-watermark/index.vue')
    ),
    enabled: true,
    description: '页面水印显示组件'
  },
  {
    name: 'AI 助手',
    key: 'ai-assistant',
    component: defineAsyncComponent(
      () => import('@/components/core/layouts/art-ai-assistant/index.vue')
    ),
    enabled: true,
    description: '基于当前页面上下文提供问答、建议与自动化操作'
  }
]

export const getEnabledGlobalComponents = () => {
  return globalComponentsConfig.filter((config) => config.enabled !== false)
}

export const getGlobalComponentByKey = (key: string) => {
  return globalComponentsConfig.find((config) => config.key === key)
}
