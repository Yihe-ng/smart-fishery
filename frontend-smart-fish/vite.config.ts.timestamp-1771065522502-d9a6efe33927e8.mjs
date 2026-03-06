// vite.config.ts
import {
  defineConfig,
  loadEnv
} from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/vite@5.4.21_@types+node@20._688badd30b5bb45ca3bb3911580c3893/node_modules/vite/dist/node/index.js'
import vue from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/@vitejs+plugin-vue@5.2.4_vi_bdc1898136e34b3a6c5a97a360f8e4e3/node_modules/@vitejs/plugin-vue/dist/index.mjs'
import path from 'path'
import { fileURLToPath } from 'url'
import vueDevTools from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/vite-plugin-vue-devtools@7._ca8fa00e4923946f5023b04626cd10e8/node_modules/vite-plugin-vue-devtools/dist/vite.mjs'
import viteCompression from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/vite-plugin-compression@0.5_a569286b41e1e7784246041116bd69c6/node_modules/vite-plugin-compression/dist/index.mjs'
import Components from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/unplugin-vue-components@0.2_ab09b8999c3941217543558964236656/node_modules/unplugin-vue-components/dist/vite.js'
import AutoImport from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/unplugin-auto-import@0.17.8_a887b5208d1e68a4cd928e5f67cdd20f/node_modules/unplugin-auto-import/dist/vite.js'
import ElementPlus from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/unplugin-element-plus@0.8.0_rollup@4.52.3/node_modules/unplugin-element-plus/dist/vite.mjs'
import { ElementPlusResolver } from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/unplugin-vue-components@0.2_ab09b8999c3941217543558964236656/node_modules/unplugin-vue-components/dist/resolvers.js'
import tailwindcss from 'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/node_modules/.pnpm/@tailwindcss+vite@4.1.14_vi_7f843fd8d301ffc8247fa0c362e53721/node_modules/@tailwindcss/vite/dist/index.mjs'
let __vite_injected_original_dirname =
  'D:\\\u6587\u4EF6\\\u6613\u627E\u7684\u6587\u4EF6\\\u667A\u6167\u6E14\u4E1A\\code\\frontend-smart-fish'
let __vite_injected_original_import_meta_url =
  'file:///D:/%E6%96%87%E4%BB%B6/%E6%98%93%E6%89%BE%E7%9A%84%E6%96%87%E4%BB%B6/%E6%99%BA%E6%85%A7%E6%B8%94%E4%B8%9A/code/frontend-smart-fish/vite.config.ts'
let vite_config_default = ({ mode }) => {
  const root = process.cwd()
  const env = loadEnv(mode, root)
  const { VITE_VERSION, VITE_PORT, VITE_BASE_URL, VITE_API_URL, VITE_API_PROXY_URL } = env
  console.log(`\u{1F680} API_URL = ${VITE_API_URL}`)
  console.log(`\u{1F680} VERSION = ${VITE_VERSION}`)
  return defineConfig({
    define: {
      __APP_VERSION__: JSON.stringify(VITE_VERSION)
    },
    base: VITE_BASE_URL,
    server: {
      port: Number(VITE_PORT),
      proxy: {
        '/api': {
          target: VITE_API_PROXY_URL,
          changeOrigin: true
        }
      },
      host: true
    },
    // 路径别名
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', __vite_injected_original_import_meta_url)),
        '@views': resolvePath('src/views'),
        '@imgs': resolvePath('src/assets/images'),
        '@icons': resolvePath('src/assets/icons'),
        '@utils': resolvePath('src/utils'),
        '@stores': resolvePath('src/store'),
        '@styles': resolvePath('src/assets/styles')
      }
    },
    build: {
      target: 'es2015',
      outDir: 'dist',
      chunkSizeWarningLimit: 2e3,
      minify: 'terser',
      terserOptions: {
        compress: {
          // 生产环境去除 console
          drop_console: true,
          // 生产环境去除 debugger
          drop_debugger: true
        }
      },
      dynamicImportVarsOptions: {
        warnOnError: true,
        exclude: [],
        include: ['src/views/**/*.vue']
      }
    },
    plugins: [
      vue(),
      tailwindcss(),
      // 自动按需导入 API
      AutoImport({
        imports: ['vue', 'vue-router', 'pinia', '@vueuse/core'],
        dts: 'src/types/import/auto-imports.d.ts',
        resolvers: [ElementPlusResolver()],
        eslintrc: {
          enabled: true,
          filepath: './.auto-import.json',
          globalsPropValue: true
        }
      }),
      // 自动按需导入组件
      Components({
        dts: 'src/types/import/components.d.ts',
        resolvers: [ElementPlusResolver()]
      }),
      // 按需定制主题配置
      ElementPlus({
        useSource: true
      }),
      // 压缩
      viteCompression({
        verbose: false,
        // 是否在控制台输出压缩结果
        disable: false,
        // 是否禁用
        algorithm: 'gzip',
        // 压缩算法
        ext: '.gz',
        // 压缩后的文件名后缀
        threshold: 10240,
        // 只有大小大于该值的资源会被处理 10240B = 10KB
        deleteOriginFile: false
        // 压缩后是否删除原文件
      }),
      vueDevTools()
      // 打包分析
      // visualizer({
      //   open: true,
      //   gzipSize: true,
      //   brotliSize: true,
      //   filename: 'dist/stats.html' // 分析图生成的文件名及路径
      // }),
    ],
    // 依赖预构建：避免运行时重复请求与转换，提升首次加载速度
    optimizeDeps: {
      include: [
        'echarts/core',
        'echarts/charts',
        'echarts/components',
        'echarts/renderers',
        'xlsx',
        'xgplayer',
        'crypto-js',
        'file-saver',
        'vue-img-cutter',
        'element-plus/es',
        'element-plus/es/components/*/style/css',
        'element-plus/es/components/*/style/index'
      ]
    },
    css: {
      preprocessorOptions: {
        // sass variable and mixin
        scss: {
          additionalData: `
            @use "@styles/core/el-light.scss" as *; 
            @use "@styles/core/mixin.scss" as *;
          `
        }
      },
      postcss: {
        plugins: [
          {
            postcssPlugin: 'internal:charset-removal',
            AtRule: {
              charset: (atRule) => {
                if (atRule.name === 'charset') {
                  atRule.remove()
                }
              }
            }
          }
        ]
      }
    }
  })
}
function resolvePath(paths) {
  return path.resolve(__vite_injected_original_dirname, paths)
}
export { vite_config_default as default }
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJEOlxcXFxcdTY1ODdcdTRFRjZcXFxcXHU2NjEzXHU2MjdFXHU3Njg0XHU2NTg3XHU0RUY2XFxcXFx1NjY3QVx1NjE2N1x1NkUxNFx1NEUxQVxcXFxjb2RlXFxcXGZyb250ZW5kLXNtYXJ0LWZpc2hcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkQ6XFxcXFx1NjU4N1x1NEVGNlxcXFxcdTY2MTNcdTYyN0VcdTc2ODRcdTY1ODdcdTRFRjZcXFxcXHU2NjdBXHU2MTY3XHU2RTE0XHU0RTFBXFxcXGNvZGVcXFxcZnJvbnRlbmQtc21hcnQtZmlzaFxcXFx2aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vRDovJUU2JTk2JTg3JUU0JUJCJUI2LyVFNiU5OCU5MyVFNiU4OSVCRSVFNyU5QSU4NCVFNiU5NiU4NyVFNCVCQiVCNi8lRTYlOTklQkElRTYlODUlQTclRTYlQjglOTQlRTQlQjglOUEvY29kZS9mcm9udGVuZC1zbWFydC1maXNoL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnLCBsb2FkRW52IH0gZnJvbSAndml0ZSdcbmltcG9ydCB2dWUgZnJvbSAnQHZpdGVqcy9wbHVnaW4tdnVlJ1xuaW1wb3J0IHBhdGggZnJvbSAncGF0aCdcbmltcG9ydCB7IGZpbGVVUkxUb1BhdGggfSBmcm9tICd1cmwnXG5pbXBvcnQgdnVlRGV2VG9vbHMgZnJvbSAndml0ZS1wbHVnaW4tdnVlLWRldnRvb2xzJ1xuaW1wb3J0IHZpdGVDb21wcmVzc2lvbiBmcm9tICd2aXRlLXBsdWdpbi1jb21wcmVzc2lvbidcbmltcG9ydCBDb21wb25lbnRzIGZyb20gJ3VucGx1Z2luLXZ1ZS1jb21wb25lbnRzL3ZpdGUnXG5pbXBvcnQgQXV0b0ltcG9ydCBmcm9tICd1bnBsdWdpbi1hdXRvLWltcG9ydC92aXRlJ1xuaW1wb3J0IEVsZW1lbnRQbHVzIGZyb20gJ3VucGx1Z2luLWVsZW1lbnQtcGx1cy92aXRlJ1xuaW1wb3J0IHsgRWxlbWVudFBsdXNSZXNvbHZlciB9IGZyb20gJ3VucGx1Z2luLXZ1ZS1jb21wb25lbnRzL3Jlc29sdmVycydcbmltcG9ydCB0YWlsd2luZGNzcyBmcm9tICdAdGFpbHdpbmRjc3Mvdml0ZSdcbi8vIGltcG9ydCB7IHZpc3VhbGl6ZXIgfSBmcm9tICdyb2xsdXAtcGx1Z2luLXZpc3VhbGl6ZXInXG5cbmV4cG9ydCBkZWZhdWx0ICh7IG1vZGUgfTogeyBtb2RlOiBzdHJpbmcgfSkgPT4ge1xuICBjb25zdCByb290ID0gcHJvY2Vzcy5jd2QoKVxuICBjb25zdCBlbnYgPSBsb2FkRW52KG1vZGUsIHJvb3QpXG4gIGNvbnN0IHsgVklURV9WRVJTSU9OLCBWSVRFX1BPUlQsIFZJVEVfQkFTRV9VUkwsIFZJVEVfQVBJX1VSTCwgVklURV9BUElfUFJPWFlfVVJMIH0gPSBlbnZcblxuICBjb25zb2xlLmxvZyhgXHVEODNEXHVERTgwIEFQSV9VUkwgPSAke1ZJVEVfQVBJX1VSTH1gKVxuICBjb25zb2xlLmxvZyhgXHVEODNEXHVERTgwIFZFUlNJT04gPSAke1ZJVEVfVkVSU0lPTn1gKVxuXG4gIHJldHVybiBkZWZpbmVDb25maWcoe1xuICAgIGRlZmluZToge1xuICAgICAgX19BUFBfVkVSU0lPTl9fOiBKU09OLnN0cmluZ2lmeShWSVRFX1ZFUlNJT04pXG4gICAgfSxcbiAgICBiYXNlOiBWSVRFX0JBU0VfVVJMLFxuICAgIHNlcnZlcjoge1xuICAgICAgcG9ydDogTnVtYmVyKFZJVEVfUE9SVCksXG4gICAgICBwcm94eToge1xuICAgICAgICAnL2FwaSc6IHtcbiAgICAgICAgICB0YXJnZXQ6IFZJVEVfQVBJX1BST1hZX1VSTCxcbiAgICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWVcbiAgICAgICAgfVxuICAgICAgfSxcbiAgICAgIGhvc3Q6IHRydWVcbiAgICB9LFxuICAgIC8vIFx1OERFRlx1NUY4NFx1NTIyQlx1NTQwRFxuICAgIHJlc29sdmU6IHtcbiAgICAgIGFsaWFzOiB7XG4gICAgICAgICdAJzogZmlsZVVSTFRvUGF0aChuZXcgVVJMKCcuL3NyYycsIGltcG9ydC5tZXRhLnVybCkpLFxuICAgICAgICAnQHZpZXdzJzogcmVzb2x2ZVBhdGgoJ3NyYy92aWV3cycpLFxuICAgICAgICAnQGltZ3MnOiByZXNvbHZlUGF0aCgnc3JjL2Fzc2V0cy9pbWFnZXMnKSxcbiAgICAgICAgJ0BpY29ucyc6IHJlc29sdmVQYXRoKCdzcmMvYXNzZXRzL2ljb25zJyksXG4gICAgICAgICdAdXRpbHMnOiByZXNvbHZlUGF0aCgnc3JjL3V0aWxzJyksXG4gICAgICAgICdAc3RvcmVzJzogcmVzb2x2ZVBhdGgoJ3NyYy9zdG9yZScpLFxuICAgICAgICAnQHN0eWxlcyc6IHJlc29sdmVQYXRoKCdzcmMvYXNzZXRzL3N0eWxlcycpXG4gICAgICB9XG4gICAgfSxcbiAgICBidWlsZDoge1xuICAgICAgdGFyZ2V0OiAnZXMyMDE1JyxcbiAgICAgIG91dERpcjogJ2Rpc3QnLFxuICAgICAgY2h1bmtTaXplV2FybmluZ0xpbWl0OiAyMDAwLFxuICAgICAgbWluaWZ5OiAndGVyc2VyJyxcbiAgICAgIHRlcnNlck9wdGlvbnM6IHtcbiAgICAgICAgY29tcHJlc3M6IHtcbiAgICAgICAgICAvLyBcdTc1MUZcdTRFQTdcdTczQUZcdTU4ODNcdTUzQkJcdTk2NjQgY29uc29sZVxuICAgICAgICAgIGRyb3BfY29uc29sZTogdHJ1ZSxcbiAgICAgICAgICAvLyBcdTc1MUZcdTRFQTdcdTczQUZcdTU4ODNcdTUzQkJcdTk2NjQgZGVidWdnZXJcbiAgICAgICAgICBkcm9wX2RlYnVnZ2VyOiB0cnVlXG4gICAgICAgIH1cbiAgICAgIH0sXG4gICAgICBkeW5hbWljSW1wb3J0VmFyc09wdGlvbnM6IHtcbiAgICAgICAgd2Fybk9uRXJyb3I6IHRydWUsXG4gICAgICAgIGV4Y2x1ZGU6IFtdLFxuICAgICAgICBpbmNsdWRlOiBbJ3NyYy92aWV3cy8qKi8qLnZ1ZSddXG4gICAgICB9XG4gICAgfSxcbiAgICBwbHVnaW5zOiBbXG4gICAgICB2dWUoKSxcbiAgICAgIHRhaWx3aW5kY3NzKCksXG4gICAgICAvLyBcdTgxRUFcdTUyQThcdTYzMDlcdTk3MDBcdTVCRkNcdTUxNjUgQVBJXG4gICAgICBBdXRvSW1wb3J0KHtcbiAgICAgICAgaW1wb3J0czogWyd2dWUnLCAndnVlLXJvdXRlcicsICdwaW5pYScsICdAdnVldXNlL2NvcmUnXSxcbiAgICAgICAgZHRzOiAnc3JjL3R5cGVzL2ltcG9ydC9hdXRvLWltcG9ydHMuZC50cycsXG4gICAgICAgIHJlc29sdmVyczogW0VsZW1lbnRQbHVzUmVzb2x2ZXIoKV0sXG4gICAgICAgIGVzbGludHJjOiB7XG4gICAgICAgICAgZW5hYmxlZDogdHJ1ZSxcbiAgICAgICAgICBmaWxlcGF0aDogJy4vLmF1dG8taW1wb3J0Lmpzb24nLFxuICAgICAgICAgIGdsb2JhbHNQcm9wVmFsdWU6IHRydWVcbiAgICAgICAgfVxuICAgICAgfSksXG4gICAgICAvLyBcdTgxRUFcdTUyQThcdTYzMDlcdTk3MDBcdTVCRkNcdTUxNjVcdTdFQzRcdTRFRjZcbiAgICAgIENvbXBvbmVudHMoe1xuICAgICAgICBkdHM6ICdzcmMvdHlwZXMvaW1wb3J0L2NvbXBvbmVudHMuZC50cycsXG4gICAgICAgIHJlc29sdmVyczogW0VsZW1lbnRQbHVzUmVzb2x2ZXIoKV1cbiAgICAgIH0pLFxuICAgICAgLy8gXHU2MzA5XHU5NzAwXHU1QjlBXHU1MjM2XHU0RTNCXHU5ODk4XHU5MTREXHU3RjZFXG4gICAgICBFbGVtZW50UGx1cyh7XG4gICAgICAgIHVzZVNvdXJjZTogdHJ1ZVxuICAgICAgfSksXG4gICAgICAvLyBcdTUzOEJcdTdGMjlcbiAgICAgIHZpdGVDb21wcmVzc2lvbih7XG4gICAgICAgIHZlcmJvc2U6IGZhbHNlLCAvLyBcdTY2MkZcdTU0MjZcdTU3MjhcdTYzQTdcdTUyMzZcdTUzRjBcdThGOTNcdTUxRkFcdTUzOEJcdTdGMjlcdTdFRDNcdTY3OUNcbiAgICAgICAgZGlzYWJsZTogZmFsc2UsIC8vIFx1NjYyRlx1NTQyNlx1Nzk4MVx1NzUyOFxuICAgICAgICBhbGdvcml0aG06ICdnemlwJywgLy8gXHU1MzhCXHU3RjI5XHU3Qjk3XHU2Q0Q1XG4gICAgICAgIGV4dDogJy5neicsIC8vIFx1NTM4Qlx1N0YyOVx1NTQwRVx1NzY4NFx1NjU4N1x1NEVGNlx1NTQwRFx1NTQwRVx1N0YwMFxuICAgICAgICB0aHJlc2hvbGQ6IDEwMjQwLCAvLyBcdTUzRUFcdTY3MDlcdTU5MjdcdTVDMEZcdTU5MjdcdTRFOEVcdThCRTVcdTUwM0NcdTc2ODRcdThENDRcdTZFOTBcdTRGMUFcdTg4QUJcdTU5MDRcdTc0MDYgMTAyNDBCID0gMTBLQlxuICAgICAgICBkZWxldGVPcmlnaW5GaWxlOiBmYWxzZSAvLyBcdTUzOEJcdTdGMjlcdTU0MEVcdTY2MkZcdTU0MjZcdTUyMjBcdTk2NjRcdTUzOUZcdTY1ODdcdTRFRjZcbiAgICAgIH0pLFxuICAgICAgdnVlRGV2VG9vbHMoKVxuICAgICAgLy8gXHU2MjUzXHU1MzA1XHU1MjA2XHU2NzkwXG4gICAgICAvLyB2aXN1YWxpemVyKHtcbiAgICAgIC8vICAgb3BlbjogdHJ1ZSxcbiAgICAgIC8vICAgZ3ppcFNpemU6IHRydWUsXG4gICAgICAvLyAgIGJyb3RsaVNpemU6IHRydWUsXG4gICAgICAvLyAgIGZpbGVuYW1lOiAnZGlzdC9zdGF0cy5odG1sJyAvLyBcdTUyMDZcdTY3OTBcdTU2RkVcdTc1MUZcdTYyMTBcdTc2ODRcdTY1ODdcdTRFRjZcdTU0MERcdTUzQ0FcdThERUZcdTVGODRcbiAgICAgIC8vIH0pLFxuICAgIF0sXG4gICAgLy8gXHU0RjlEXHU4RDU2XHU5ODg0XHU2Nzg0XHU1RUZBXHVGRjFBXHU5MDdGXHU1MTREXHU4RkQwXHU4ODRDXHU2NUY2XHU5MUNEXHU1OTBEXHU4QkY3XHU2QzQyXHU0RTBFXHU4RjZDXHU2MzYyXHVGRjBDXHU2M0QwXHU1MzQ3XHU5OTk2XHU2QjIxXHU1MkEwXHU4RjdEXHU5MDFGXHU1RUE2XG4gICAgb3B0aW1pemVEZXBzOiB7XG4gICAgICBpbmNsdWRlOiBbXG4gICAgICAgICdlY2hhcnRzL2NvcmUnLFxuICAgICAgICAnZWNoYXJ0cy9jaGFydHMnLFxuICAgICAgICAnZWNoYXJ0cy9jb21wb25lbnRzJyxcbiAgICAgICAgJ2VjaGFydHMvcmVuZGVyZXJzJyxcbiAgICAgICAgJ3hsc3gnLFxuICAgICAgICAneGdwbGF5ZXInLFxuICAgICAgICAnY3J5cHRvLWpzJyxcbiAgICAgICAgJ2ZpbGUtc2F2ZXInLFxuICAgICAgICAndnVlLWltZy1jdXR0ZXInLFxuICAgICAgICAnZWxlbWVudC1wbHVzL2VzJyxcbiAgICAgICAgJ2VsZW1lbnQtcGx1cy9lcy9jb21wb25lbnRzLyovc3R5bGUvY3NzJyxcbiAgICAgICAgJ2VsZW1lbnQtcGx1cy9lcy9jb21wb25lbnRzLyovc3R5bGUvaW5kZXgnXG4gICAgICBdXG4gICAgfSxcbiAgICBjc3M6IHtcbiAgICAgIHByZXByb2Nlc3Nvck9wdGlvbnM6IHtcbiAgICAgICAgLy8gc2FzcyB2YXJpYWJsZSBhbmQgbWl4aW5cbiAgICAgICAgc2Nzczoge1xuICAgICAgICAgIGFkZGl0aW9uYWxEYXRhOiBgXG4gICAgICAgICAgICBAdXNlIFwiQHN0eWxlcy9jb3JlL2VsLWxpZ2h0LnNjc3NcIiBhcyAqOyBcbiAgICAgICAgICAgIEB1c2UgXCJAc3R5bGVzL2NvcmUvbWl4aW4uc2Nzc1wiIGFzICo7XG4gICAgICAgICAgYFxuICAgICAgICB9XG4gICAgICB9LFxuICAgICAgcG9zdGNzczoge1xuICAgICAgICBwbHVnaW5zOiBbXG4gICAgICAgICAge1xuICAgICAgICAgICAgcG9zdGNzc1BsdWdpbjogJ2ludGVybmFsOmNoYXJzZXQtcmVtb3ZhbCcsXG4gICAgICAgICAgICBBdFJ1bGU6IHtcbiAgICAgICAgICAgICAgY2hhcnNldDogKGF0UnVsZSkgPT4ge1xuICAgICAgICAgICAgICAgIGlmIChhdFJ1bGUubmFtZSA9PT0gJ2NoYXJzZXQnKSB7XG4gICAgICAgICAgICAgICAgICBhdFJ1bGUucmVtb3ZlKClcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH1cbiAgICAgICAgICB9XG4gICAgICAgIF1cbiAgICAgIH1cbiAgICB9XG4gIH0pXG59XG5cbmZ1bmN0aW9uIHJlc29sdmVQYXRoKHBhdGhzOiBzdHJpbmcpIHtcbiAgcmV0dXJuIHBhdGgucmVzb2x2ZShfX2Rpcm5hbWUsIHBhdGhzKVxufVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUFpWixTQUFTLGNBQWMsZUFBZTtBQUN2YixPQUFPLFNBQVM7QUFDaEIsT0FBTyxVQUFVO0FBQ2pCLFNBQVMscUJBQXFCO0FBQzlCLE9BQU8saUJBQWlCO0FBQ3hCLE9BQU8scUJBQXFCO0FBQzVCLE9BQU8sZ0JBQWdCO0FBQ3ZCLE9BQU8sZ0JBQWdCO0FBQ3ZCLE9BQU8saUJBQWlCO0FBQ3hCLFNBQVMsMkJBQTJCO0FBQ3BDLE9BQU8saUJBQWlCO0FBVnhCLElBQU0sbUNBQW1DO0FBQTRKLElBQU0sMkNBQTJDO0FBYXRQLElBQU8sc0JBQVEsQ0FBQyxFQUFFLEtBQUssTUFBd0I7QUFDN0MsUUFBTSxPQUFPLFFBQVEsSUFBSTtBQUN6QixRQUFNLE1BQU0sUUFBUSxNQUFNLElBQUk7QUFDOUIsUUFBTSxFQUFFLGNBQWMsV0FBVyxlQUFlLGNBQWMsbUJBQW1CLElBQUk7QUFFckYsVUFBUSxJQUFJLHVCQUFnQixZQUFZLEVBQUU7QUFDMUMsVUFBUSxJQUFJLHVCQUFnQixZQUFZLEVBQUU7QUFFMUMsU0FBTyxhQUFhO0FBQUEsSUFDbEIsUUFBUTtBQUFBLE1BQ04saUJBQWlCLEtBQUssVUFBVSxZQUFZO0FBQUEsSUFDOUM7QUFBQSxJQUNBLE1BQU07QUFBQSxJQUNOLFFBQVE7QUFBQSxNQUNOLE1BQU0sT0FBTyxTQUFTO0FBQUEs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
