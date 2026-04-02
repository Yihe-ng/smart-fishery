import type { WeatherData, BackendWeatherData } from '@/types/weather'
import request from '@/utils/http'

/**
 * 天气代码映射为图标名称
 * @param code - WMO Weather interpretation code
 * @returns Remix Icon 名称
 */
function getWeatherIconName(code: number): string {
  // WMO Weather interpretation codes (WW)
  // 0: Clear sky
  if (code === 0) return 'ri:sun-line'

  // 1, 2, 3: Mainly clear, partly cloudy, and overcast
  if (code >= 1 && code <= 3) return 'ri:cloudy-line'

  // 45, 48: Fog and depositing rime fog
  if (code === 45 || code === 48) return 'ri:foggy-line'

  // 51, 53, 55: Drizzle: Light, moderate, and dense intensity
  if (code >= 51 && code <= 55) return 'ri:drizzle-line'

  // 56, 57: Freezing Drizzle: Light and dense intensity
  if (code === 56 || code === 57) return 'ri:drizzle-line'

  // 61, 63, 65: Rain: Slight, moderate and heavy intensity
  if (code >= 61 && code <= 65) return 'ri:rainy-line'

  // 66, 67: Freezing Rain: Light and heavy intensity
  if (code === 66 || code === 67) return 'ri:rainy-line'

  // 71, 73, 75: Snow fall: Slight, moderate, and heavy intensity
  if (code >= 71 && code <= 75) return 'ri:snowy-line'

  // 77: Snow grains
  if (code === 77) return 'ri:snowy-line'

  // 80, 81, 82: Rain showers: Slight, moderate, and violent
  if (code >= 80 && code <= 82) return 'ri:showers-line'

  // 85, 86: Snow showers slight and heavy
  if (code === 85 || code === 86) return 'ri:snowy-line'

  // 95: Thunderstorm: Slight or moderate
  // 96, 99: Thunderstorm with slight and heavy hail
  if (code >= 95) return 'ri:thunderstorms-line'

  return 'ri:sun-cloudy-line'
}

/**
 * 天气代码映射为中文描述
 * @param code - WMO Weather interpretation code
 * @returns 中文天气描述
 */
function getWeatherDescription(code: number): string {
  if (code === 0) return '晴'
  if (code === 1) return ' mainly clear'
  if (code === 2) return '多云'
  if (code === 3) return '阴'
  if (code === 45 || code === 48) return '雾'
  if (code >= 51 && code <= 57) return '毛毛雨'
  if (code >= 61 && code <= 67) return '雨'
  if (code >= 71 && code <= 77) return '雪'
  if (code >= 80 && code <= 82) return '阵雨'
  if (code === 85 || code === 86) return '阵雪'
  if (code >= 95) return '雷雨'
  return '多云'
}

/**
 * 气压风险等级类型
 */
export interface PressureRisk {
  level: 'high' | 'medium' | 'low'
  text: string
  description: string
  feedingSuggestion: string
  pressure: number
}

/**
 * 从后端获取天气数据（包含气压风险等级）
 * @returns 天气数据
 */
export async function getWeatherDataFromBackend(): Promise<
  WeatherData & { pressureRisk: PressureRisk }
> {
  const response = await request.get<BackendWeatherData>({
    url: '/api/weather/current'
  })

  return {
    current: {
      temperature: response.current.temperature,
      pressure: response.current.pressure,
      windSpeed: response.current.windSpeed,
      humidity: response.current.humidity,
      weatherCode: response.current.weatherCode
    },
    forecast: [], // 后端暂不提供预报，保持兼容
    location: response.location,
    updateTime: response.updateTime,
    pressureRisk: response.pressureRisk
  }
}

/**
 * 获取当前天气和未来3小时预报（直接调用Open-Meteo，用于dashboard）
 * @returns 天气数据
 */
export async function getWeatherData(): Promise<WeatherData> {
  // 广东阳江市阳西区坐标
  const YANGXI_LATITUDE = 21.75
  const YANGXI_LONGITUDE = 111.75
  const LOCATION_NAME = '广东阳西'

  const url = new URL('https://api.open-meteo.com/v1/forecast')
  url.searchParams.append('latitude', YANGXI_LATITUDE.toString())
  url.searchParams.append('longitude', YANGXI_LONGITUDE.toString())
  url.searchParams.append(
    'current',
    'temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,weather_code'
  )
  url.searchParams.append(
    'hourly',
    'temperature_2m,surface_pressure,relative_humidity_2m,weather_code'
  )
  url.searchParams.append('timezone', 'Asia/Shanghai')
  url.searchParams.append('forecast_hours', '4')

  const response = await fetch(url.toString())

  if (!response.ok) {
    throw new Error(`天气API请求失败: ${response.status}`)
  }

  const data = await response.json()

  // 格式化时间
  const formatTime = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  }

  // 处理当前天气
  const current = {
    temperature: Math.round(data.current.temperature_2m),
    pressure: Math.round(data.current.surface_pressure),
    windSpeed: Math.round(data.current.wind_speed_10m * 10) / 10,
    humidity: data.current.relative_humidity_2m,
    weatherCode: data.current.weather_code
  }

  // 处理未来3小时预报
  const forecast: WeatherData['forecast'] = []
  const now = new Date()
  const currentHour = now.getHours()

  for (let i = 0; i < data.hourly.time.length; i++) {
    const hourTime = new Date(data.hourly.time[i])
    const hour = hourTime.getHours()

    if (hour > currentHour || (hour === 0 && currentHour === 23)) {
      if (forecast.length < 3) {
        forecast.push({
          time: formatTime(data.hourly.time[i]),
          temperature: Math.round(data.hourly.temperature_2m[i]),
          pressure: Math.round(data.hourly.surface_pressure[i]),
          humidity: data.hourly.relative_humidity_2m[i],
          weatherCode: data.hourly.weather_code[i]
        })
      }
    }
  }

  // 如果不足3个，从前面补充
  while (forecast.length < 3 && data.hourly.time.length > 3) {
    const index = data.hourly.time.length - 3 + forecast.length
    if (index >= 0 && index < data.hourly.time.length) {
      forecast.push({
        time: formatTime(data.hourly.time[index]),
        temperature: Math.round(data.hourly.temperature_2m[index]),
        pressure: Math.round(data.hourly.surface_pressure[index]),
        humidity: data.hourly.relative_humidity_2m[index],
        weatherCode: data.hourly.weather_code[index]
      })
    }
  }

  return {
    current,
    forecast,
    location: LOCATION_NAME,
    updateTime: new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  }
}

export { getWeatherIconName, getWeatherDescription }
