<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { getErrorMessage, instanceApi, type Instance } from '@/api'
import Toast from '@/components/ui/Toast.vue'
import { useToast } from '@/composables/useToast'
import { useUiPreferences } from '@/composables/useUiPreferences'

const route = useRoute()
const toast = useToast()
const { preferences } = useUiPreferences()

const instances = ref<Instance[]>([])
const selectedInstanceId = ref((route.query.id as string) || '')
const logs = ref('')
const loading = ref(false)
const logsLoading = ref(false)
const isRealtime = ref(false)
const autoScroll = ref(true)
const logLines = ref(preferences.value.defaultLogLines)
const logCursor = ref(0)
const logsContainer = ref<HTMLElement | null>(null)
const realtimeTimer = ref<number | null>(null)

const selectedInstance = computed(() => instances.value.find((item) => item.id === selectedInstanceId.value) || null)

async function fetchInstances(): Promise<void> {
  loading.value = true
  try {
    const response = await instanceApi.list()
    instances.value = response.data.data || []

    if (!selectedInstanceId.value) {
      const firstInstance = instances.value[0]
      if (firstInstance) {
        selectedInstanceId.value = firstInstance.id
      }
    }
  } catch (error) {
    toast.error(getErrorMessage(error, '加载实例列表失败'))
  } finally {
    loading.value = false
  }
}

function resetCursor(): void {
  logCursor.value = 0
}

async function fetchLogs(): Promise<void> {
  if (!selectedInstanceId.value) {
    logs.value = ''
    return
  }

  logsLoading.value = true
  try {
    const response = await instanceApi.logs(selectedInstanceId.value, logLines.value, logCursor.value)
    const payload = response.data.data
    if (!payload) {
      return
    }

    if (logCursor.value === 0) {
      logs.value = payload.logs || '暂无日志'
    } else if (payload.logs) {
      logs.value = logs.value ? `${logs.value}\n${payload.logs}` : payload.logs
    }

    logCursor.value = payload.next_cursor

    if (autoScroll.value && logsContainer.value) {
      setTimeout(() => {
        if (logsContainer.value) {
          logsContainer.value.scrollTop = logsContainer.value.scrollHeight
        }
      }, 0)
    }
  } catch (error) {
    logs.value = '获取日志失败'
    toast.error(getErrorMessage(error, '获取日志失败'))
  } finally {
    logsLoading.value = false
  }
}

async function reloadLogs(): Promise<void> {
  resetCursor()
  await fetchLogs()
}

function stopRealtime(): void {
  isRealtime.value = false
  if (realtimeTimer.value !== null) {
    clearInterval(realtimeTimer.value)
    realtimeTimer.value = null
  }
}

function toggleRealtime(enable: boolean): void {
  if (enable) {
    if (!selectedInstance.value || selectedInstance.value.status !== 'running') {
      toast.warning('请选择运行中的实例以开启实时日志')
      return
    }

    isRealtime.value = true
    void fetchLogs()
    realtimeTimer.value = window.setInterval(() => {
      if (!logsLoading.value) {
        void fetchLogs()
      }
    }, preferences.value.logRefreshIntervalMs)
  } else {
    stopRealtime()
  }
}

function onInstanceChange(): void {
  stopRealtime()
  void reloadLogs()
}

function onLogLineChange(): void {
  stopRealtime()
  void reloadLogs()
}

onMounted(async () => {
  await fetchInstances()
  await reloadLogs()
})

onUnmounted(() => {
  stopRealtime()
})
</script>

<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center text-sm text-gray-500">
      <span class="font-medium">控制台</span>
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-2"><path d="m9 18 6-6-6-6"/></svg>
      <span class="font-medium text-gray-900">实时日志</span>
    </div>
    <div class="flex items-center gap-2">
      <button
        class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
        :disabled="logsLoading"
        @click="reloadLogs"
      >刷新</button>
    </div>
  </header>

  <main class="flex-1 p-6 overflow-hidden">
    <div class="max-w-6xl mx-auto h-full flex flex-col gap-4">
      <div class="rounded-xl border border-slate-200 bg-white p-3 grid grid-cols-1 gap-3 md:grid-cols-4">
        <div class="md:col-span-2">
          <label class="block text-xs text-slate-500 mb-1">选择实例</label>
          <select
            v-model="selectedInstanceId"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
            :disabled="loading"
            @change="onInstanceChange"
          >
            <option value="">请选择实例</option>
            <option v-for="instance in instances" :key="instance.id" :value="instance.id">
              {{ instance.name }} ({{ instance.status }})
            </option>
          </select>
        </div>

        <div>
          <label class="block text-xs text-slate-500 mb-1">日志行数</label>
          <select
            v-model.number="logLines"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
            @change="onLogLineChange"
          >
            <option :value="50">50 行</option>
            <option :value="100">100 行</option>
            <option :value="200">200 行</option>
            <option :value="500">500 行</option>
          </select>
        </div>

        <div class="flex items-end gap-2">
          <button
            class="rounded-lg px-3 py-2 text-sm font-medium"
            :class="isRealtime ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'"
            @click="toggleRealtime(!isRealtime)"
          >{{ isRealtime ? '暂停实时' : '开启实时' }}</button>
          <label class="inline-flex items-center gap-1 text-xs text-slate-600">
            <input v-model="autoScroll" type="checkbox" /> 自动滚动
          </label>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-gray-200 flex-1 flex flex-col overflow-hidden">
        <div class="px-4 py-2 border-b border-slate-200 text-xs text-slate-500">
          {{ selectedInstance ? `${selectedInstance.name} · ${selectedInstance.status}` : '请选择实例查看日志' }}
        </div>
        <div ref="logsContainer" class="flex-1 p-4 text-sm text-emerald-600 font-mono overflow-auto whitespace-pre-wrap bg-slate-900">
          <pre v-if="logsLoading" class="text-slate-300">加载中...</pre>
          <pre v-else class="text-emerald-300">{{ logs || '暂无日志，请选择实例查看' }}</pre>
        </div>
      </div>
    </div>
  </main>

  <Toast />
</template>
