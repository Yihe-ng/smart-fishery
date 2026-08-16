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
      path: 'growth-records',
      name: 'GrowthRecords',
      component: '/growth-monitoring/records/index',
      meta: { title: 'menus.fishery.growthRecords', icon: 'ri:file-list-3-line', keepAlive: true }
    },
    {
      path: 'feeding',
      name: 'Feeding',
      component: '/feeding/index',
      meta: { title: 'menus.fishery.feeding', icon: 'ri:hand-coin-line', keepAlive: true }
    },
    {
      path: 'data-management',
      name: 'DataManagement',
      component: '/fishery/data-management/index',
      meta: { title: 'menus.fishery.dataManagement', icon: 'ri:database-2-line', keepAlive: true }
    },
    {
      path: 'water-quality',
      name: 'WaterQuality',
      component: '/monitoring/water-quality/index',
      meta: {
        title: 'menus.fishery.waterQuality',
        icon: 'ri:temp-hot-line',
        keepAlive: true,
        isHide: true
      }
    },
    {
      path: 'production',
      name: 'Production',
      component: '/production/index',
      meta: {
        title: 'menus.fishery.production',
        icon: 'ri:bar-chart-box-line',
        keepAlive: true,
        isHide: true
      }
    }
  ]
}
