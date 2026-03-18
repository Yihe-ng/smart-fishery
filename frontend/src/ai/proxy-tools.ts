import * as z from 'zod/v4'
import type { PageAgentCore } from 'page-agent'

import { fetchExecuteTool } from '@/api/ai'

export interface PageAgentTool {
  description: string
  inputSchema: z.ZodType
  execute: (this: PageAgentCore, args: Record<string, unknown>) => Promise<string>
}

function makeProxyTool(
  toolName: string,
  description: string,
  inputSchema: z.ZodType,
): PageAgentTool {
  return {
    description,
    inputSchema,
    async execute(args) {
      const response = await fetchExecuteTool(toolName, { arguments: args })
      return response.result
    },
  }
}

export const PROXY_TOOL_DEFINITIONS: Record<string, PageAgentTool> = {
  get_water_quality_summary: makeProxyTool(
    'get_water_quality_summary',
    '获取当前鱼塘水质摘要和关键指标。',
    z.object({ pondId: z.string().optional() }),
  ),
  get_feeding_recommendation: makeProxyTool(
    'get_feeding_recommendation',
    '基于当前水质和投喂配置生成投喂建议。',
    z.object({ pondId: z.string().optional() }),
  ),
  get_alert_digest: makeProxyTool(
    'get_alert_digest',
    '获取当前页面最近告警摘要。',
    z.object({
      pondId: z.string().optional(),
      limit: z.number().optional(),
    }),
  ),
  get_device_status: makeProxyTool(
    'get_device_status',
    '获取当前鱼塘设备在线状态摘要。',
    z.object({ pondId: z.string().optional() }),
  ),
  preview_manual_feeding_action: makeProxyTool(
    'preview_manual_feeding_action',
    '生成一次手动投喂的预览确认信息，不执行真实动作。',
    z.object({
      pondId: z.string().optional(),
      amount: z.number(),
    }),
  ),
}

export function createProxyTools(allowedTools: string[]): Record<string, PageAgentTool> {
  const result: Record<string, PageAgentTool> = {}
  for (const name of allowedTools) {
    const def = PROXY_TOOL_DEFINITIONS[name]
    if (def) {
      result[name] = def
    }
  }
  return result
}
