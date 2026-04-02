/**
 * 天气数据类型定义
 * @description 用于实时气象卡片的数据结构
 */

/** 当前天气数据 */
export interface CurrentWeather {
  /** 温度 (°C) */
  temperature: number
  /** 大气压 (hPa) */
  pressure: number
  /** 风速 (m/s) */
  windSpeed: number
  /** 相对湿度 (%) */
  humidity: number
  /** 天气代码 (WMO Weather interpretation codes) */
  weatherCode: number
}

/** 小时预报数据 */
export interface HourlyForecast {
  /** 时间 (HH:mm) */
  time: string
  /** 温度 (°C) */
  temperature: number
  /** 大气压 (hPa) */
  pressure: number
  /** 相对湿度 (%) */
  humidity: number
  /** 天气代码 */
  weatherCode: number
}

/** 气压风险等级 */
export interface PressureRisk {
  level: 'high' | 'medium' | 'low'
  text: string
  description: string
  feedingSuggestion: string
  pressure: number
}

/** 完整天气数据 */
export interface WeatherData {
  /** 当前天气 */
  current: CurrentWeather
  /** 未来3小时预报 */
  forecast: HourlyForecast[]
  /** 位置名称 */
  location: string
  /** 数据更新时间 (HH:mm) */
  updateTime: string
}

/** 后端天气API响应结构 */
export interface BackendWeatherData {
  current: CurrentWeather
  pressureRisk: PressureRisk
  location: string
  updateTime: string
}

/** Open-Meteo API 响应结构 */
export interface OpenMeteoResponse {
  current: {
    time: string
    interval: number
    temperature_2m: number
    relative_humidity_2m: number
    surface_pressure: number
    wind_speed_10m: number
    weather_code: number
  }
  hourly: {
    time: string[]
    temperature_2m: number[]
    surface_pressure: number[]
    relative_humidity_2m: number[]
    weather_code: number[]
  }
}
