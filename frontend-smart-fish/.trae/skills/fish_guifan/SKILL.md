---
name: "frontend-smart-fish-docs"
description: "在修改frontend-smart-fish项目前必须阅读官方文档。在开始任何开发、修改、重构任务前立即调用。"
---

# frontend-smart-fish 文档阅读器

此skill确保AI助手在进行任何项目修改前，已经充分了解frontend-smart-fish框架的官方文档和最佳实践。

## 必读文档列表

在开始任何任务前，必须先阅读以下官方文档：

### 核心文档
1. [开发必读文档](https://www.artd.pro/docs/zh/guide/must-read.html) - 基础响应格式、菜单接口对接、表格分页、常见问题
2. [Element Plus组件](https://www.artd.pro/docs/zh/guide/essentials/element-plus.html) - 组件库使用说明
3. [路由和菜单](https://www.artd.pro/docs/zh/guide/essentials/route.html) - 静态路由、动态路由配置
4. [系统配置](https://www.artd.pro/docs/zh/guide/essentials/settings.html) - 系统信息、主题、菜单布局配置
5. [主题配置](https://www.artd.pro/docs/zh/guide/essentials/theme.html) - CSS变量、Tailwind工具类、颜色系统
6. [图标使用](https://www.artd.pro/docs/zh/guide/essentials/icon.html) - Iconify图标库、离线图标配置

### 高级文档
7. [环境变量](https://www.artd.pro/docs/zh/guide/essentials/env-variables.html) - 环境配置说明
8. [权限管理](https://www.artd.pro/docs/zh/guide/in-depth/permission.html) - 前端/后端权限模式
9. [useTable Hook](https://www.artd.pro/docs/zh/guide/hooks/use-table.html) - 表格分页、排序、筛选
10. [ArtSearchBar组件](https://www.artd.pro/docs/zh/guide/components/art-search-bar.html) - 搜索栏组件使用

## 使用时机

**必须在以下情况调用此skill：**
- 开始任何新功能开发前
- 修改路由配置前
- 调整主题或样式前
- 添加或修改菜单前
- 使用表格组件前
- 配置权限前
- 任何对项目结构的修改前

## 关键要点提醒

### 响应格式
- 默认返回 `{ code, msg, data }` 格式
- 网络请求默认返回data中的数据

### 路由配置
- 静态路由：登录页、404等公共页面
- 动态路由：根据权限动态生成
- 菜单接口对接：在.env中切换权限模式

### 页面开发
- 必须有单个根元素（避免路由切换空白）
- 在/src/views/目录下创建页面
- 在asyncRoutes.ts中注册路由

### 主题系统
- 使用CSS变量：`var(--art-primary)`
- Tailwind工具类：`text-g-900`, `bg-box`, `border-full-d`
- 支持Light/Dark模式自动适配

### 图标使用
- 使用Iconify：`<ArtSvgIcon icon="ri:home-line" />`
- 推荐Remix Icon图标库
- 离线图标需安装@iconify-json包

### 表格分页
- 配置文件：src/utils/table/tableConfig.ts
- 支持多种字段名映射
- 使用useTable组合式函数

## 开发规范

1. **代码风格**：遵循项目现有的代码规范
2. **组件使用**：优先使用Element Plus组件
3. **样式开发**：使用Tailwind CSS工具类
4. **图标选择**：统一使用Remix Icon
5. **路由注册**：在asyncRoutes.ts中配置
6. **权限控制**：根据角色配置meta.roles

## 常见问题

- **页面切换空白**：确保组件有单个根元素
- **点击菜单自动刷新**：在vite.config.ts中配置optimizeDeps.include
- **路由配置错误**：查看浏览器控制台错误提示

## 注意事项

- 生产环境打包约8.4MB（完整版）或4.7MB（精简版）
- 默认开启gzip压缩
- 开发环境首次使用组件库子模块会触发Vite依赖预构建
