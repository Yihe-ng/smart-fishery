---
name: fish_guifan
description: "Smart Fishery frontend dev guide based on Art Design Pro. Invoke when developing Vue3/Element Plus/Vite/Tailwind CSS features, creating pages/components, configuring routes, using useTable/ArtTable/ArtForm/ArtSearchBar, or working on fish-disease/water-quality/growth-monitoring modules. Keywords: 智慧渔业, Art Design Pro, frontend-smart-fish, useTable, ArtTable"
---

# 智慧渔业前端开发规范 (基于 Art Design Pro)

> 本项目基于 [Art Design Pro](https://www.artd.pro/docs/zh/) 框架开发，使用 Vue3 + TypeScript + Vite + Tailwind CSS + Element Plus 技术栈

## 项目架构概览

```
frontend-smart-fish/
├── src/
│   ├── api/                 # API 接口
│   │   ├── fish-disease/    # 病害检测接口
│   │   ├── water-quality/   # 水质监测接口
│   │   ├── feeding/         # 投喂管理接口
│   │   └── ...
│   ├── components/          # 组件
│   │   ├── core/           # 核心组件（框架自带）
│   │   │   ├── tables/     # ArtTable 等表格组件
│   │   │   ├── forms/      # ArtForm, ArtSearchBar 等表单组件
│   │   │   └── layouts/    # 布局组件
│   │   └── business/       # 业务组件（自定义）
│   ├── composables/        # 组合式函数
│   │   └── useTable.ts     # 表格管理核心 hook
│   ├── views/              # 页面视图
│   │   ├── dashboard/      # 仪表盘
│   │   ├── fish-disease/   # 病害检测
│   │   ├── growth-monitoring/  # 生长监测
│   │   ├── monitoring/     # 监测中心
│   │   ├── feeding/        # 投喂管理
│   │   ├── production/     # 生产管理
│   │   └── ...
│   ├── router/             # 路由配置
│   ├── types/              # TypeScript 类型定义
│   └── utils/              # 工具函数
└── ...
```

## 核心技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript 超集
- **Vite** - 下一代前端构建工具
- **Element Plus** - 基于 Vue 3 的组件库
- **Tailwind CSS** - 原子化 CSS 框架
- **Pinia** - Vue 状态管理方案

## 主题配置系统

### CSS 变量定义

主题配置文件位于：`src/assets/styles/core/tailwind.css`

#### Light Mode 变量

```css
:root {
  /* 主题色 - OKLCH 格式 */
  --art-primary: oklch(0.7 0.23 260);      /* 主色 */
  --art-secondary: oklch(0.72 0.19 231.6); /* 次要色 */
  --art-error: oklch(0.73 0.15 25.3);      /* 错误色 */
  --art-info: oklch(0.58 0.03 254.1);      /* 信息色 */
  --art-success: oklch(0.78 0.17 166.1);   /* 成功色 */
  --art-warning: oklch(0.78 0.14 75.5);    /* 警告色 */
  --art-danger: oklch(0.68 0.22 25.3);     /* 危险色 */

  /* 灰度色系 */
  --art-gray-100: #f9fafb;  /* 最浅 */
  --art-gray-200: #f2f4f5;
  --art-gray-300: #e6eaeb;
  --art-gray-400: #dbdfe1;
  --art-gray-500: #949eb7;  /* 中等 */
  --art-gray-600: #7987a1;
  --art-gray-700: #4d5875;
  --art-gray-800: #383853;
  --art-gray-900: #323251;  /* 最深 */

  /* 边框颜色 */
  --art-card-border: rgba(0, 0, 0, 0.08);
  --default-border: #e2e8ee;
  --default-border-dashed: #dbdfe9;

  /* 背景颜色 */
  --default-bg-color: #fafbfc;   /* 页面底色 */
  --default-box-color: #ffffff;  /* 卡片/容器背景 */

  /* 交互状态颜色 */
  --art-hover-color: #edeff0;    /* 悬停状态 */
  --art-active-color: #f2f4f5;   /* 激活状态 */
  --art-el-active-color: #f2f4f5; /* Element 组件激活状态 */
}
```

#### Dark Mode 变量

```css
.dark {
  /* 灰度色系（暗黑模式下反转） */
  --art-gray-100: #110f0f;  /* 最深 */
  --art-gray-200: #17171c;
  --art-gray-300: #393946;
  --art-gray-400: #505062;
  --art-gray-500: #73738c;  /* 中等 */
  --art-gray-600: #8f8fa3;
  --art-gray-700: #ababba;
  --art-gray-800: #c7c7d1;
  --art-gray-900: #e3e3e8;  /* 最浅 */

  /* 边框颜色 */
  --art-card-border: rgba(255, 255, 255, 0.08);
  --default-border: rgba(255, 255, 255, 0.1);
  --default-border-dashed: #363843;

  /* 背景颜色 */
  --default-bg-color: #070707;   /* 页面底色 */
  --default-box-color: #161618;  /* 卡片/容器背景 */

  /* 交互状态颜色 */
  --art-hover-color: #252530;    /* 悬停状态 */
  --art-active-color: #202226;   /* 激活状态 */
  --art-el-active-color: #2e2e38; /* Element 组件激活状态 */
}
```

### Tailwind 工具类使用

#### 颜色工具类

```vue
<!-- 文字颜色 -->
<div class="text-g-100">最浅文字</div>
<div class="text-g-500">中等文字</div>
<div class="text-g-900">最深文字</div>

<!-- 背景颜色 -->
<div class="bg-box">卡片背景</div>
<div class="bg-hover-color">悬停背景</div>
<div class="bg-active-color">激活背景</div>

<!-- 边框 -->
<div class="border-full-d">完整边框</div>
<div class="border-b-d">底部边框</div>
<div class="border-t-d">顶部边框</div>

<!-- 主题色 -->
<div class="bg-primary text-white">主题色背景</div>
<div class="text-primary">主题色文字</div>
<div class="text-success">成功色</div>
<div class="text-warning">警告色</div>
<div class="text-error">错误色</div>
```

#### CSS 变量直接使用

```css
/* 文字颜色 */
color: var(--art-gray-100);
color: var(--art-gray-900);

/* 边框 */
border: 1px solid var(--default-border);
border: 1px solid var(--default-border-dashed);

/* 背景颜色 */
background-color: var(--default-bg-color);  /* 页面底色 */
background-color: var(--default-box-color); /* 卡片/容器背景 */

/* 交互状态 */
background-color: var(--art-hover-color);   /* 悬停状态 */
background-color: var(--art-active-color);  /* 激活状态 */
```

#### Element Plus 主题色变体

系统自动生成 9 个不同深浅的主题色变体：

```css
/* 主题色变浅（数字越大越浅） */
background-color: var(--el-color-primary-light-1); /* 最深 */
background-color: var(--el-color-primary-light-5); /* 中等 */
background-color: var(--el-color-primary-light-9); /* 最浅 */

/* 主题色变深（数字越大越深） */
background-color: var(--el-color-primary-dark-1);
background-color: var(--el-color-primary-dark-5);
background-color: var(--el-color-primary-dark-9);
```

### 布局工具类

```vue
<!-- Flexbox 快捷类 -->
<div class="flex-c">    <!-- flex + items-center -->
<div class="flex-b">    <!-- flex + justify-between -->
<div class="flex-cc">   <!-- flex + items-center + justify-center -->
<div class="flex-cb">   <!-- flex + items-center + justify-between -->

<!-- 过渡动画 -->
<div class="tad-200">   <!-- transition-all duration-200 -->
<div class="tad-300">   <!-- transition-all duration-300 -->

<!-- 指针样式 -->
<div class="c-p">       <!-- cursor-pointer -->
```

## 系统配置

### 配置文件位置

- **系统设置默认值**：`src/config/setting.ts`
- **应用配置**：`src/config/index.ts`
- **组件配置**：`src/config/modules/component.ts`

### 系统设置默认值 (SETTING_DEFAULT_CONFIG)

```typescript
// src/config/setting.ts

export const SETTING_DEFAULT_CONFIG = {
  /** 菜单类型 */
  menuType: MenuTypeEnum.LEFT,              // LEFT | TOP | TOP_LEFT | DUAL_MENU
  /** 菜单展开宽度 */
  menuOpenWidth: 230,
  /** 菜单是否展开 */
  menuOpen: true,
  /** 双菜单是否显示文本 */
  dualMenuShowText: false,
  /** 系统主题类型 */
  systemThemeType: SystemThemeEnum.AUTO,    // LIGHT | DARK | AUTO
  /** 系统主题模式 */
  systemThemeMode: SystemThemeEnum.AUTO,
  /** 菜单风格 */
  menuThemeType: MenuThemeEnum.DESIGN,      // DESIGN | DARK | LIGHT
  /** 系统主题颜色 */
  systemThemeColor: AppConfig.systemMainColor[0],  // 默认蓝色 #5D87FF
  /** 是否显示菜单按钮 */
  showMenuButton: true,
  /** 是否显示快速入口 */
  showFastEnter: true,
  /** 是否显示刷新按钮 */
  showRefreshButton: true,
  /** 是否显示面包屑 */
  showCrumbs: true,
  /** 是否显示工作台标签 */
  showWorkTab: true,
  /** 是否显示语言切换 */
  showLanguage: true,
  /** 是否显示进度条 */
  showNprogress: false,
  /** 是否显示设置引导 */
  showSettingGuide: true,
  /** 是否显示水印 */
  watermarkVisible: false,
  /** 是否自动关闭 */
  autoClose: false,
  /** 是否唯一展开 */
  uniqueOpened: true,
  /** 是否色弱模式 */
  colorWeak: false,
  /** 边框模式 */
  boxBorderMode: true,
  /** 页面过渡效果 */
  pageTransition: 'slide-left',
  /** 标签页样式 */
  tabStyle: 'tab-default',
  /** 自定义圆角 */
  customRadius: '0.75',
  /** 容器宽度 */
  containerWidth: ContainerWidthEnum.FULL   // FULL | CENTER
}
```

### 系统主色配置

```typescript
// src/config/index.ts

systemMainColor: [
  "#5D87FF",  // 默认蓝
  "#B48DF3",  // 紫色
  "#1D84FF",  // 深蓝
  "#60C041",  // 绿色
  "#38C0FC",  // 青色
  "#F9901F",  // 橙色
  "#FF80C8"   // 粉色
]
```

### 菜单布局类型

```typescript
enum MenuTypeEnum {
  LEFT = 'left',           // 左侧菜单
  TOP = 'top',             // 顶部菜单
  TOP_LEFT = 'top-left',   // 混合菜单
  DUAL_MENU = 'dual-menu'  // 双列菜单
}
```

### 系统主题类型

```typescript
enum SystemThemeEnum {
  LIGHT = 'light',   // 亮色模式
  DARK = 'dark',     // 暗黑模式
  AUTO = 'auto'      // 跟随系统
}
```

### 菜单主题类型

```typescript
enum MenuThemeEnum {
  DESIGN = 'design',  // 设计风（默认）
  DARK = 'dark',      // 暗黑风
  LIGHT = 'light'     // 明亮风
}
```

## 开发规范

### 1. 页面开发规范

#### 文件位置
- 页面必须放在 `src/views/{模块名}/` 目录下
- 子页面放在 `src/views/{模块名}/{功能}/index.vue`
- 组件放在 `src/views/{模块名}/{功能}/components/` 目录

#### 页面模板结构
```vue
<template>
  <!-- 必须有单个根元素 -->
  <div class="page-container">
    <!-- 页面标题区 -->
    <div class="page-header">
      <div class="title-section">
        <ArtSvgIcon icon="ri:xxx-line" style="font-size: 32px; color: #409eff" />
        <h2>页面标题</h2>
      </div>
    </div>

    <!-- 页面内容区 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="8" :lg="6">
        <!-- 左侧内容 -->
      </el-col>
      <el-col :xs="24" :sm="24" :md="16" :lg="18">
        <!-- 右侧内容 -->
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { ElMessage } from 'element-plus'
  import type { XxxType } from '@/types/xxx'
  import { xxxApi } from '@/api/xxx'
  import XxxComponent from './components/XxxComponent.vue'

  defineOptions({ name: 'PageName' })

  // 状态定义
  const loading = ref(false)
  const data = reactive<XxxType>({...})

  // 方法定义
  const handleAction = async () => {
    try {
      loading.value = true
      const result = await xxxApi()
      // 处理结果
    } catch (err) {
      console.error('操作失败:', err)
      ElMessage.error('操作失败，请重试')
    } finally {
      loading.value = false
    }
  }
</script>

<style scoped>
  .page-container {
    padding: 20px;
  }
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  .title-section {
    display: flex;
    align-items: center;
    gap: 12px;
  }
</style>
```

### 2. 表格开发规范 (useTable + ArtTable)

#### useTable 组合式函数

`useTable` 是 Art Design Pro 提供的强大表格管理工具，整合了数据获取、分页、搜索等功能。

```vue
<template>
  <div>
    <!-- 搜索栏 -->
    <ArtSearchBar
      v-model="searchForm"
      :items="searchItems"
      @search="handleSearch"
      @reset="handleReset"
    />
    
    <!-- 表格 -->
    <ArtTable
      :loading="loading"
      :data="data"
      :columns="columns"
      :pagination="pagination"
      @pagination:size-change="handleSizeChange"
      @pagination:current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup lang="ts">
  import { useTable } from '@/composables/useTable'
  import { fetchGetUserList } from '@/api/system-manage'
  import ArtTable from '@/components/core/tables/art-table/index.vue'
  import ArtSearchBar from '@/components/core/forms/art-search-bar/index.vue'

  defineOptions({ name: 'UserList' })

  // 搜索表单
  const searchForm = reactive({
    name: '',
    email: ''
  })

  // 搜索项配置
  const searchItems = [
    { prop: 'name', label: '姓名', type: 'input' },
    { prop: 'email', label: '邮箱', type: 'input' }
  ]

  // 使用 useTable
  const {
    data,
    loading,
    columns,
    pagination,
    handleSizeChange,
    handleCurrentChange,
    handleSearch,
    handleReset
  } = useTable({
    core: {
      apiFn: fetchGetUserList,
      apiParams: {
        current: 1,
        size: 20
      },
      columnsFactory: () => [
        { prop: 'id', label: 'ID', width: 80 },
        { prop: 'name', label: '姓名' },
        { prop: 'email', label: '邮箱' },
        { 
          prop: 'actions', 
          label: '操作',
          type: 'button',
          buttons: [
            { type: 'primary', label: '编辑', onClick: (row) => handleEdit(row) },
            { type: 'danger', label: '删除', onClick: (row) => handleDelete(row) }
          ]
        }
      ]
    }
  })

  const handleEdit = (row: any) => {
    console.log('编辑', row)
  }

  const handleDelete = (row: any) => {
    console.log('删除', row)
  }
</script>
```

#### useTable 配置选项

```typescript
useTable({
  core: {
    apiFn: () => Promise,           // 数据获取函数
    apiParams: {},                  // 初始请求参数
    columnsFactory: () => [],       // 列配置工厂函数
    immediate: true,                // 是否立即执行查询
    cache: true                     // 是否启用缓存（LRU算法）
  },
  pagination: {
    enabled: true,                  // 是否启用分页
    pageSize: 20,                   // 每页条数
    pageSizes: [10, 20, 50, 100]    // 可选每页条数
  },
  search: {
    enabled: true,                  // 是否启用搜索
    transform: (form) => form       // 搜索参数转换
  }
})
```

### 3. 表单开发规范 (ArtForm)

```vue
<template>
  <ArtForm
    v-model="formData"
    :items="formItems"
    :rules="formRules"
    @submit="handleSubmit"
    @reset="handleReset"
  />
</template>

<script setup lang="ts">
  import { reactive } from 'vue'
  import ArtForm from '@/components/core/forms/art-form/index.vue'
  import type { FormItem } from '@/types/form'

  defineOptions({ name: 'UserForm' })

  const formData = reactive({
    name: '',
    email: '',
    status: 1
  })

  const formItems: FormItem[] = [
    { prop: 'name', label: '姓名', type: 'input', required: true },
    { prop: 'email', label: '邮箱', type: 'input', required: true },
    { 
      prop: 'status', 
      label: '状态', 
      type: 'select',
      options: [
        { label: '启用', value: 1 },
        { label: '禁用', value: 0 }
      ]
    }
  ]

  const formRules = {
    name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
    ]
  }

  const handleSubmit = async (form: any) => {
    console.log('提交表单', form)
  }

  const handleReset = () => {
    console.log('重置表单')
  }
</script>
```

### 4. 路由配置规范

#### 新增路由步骤
1. 在 `src/router/modules/` 下找到对应模块文件（如 fishery.ts）
2. 添加路由配置：

```typescript
{
  path: 'new-feature',
  name: 'NewFeature',
  component: '/模块名/功能名/index',
  meta: { 
    title: 'menus.xxx.title',      // i18n 键名
    icon: 'ri:xxx-line',           // Remix Icon
    keepAlive: true,               // 是否缓存
    roles: ['R_SUPER', 'R_ADMIN']  // 权限角色（可选）
  }
}
```

#### 路由配置要点
- `component` 路径以 `/views/` 为根，不需要写 `.vue` 后缀
- `name` 必须唯一，使用 PascalCase
- `path` 使用 kebab-case
- `meta.title` 使用 i18n 键名，在 `src/i18n/` 中定义

### 5. API 接口规范

#### 文件位置
- `src/api/{模块名}/index.ts` 或 `src/api/{模块名}/{功能}.ts`

#### 接口模板
```typescript
import type { XxxResponse, XxxParams } from '@/types/xxx'
import request from '@/utils/request'

/**
 * 获取XXX列表
 * @param params - 查询参数
 * @returns 列表数据
 */
export async function getXxxList(params: XxxParams): Promise<XxxResponse[]> {
  return request.get('/xxx/list', { params })
}

/**
 * 创建XXX
 * @param data - 创建数据
 * @returns 创建结果
 */
export async function createXxx(data: Partial<XxxResponse>): Promise<XxxResponse> {
  return request.post('/xxx/create', data)
}

/**
 * 更新XXX
 * @param id - 记录ID
 * @param data - 更新数据
 * @returns 更新结果
 */
export async function updateXxx(id: string, data: Partial<XxxResponse>): Promise<XxxResponse> {
  return request.put(`/xxx/update/${id}`, data)
}

/**
 * 删除XXX
 * @param id - 记录ID
 * @returns 删除结果
 */
export async function deleteXxx(id: string): Promise<void> {
  return request.delete(`/xxx/delete/${id}`)
}
```

#### 接口开发注意事项
- 必须添加 JSDoc 注释说明参数和返回值
- 使用 TypeScript 类型定义
- 接口返回格式：`{ code, msg, data }`
- 模拟数据需标注 `// TODO: [后端接入]`

### 6. 组件开发规范

#### 组件结构
```vue
<template>
  <div class="component-name">
    <!-- 组件内容 -->
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue'
  
  // Props 定义
  interface Props {
    title: string
    data?: any[]
    loading?: boolean
  }
  const props = withDefaults(defineProps<Props>(), {
    data: () => [],
    loading: false
  })

  // Emits 定义
  const emit = defineEmits<{
    click: [id: string]
    update: [value: any]
  }>()

  defineOptions({ name: 'ComponentName' })

  // 逻辑代码
</script>

<style scoped>
  .component-name {
    /* 样式 */
  }
</style>
```

### 7. 图标使用规范

```vue
<!-- Remix Icon -->
<ArtSvgIcon icon="ri:home-line" />
<ArtSvgIcon icon="ri:fish-line" style="font-size: 32px; color: #409eff" />

<!-- 带动画 -->
<ArtSvgIcon icon="ri:loader-4-line" class="animate-spin" />
```

常用渔业相关图标：
- `ri:fish-line` - 鱼类
- `ri:water-flash-line` - 水质
- `ri:microscope-line` - 检测
- `ri:scales-3-line` - 生长/称重
- `ri:hand-coin-line` - 投喂
- `ri:bar-chart-box-line` - 生产统计
- `ri:dashboard-line` - 仪表盘
- `ri:temp-hot-line` - 温度

### 8. 类型定义规范

#### 文件位置
- `src/types/{模块名}.ts`

#### 类型定义示例
```typescript
// src/types/fish-disease.ts

/** 病害检测结果 */
export interface DiseaseDetection {
  /** 病害类型 */
  class: string
  /** 置信度 0-1 */
  confidence: number
  /** 边界框 [x, y, width, height] */
  bbox: number[]
}

/** 检测响应 */
export interface DetectResponse {
  /** 检测到的病害列表 */
  detections: DiseaseDetection[]
  /** 处理时间(ms) */
  processTime?: number
}

/** 病害统计 */
export interface DiseaseStats {
  [key: string]: number
}
```

## 渔业业务模块指南

### 病害检测模块 (fish-disease)
- 位置：`src/views/fish-disease/`
- 功能：鱼类病害智能识别
- 主要组件：DetectControlPanel、DetectImageDisplay、DetectStatsTable

### 生长监测模块 (growth-monitoring)
- 位置：`src/views/growth-monitoring/`
- 功能：鱼类生长状况监测
- 主要组件：GrowthControlPanel、GrowthImageDisplay、GrowthResultCard

### 水质监测模块 (water-quality)
- 位置：`src/views/monitoring/water-quality/`
- 功能：水质参数实时监测
- API：`src/api/water-quality/index.ts`

### 投喂管理模块 (feeding)
- 位置：`src/views/feeding/`
- 功能：智能投喂控制
- API：`src/api/feeding/index.ts`

### 生产管理模块 (production)
- 位置：`src/views/production/`
- 功能：生产数据统计分析

## 常见问题及解决方案

### Q1: 页面切换空白
**原因**：组件没有单个根元素
**解决**：确保 `<template>` 下只有一个根 `<div>`

### Q2: 路由配置后菜单不显示
**原因**：未在 asyncRoutes.ts 中注册或权限配置错误
**解决**：
1. 检查 `src/router/modules/` 中的路由配置
2. 确认 `meta.roles` 包含当前用户角色

### Q3: API 请求失败
**原因**：接口地址错误或后端未启动
**解决**：
1. 检查 `.env` 中的 `VITE_API_BASE_URL`
2. 确认后端服务运行状态
3. 查看浏览器 Network 面板

### Q4: 图标不显示
**原因**：图标名称错误或离线图标未安装
**解决**：
1. 使用正确的 Remix Icon 名称（如 `ri:home-line`）
2. 如需离线使用，安装 `@iconify-json/ri`

### Q5: 样式不生效
**原因**：CSS 作用域或类名错误
**解决**：
1. 检查 `<style scoped>` 是否正确
2. 使用 Tailwind 工具类时注意拼写
3. 使用 CSS 变量时确认变量名正确
4. 参考 `src/assets/styles/core/tailwind.css` 中的变量定义

### Q6: useTable 数据不刷新
**原因**：缓存机制或参数未正确传递
**解决**：
1. 检查 `apiParams` 是否正确配置
2. 调用 `refresh()` 方法强制刷新
3. 如需禁用缓存，设置 `cache: false`

### Q7: 主题颜色不正确
**原因**：使用了错误的 CSS 变量或工具类
**解决**：
1. Light 模式使用 `--art-gray-100` 到 `--art-gray-900`（由浅到深）
2. Dark 模式下灰度色自动反转，`--art-gray-100` 变为最深色
3. 使用 Tailwind 工具类 `text-g-100` 到 `text-g-900` 自动适配 Dark 模式
4. 主题色使用 `var(--art-primary)` 或 `text-primary`

## 开发检查清单

新建功能时，请确认：

- [ ] 页面文件放在正确的 `src/views/{模块}/` 目录下
- [ ] 组件有单个根元素
- [ ] 路由配置在 `src/router/modules/` 中
- [ ] API 接口放在 `src/api/{模块}/` 中
- [ ] 类型定义在 `src/types/{模块}.ts` 中
- [ ] 使用 `defineOptions({ name: 'Xxx' })` 定义组件名
- [ ] 图标使用 Remix Icon（`ri:xxx-line`）
- [ ] 样式优先使用 Tailwind 工具类
- [ ] 添加必要的 JSDoc 注释
- [ ] 模拟数据标注 `// TODO: [后端接入]`
- [ ] 表格使用 useTable + ArtTable 组合
- [ ] 表单使用 ArtForm 组件
- [ ] 颜色使用正确的 CSS 变量或工具类

## Art Design Pro 参考文档

1. [官方文档首页](https://www.artd.pro/docs/zh/)
2. [开发必读文档](https://www.artd.pro/docs/zh/guide/must-read.html)
3. [Element Plus组件](https://www.artd.pro/docs/zh/guide/essentials/element-plus.html)
4. [路由和菜单](https://www.artd.pro/docs/zh/guide/essentials/route.html)
5. [主题配置](https://www.artd.pro/docs/zh/guide/essentials/theme.html)
6. [系统配置](https://www.artd.pro/docs/zh/guide/essentials/settings.html)
7. [权限管理](https://www.artd.pro/docs/zh/guide/in-depth/permission.html)
8. [useTable Hook](https://www.artd.pro/docs/zh/guide/hooks/use-table.html)
9. [ArtSearchBar组件](https://www.artd.pro/docs/zh/guide/components/art-search-bar.html)
