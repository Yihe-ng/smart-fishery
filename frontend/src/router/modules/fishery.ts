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
      path: 'water-quality',
      name: 'WaterQuality',
      component: '/monitoring/water-quality/index',
      meta: { title: 'menus.fishery.waterQuality', icon: 'ri:temp-hot-line', keepAlive: true }
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
      path: 'production',
      name: 'Production',
      component: '/production/index',
      meta: { title: 'menus.fishery.production', icon: 'ri:bar-chart-box-line', keepAlive: true }
    }
  ]
}
