import { AppRouteRecord } from '@/types/router'

export const fisheryRoutes: AppRouteRecord = {
  path: '/fishery',
  name: 'Fishery',
  component: '/index/index',
  meta: {
    title: 'menus.fishery.title',
    icon: 'ri:water-flash-line',
    roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
  },
  children: [
    {
      path: 'dashboard',
      name: 'FisheryDashboard',
      component: '/dashboard/fishery-console/index',
      meta: { title: 'menus.fishery.dashboard', icon: 'ri:dashboard-line', keepAlive: true }
    },
    {
      path: 'growth',
      name: 'GrowthRecognition',
      component: '/growth-monitoring/detect/index',
      meta: { title: 'menus.fishery.growth', icon: 'ri:scales-3-line', keepAlive: true }
    },
    {
      path: 'feeding',
      name: 'Feeding',
      component: '/feeding/index',
      meta: { title: 'menus.fishery.feeding', icon: 'ri:hand-coin-line', keepAlive: true }
    },
    {
      path: 'fish-disease',
      name: 'FishDisease',
      component: '/outside/Iframe',
      redirect: '/fishery/growth',
      meta: {
        title: 'menus.fishery.disease',
        icon: 'ri:microscope-line',
        keepAlive: true,
        isHide: true
      }
    }
    // 水质监测和生产数据页面暂不注册到渔业菜单；源码保留，后续可按需要恢复。
  ]
}
