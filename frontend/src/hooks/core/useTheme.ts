import { watch } from 'vue'
import { usePreferredDark } from '@vueuse/core'
import { SystemThemeEnum } from '@/enums/appEnum'
import { useSettingStore } from '@/store/modules/setting'
import { setElementThemeColor } from '@/utils/ui'

const HTML_DARK_CLASS = SystemThemeEnum.DARK

type ResolvedTheme = Exclude<SystemThemeEnum, SystemThemeEnum.AUTO>

function resolveTheme(themeMode: SystemThemeEnum, prefersDark: boolean): ResolvedTheme {
  if (themeMode === SystemThemeEnum.AUTO) {
    return prefersDark ? SystemThemeEnum.DARK : SystemThemeEnum.LIGHT
  }

  return themeMode
}

function applyThemeClass(theme: ResolvedTheme) {
  const root = document.documentElement
  const isDark = theme === SystemThemeEnum.DARK

  root.classList.toggle(HTML_DARK_CLASS, isDark)
  root.setAttribute('data-theme', theme)
  root.style.colorScheme = theme
}

function disableTransitions() {
  const style = document.createElement('style')
  style.setAttribute('id', 'disable-transitions')
  style.textContent = '* { transition: none !important; }'
  document.head.appendChild(style)
}

function enableTransitions() {
  document.getElementById('disable-transitions')?.remove()
}

function syncThemeState(theme: ResolvedTheme, themeColor: string) {
  applyThemeClass(theme)
  setElementThemeColor(themeColor, theme === SystemThemeEnum.DARK)
}

export function useTheme() {
  const settingStore = useSettingStore()
  const prefersDark = usePreferredDark()

  const setSystemTheme = (
    theme: ResolvedTheme,
    themeMode: SystemThemeEnum = theme
  ) => {
    disableTransitions()
    syncThemeState(theme, settingStore.systemThemeColor)
    settingStore.setSystemThemeState(theme, themeMode)

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        enableTransitions()
      })
    })
  }

  const setSystemAutoTheme = () => {
    setSystemTheme(resolveTheme(SystemThemeEnum.AUTO, prefersDark.value), SystemThemeEnum.AUTO)
  }

  const switchThemeStyles = (themeMode: SystemThemeEnum) => {
    if (themeMode === SystemThemeEnum.AUTO) {
      setSystemAutoTheme()
      return
    }

    setSystemTheme(themeMode)
  }

  return {
    setSystemTheme,
    setSystemAutoTheme,
    switchThemeStyles,
    prefersDark
  }
}

export function initializeTheme() {
  const settingStore = useSettingStore()
  const prefersDark = usePreferredDark()

  const applyThemeByMode = () => {
    const theme = resolveTheme(settingStore.systemThemeMode, prefersDark.value)
    syncThemeState(theme, settingStore.systemThemeColor)
    document.documentElement.style.setProperty('--custom-radius', `${settingStore.customRadius}rem`)
    settingStore.setSystemThemeState(theme, settingStore.systemThemeMode)
  }

  applyThemeByMode()

  watch(
    prefersDark,
    () => {
      if (settingStore.systemThemeMode === SystemThemeEnum.AUTO) {
        applyThemeByMode()
      }
    },
    { immediate: false }
  )
}
