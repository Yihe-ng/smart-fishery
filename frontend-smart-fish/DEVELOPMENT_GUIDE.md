# 石斑鱼智慧监测系统 - 后续开发接入文档

## 1. 技术栈说明
- **前端框架**: Vue 3.5+ (Composition API)
- **开发语言**: TypeScript
- **UI 组件库**: Element Plus
- **样式方案**: SCSS + Tailwind CSS
- **视频处理**: HLS.js
- **图标库**: Remix Icon (使用 `ri:` 前缀，已集成 `@iconify-json/ri` 支持离线显示)

## 2. API 接入指南
系统所有 API 定义在 `src/api/` 目录下，遵循 `BaseResponse` 格式：
```typescript
interface BaseResponse<T> {
  code: number; // 200 为成功
  msg: string;  // 错误信息
  data: T;      // 数据体
}
```

### 核心模块接入点：
- **水质监测**: `src/api/water-quality/index.ts`
- **病害识别**: `src/api/fish-disease/detect.ts`
- **精准投喂**: `src/api/feeding/index.ts`
- **设备告警**: `src/api/alert/index.ts`

## 3. 功能扩展说明

### 3.1 接入真实视频流
在 `src/views/dashboard/fishery-console/components/VideoPlayer.vue` 中修改 `src` 属性。系统目前使用 `HLS.js` 兼容常见的 M3U8 格式。

### 3.2 完善 AI 识别逻辑
病害识别的核心逻辑位于 `src/views/fish-disease/detect/index.vue`。
- 后端应返回 `DetectionResult` 类型的数组，包含病害类型、置信度和 `bbox` (坐标百分比)。
- 前端 `AIDetectionResult.vue` 会根据百分比坐标自动绘制识别框。

### 3.3 模糊 PID 算法对接
在 `src/api/feeding/index.ts` 中预留了 `updateFeedingConfig` 接口。后端应接收前端传参，并结合实时水质数据运行 PID 算法，将计算出的投喂指令发送至下位机。

## 4. 样式与主题
- 系统主色定义在 `src/config/index.ts` 中的 `systemMainColor` 第一项。
- 适配深色模式时，请优先使用 CSS 变量：
  - 背景色: `var(--art-bg-color)`
  - 容器色: `var(--default-box-color)`
  - 边框色: `var(--art-border-color)`

## 5. 打包与部署
```bash
# 安装依赖
pnpm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```
构建产物将位于 `dist/` 目录，可直接部署至 Nginx 等 Web 服务器。

---

## 6. 后端接口接入教程 (傻瓜式指南)

**写给接手开发的同学：**
目前系统中带有 `(模拟)` 字样的地方，以及代码中标记了 `// TODO: [后端接入]` 的地方，都需要你们修改成调用真实的后端 API。
别慌，按照下面的步骤一步步来就行！

### 步骤一：找到要修改的文件
在编辑器（VS Code）中全局搜索关键词：`TODO: [后端接入]`
你会看到类似这样的代码：
```typescript
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export function getSensorDevices(): Promise<SensorDevice[]> {
  // 模拟数据返回，请替换为 axios.get('/device/list')
  return Promise.resolve([ ... ])
}
```

### 步骤二：替换为真实请求
系统已经封装好了 `request` 工具（基于 axios），你只需要把 `Promise.resolve(...)` 删掉，换成 `request.get` 或 `request.post`。

#### 示例 1：获取数据 (GET 请求)
假设后端给的接口是 `/api/device/list`，你需要把代码改成：

```typescript
import request from '@/utils/http' // 1. 确保引入了 request

// 修改后的代码
export function getSensorDevices(): Promise<SensorDevice[]> {
  // 这里的 '/device/list' 要换成你们后端真实的接口地址
  return request.get({
    url: '/device/list'
  })
}
```

#### 示例 2：提交数据 (POST 请求)
假设后端接口是 `/api/feeding/config`，需要传配置参数：

```typescript
import request from '@/utils/http'

export function updateFeedingConfig(config: FeedingConfig): Promise<boolean> {
  return request.post({
    url: '/feeding/config',
    data: config // 把参数传进去
  })
}
```

### 步骤三：去掉页面上的 "(模拟)" 标记
接口接通后，记得去页面文件里把 `(模拟)` 这几个字删掉。
主要在 `src/views/dashboard/fishery-console/index.vue` 这个文件里。

### 常见问题 (Q&A)

**Q: 我怎么知道后端接口返回的数据格式对不对？**
A: 打开浏览器的开发者工具 (F12) -> Network (网络) -> 刷新页面。看接口请求的 `Response` (响应)。
前端需要的格式一般在 `src/types/` 目录下都有定义。如果后端返回的字段名和前端不一样（比如前端叫 `userName`，后端叫 `user_name`），你需要自己转换一下，或者让后端改。

**Q: 视频流怎么接？**
A: 找到 `src/views/dashboard/fishery-console/components/VideoPlayer.vue`，把里面的 `src` 换成后端给的 `.m3u8` 地址即可。

**Q: 跨域了怎么办 (CORS Error)？**
A: 这是后端要在服务器上配置的，或者你在本地开发时，在 `vite.config.ts` 里配置 proxy 代理。但最快的方法是**喊后端改**。


