import { AppRouteRecord } from '@/types/router'
import { systemRoutes } from './system'
import { exceptionRoutes } from './exception'
import { fisheryRoutes } from './fishery'

/**
 * 导出所有模块化路由
 */
export const routeModules: AppRouteRecord[] = [fisheryRoutes, systemRoutes, exceptionRoutes]
