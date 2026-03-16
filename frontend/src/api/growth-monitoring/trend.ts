import api from '@/utils/http'

export interface GrowthTrendRecord {
  date: string
  weight: number
  feed: number
}

export interface SizeDistributionRecord {
  size_range: string
  percentage: number
}

export interface FcrRecord {
  date: string
  fishWeight: number
  feedTotal: number
  fcr: number
}

export interface InventoryRecord {
  timestamp: string
  type: string
  stock: number
  average_weight: number
}

export const getGrowthTrend = () => {
  return api.get<GrowthTrendRecord[]>({
    url: '/api/growth/trend'
  })
}

export const getSizeDistribution = () => {
  return api.get<SizeDistributionRecord[]>({
    url: '/api/growth/size-distribution'
  })
}

export const getFCRRecords = () => {
  return api.get<FcrRecord[]>({
    url: '/api/growth/fcr'
  })
}

export const getInventoryRecords = () => {
  return api.get<InventoryRecord[]>({
    url: '/api/growth/inventory'
  })
}
