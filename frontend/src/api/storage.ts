import request from '@/utils/http'

export interface StorageRuleStatus {
  prefix: string
  keepDays: number
  count: number
  totalBytes: number
  oldestAgeDays: number | null
}

export interface StorageLastCleanup {
  time: string
  deleted: number
}

export interface StorageStatus {
  backend: string
  rules: StorageRuleStatus[]
  lastCleanup: StorageLastCleanup | null
}

/** 获取存储后端与保留策略状态（只读） */
export function fetchStorageStatus() {
  return request.get<StorageStatus>({
    url: '/api/storage/status'
  })
}
