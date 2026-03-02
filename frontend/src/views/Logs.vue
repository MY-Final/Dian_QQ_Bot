<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { instanceApi } from '../api'

const route = useRoute()
const logs = ref('')
const loading = ref(false)

const instanceId = ref(route.query.id as string || '')

async function fetchLogs() {
  if (!instanceId.value) return
  loading.value = true
  try {
    const response = await instanceApi.logs(instanceId.value, 100)
    logs.value = response.data.logs || '暂无日志'
  } catch (e) {
    logs.value = '获取日志失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (instanceId.value) fetchLogs()
})
</script>

<template>
  <!-- Header -->
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center text-sm text-gray-500">
      <span class="font-medium">控制台</span>
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-2"><path d="m9 18 6-6-6-6"/></svg>
      <span class="font-medium text-gray-900">实时日志</span>
    </div>
    <button
      @click="fetchLogs"
      :disabled="loading"
      class="px-4 py-2 bg-pink-500 hover:bg-pink-600 disabled:bg-gray-300 text-white text-sm font-medium rounded-lg transition-colors flex items-center"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
      刷新
    </button>
  </header>

  <!-- Main Content -->
  <main class="flex-1 p-6 overflow-hidden">
    <div class="max-w-6xl mx-auto h-full flex flex-col">
      <div class="bg-white rounded-lg border border-gray-200 flex-1 flex flex-col overflow-hidden">
        <pre v-if="loading" class="p-4 text-gray-400">加载中...</pre>
        <pre v-else class="flex-1 p-4 text-sm text-green-600 font-mono overflow-auto whitespace-pre-wrap bg-gray-50 rounded">{{ logs || '暂无日志，请选择实例查看' }}</pre>
      </div>
    </div>
  </main>
</template>
