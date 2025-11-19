import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

import AutoImport from 'unplugin-auto-import/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
     imports: [
        {
          'naive-ui': ['useDialog', 'useMessage', 'useNotification', 'useLoadingBar', 'createDiscreteApi']
        }
      ],
      // vue3 组件 js 语句中自动引入组件
      resolvers: [NaiveUiResolver()]
    }),
    // vue3 组件中自动引入组件
    Components({
      resolvers: [NaiveUiResolver()]
    })
  ],
  server: {
    host: '0.0.0.0', // Allow access from LAN/phone
    port: 3777,
    strictPort: true,
    cors: true,
    proxy: {
      '^/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        // 不重写路径，保持 /api 前缀，因为后端 routes 都有 /api 前缀
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
})
