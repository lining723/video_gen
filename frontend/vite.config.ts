import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3100,
    proxy: {
      '/api': {
        target: 'http://10.37.124.227:8100',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://10.37.124.227:8100',
        changeOrigin: true,
      },
    },
  },
})
