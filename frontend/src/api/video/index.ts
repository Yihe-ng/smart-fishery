import request from '@/utils/http'

/**
 * 获取视频文件列表
 * @returns 视频 URL 数组，如 ["/video/VID_20260330_161745.mp4", ...]
 */
export function getVideoList(): Promise<string[]> {
  return request.get<string[]>({ url: '/api/video/list' })
}
