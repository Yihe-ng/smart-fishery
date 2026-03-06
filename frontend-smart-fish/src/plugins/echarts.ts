import { use } from 'echarts/core'
import * as echarts from 'echarts/core'
import { graphic } from 'echarts/core'
import { CanvasRenderer, SVGRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, ScatterChart } from 'echarts/charts'
import type { BarSeriesOption } from 'echarts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  TitleComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

/**
 * 注册 ECharts 常用组件
 *
 * 如果需要使用其他图表类型（如 Radar, Gauge 等），请在此处引入并注册：
 * 1. import { RadarChart } from 'echarts/charts'
 * 2. use([..., RadarChart])
 */
use([
  CanvasRenderer,
  SVGRenderer,
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  TitleComponent
])

export { VChart, echarts, graphic }
export type { BarSeriesOption }
export type EChartsOption = import('echarts').EChartsOption
