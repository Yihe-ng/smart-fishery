import { BaseResponse } from './common/response'

export interface PageResult<T> {
  list: T[]
  total: number
}

export interface PageQuery {
  current: number
  size: number
  [key: string]: any
}

export type { BaseResponse }
