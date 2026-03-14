import api from '@/utils/http'

// 生长趋势数据接口
export const getGrowthTrend = () => {
  return api.get({
    url: '/api/growth/trend'
  })
}

// 规格分布数据接口
export const getSizeDistribution = () => {
  return api.get({
    url: '/api/growth/size-distribution'
  })
}

// FCR 记录接口
export const getFCRRecords = () => {
  return api.get({
    url: '/api/growth/fcr'
  })
}

// 盘点记录接口
export const getInventoryRecords = () => {
  return api.get({
    url: '/api/growth/inventory'
  })
}
