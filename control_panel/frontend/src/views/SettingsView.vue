<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Play, Square, Trash2, Sun, Moon } from 'lucide-vue-next'
import { useI18n } from '../composables/useI18n'
import { useTheme } from '../composables/useTheme'
import { buildWsUrl } from '../utils/backend'

const { t, locale, setLocale, supportedLocales, localeLabels } = useI18n()
const { theme, toggleTheme } = useTheme()
const emit = defineEmits(['status-update'])

const isRunning = ref(true) // Default assume running
const isDbLoading = ref(false)
let ws: WebSocket | null = null

const connectWebSocket = () => {
  // Use dedicated data channel for commands
  ws = new WebSocket(buildWsUrl('/ws/data'))
  
  ws.onopen = () => {
    console.log('Settings WS Connected (Data Channel)')
  }
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      // Handle status updates for the footer
      if (data.meta) {
        emit('status-update', data.meta)
      }

      if (data.type === 'frame_update') {
        // Update running state based on backend status
        if (data.status) {
            isRunning.value = data.status === 'running'
        }
      }
    } catch (e) {
      // ignore
    }
  }

  ws.onclose = () => {
    console.log('Settings WS Disconnected')
    emit('status-update', {
      tcp_connected: false,
      memory_connected: false,
      tcp_active: false,
      db_active: false,
      tcp_port: 0,
      db_port: 0
    })
  }
}

const toggleSystem = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  
  const command = isRunning.value ? 'stop_system' : 'start_system'
  ws.send(JSON.stringify({
    type: 'command',
    command: command
  }))
  
  // Optimistic update
  isRunning.value = !isRunning.value
}

const clearMemory = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  if (!confirm(t('settings.confirmClear'))) return
  
  isDbLoading.value = true
  ws.send(JSON.stringify({
    type: 'command',
    command: 'clear_memory'
  }))
  
  // 模擬載入效果
  setTimeout(() => {
    isDbLoading.value = false
    alert(t('settings.memoryCleared'))
  }, 1000)
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<template>
  <div class="h-full flex flex-col gap-6">
    <!-- Theme -->
    <section>
      <h3 class="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3 px-1">
        {{ t('settings.themeTitle') }}
      </h3>
      <div class="bg-bgLight rounded-xl border border-gray-700 p-4">
        <div class="flex items-center justify-between">
          <div>
            <div class="font-bold text-white">{{ theme === 'dark' ? t('settings.darkMode') : t('settings.lightMode') }}</div>
            <div class="text-xs text-gray-400 mt-1">
              {{ t('settings.themeDesc') }}
            </div>
          </div>

          <button
            @click="toggleTheme"
            class="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg border"
            :class="theme === 'dark' ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/50 hover:bg-indigo-500 hover:text-white' : 'bg-amber-500/20 text-amber-500 border-amber-500/50 hover:bg-amber-500 hover:text-white'"
            :title="theme === 'dark' ? t('settings.switchToLight') : t('settings.switchToDark')"
          >
            <Moon v-if="theme === 'dark'" class="w-5 h-5" />
            <Sun v-else class="w-5 h-5" />
          </button>
        </div>
      </div>
    </section>

    <!-- Language -->
    <section>
      <h3 class="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3 px-1">
        {{ t('common.language') }}
      </h3>
      <div class="bg-bgLight rounded-xl border border-gray-700 p-4">
        <div class="text-xs text-gray-400 mb-3">
          {{ t('settings.languageDesc') }}
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="loc in supportedLocales"
            :key="loc"
            @click="setLocale(loc)"
            class="flex-1 min-w-[90px] px-3 py-2 rounded-lg text-sm font-bold transition-all duration-200 border"
            :class="locale === loc
              ? 'bg-blue-500 text-white border-blue-500 shadow-lg'
              : 'bg-transparent text-gray-300 border-gray-600 hover:border-blue-500/60 hover:text-white'"
          >
            {{ localeLabels[loc] }}
          </button>
        </div>
      </div>
    </section>

    <!-- System Control -->
    <section>
      <h3 class="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3 px-1">
        {{ t('settings.systemControl') }}
      </h3>
      <div class="bg-bgLight rounded-xl border border-gray-700 p-4">
        <div class="flex items-center justify-between">
          <div>
            <div class="font-bold text-white">{{ t('settings.serviceTitle') }}</div>
            <div class="text-xs text-gray-400 mt-1">
              {{ isRunning ? t('settings.serviceRunning') : t('settings.serviceStopped') }}
            </div>
          </div>
          
          <button 
            @click="toggleSystem"
            class="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg"
            :class="isRunning ? 'bg-red-500/20 text-red-500 hover:bg-red-500 hover:text-white border border-red-500/50' : 'bg-green-500/20 text-green-500 hover:bg-green-500 hover:text-white border border-green-500/50'"
            :title="isRunning ? t('settings.stopService') : t('settings.startService')"
          >
            <Square v-if="isRunning" class="w-5 h-5 fill-current" />
            <Play v-else class="w-6 h-6 fill-current ml-1" />
          </button>
        </div>
      </div>
    </section>
    <!-- Database Management -->
    <section>
      <h3 class="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3 px-1">
        {{ t('settings.databaseTitle') }}
      </h3>
      <div class="bg-bgLight rounded-xl border border-gray-700 p-4">
        <div class="flex items-center justify-between">
          <div>
            <div class="font-bold text-white">{{ t('settings.databaseTitle') }}</div>
            <div class="text-xs text-gray-400 mt-1">
              {{ t('settings.databaseDesc') }}
            </div>
          </div>
          
          <button 
            @click="clearMemory"
            class="w-12 h-12 rounded-full bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white border border-red-500/50 flex items-center justify-center transition-all shadow-lg active:scale-95 disabled:opacity-30"
            :disabled="isDbLoading"
            :title="t('settings.clearMemory')"
          >
            <Trash2 class="w-5 h-5" :class="{'animate-pulse': isDbLoading}" />
          </button>
        </div>
      </div>
    </section>  </div>
</template>
