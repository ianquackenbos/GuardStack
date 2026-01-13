import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'GuardStack',
      fileName: (format) => `guardstack.${format}.js`,
    },
    rollupOptions: {
      external: ['vue', 'vue-router', 'pinia', '@rancher/shell'],
      output: {
        globals: {
          vue: 'Vue',
          'vue-router': 'VueRouter',
          pinia: 'Pinia',
          '@rancher/shell': 'RancherShell',
        },
      },
    },
  },
  server: {
    port: 8005,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
