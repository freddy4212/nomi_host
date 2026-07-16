import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { useI18n } from './composables/useI18n'

// 開機時從後端 config.yaml 讀取語言設定（config.yaml 為單一真實來源；讀取前先用 localStorage 快取顯示）
useI18n().loadLocaleFromBackend()

createApp(App).mount('#app')
