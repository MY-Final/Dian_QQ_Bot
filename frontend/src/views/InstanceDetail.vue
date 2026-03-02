<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { instanceApi, type Instance } from '../api'

const route = useRoute()
const router = useRouter()

const instance = ref<Instance | null>(null)
const logs = ref('')
const loading = ref(true)
const logsLoading = ref(false)

const instanceId = computed(() => route.params.id as string)

onMounted(async () => {
  await fetchInstance()
})

async function fetchInstance() {
  loading.value = true
  try {
    const response = await instanceApi.get(instanceId.value)
    instance.value = response.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchLogs() {
  logsLoading.value = true
  try {
    const response = await instanceApi.logs(instanceId.value, 50)
    logs.value = response.data.logs || '暂无日志'
  } catch (e) {
    logs.value = '获取日志失败'
  } finally {
    logsLoading.value = false
  }
}

async function startInstance() {
  if (!instance.value) return
  try {
    const response = await instanceApi.start(instanceId.value)
    instance.value = response.data
  } catch (e) {
    console.error(e)
  }
}

async function stopInstance() {
  if (!instance.value) return
  try {
    const response = await instanceApi.stop(instanceId.value)
    instance.value = response.data
  } catch (e) {
    console.error(e)
  }
}

async function deleteInstance() {
  if (!confirm('确定要删除这个实例吗？')) return
  try {
    await instanceApi.delete(instanceId.value)
    router.push('/')
  } catch (e) {
    console.error(e)
  }
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <!-- Header -->
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center">
      <button @click="goBack" class="text-gray-500 hover:text-gray-700 mr-3">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <span class="font-medium text-gray-900">实例详情</span>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex-1 p-6 overflow-auto">
    <div class="max-w-4xl mx-auto">
      <!-- Loading -->
      <div v-if="loading" class="text-center py-12 text-gray-400">加载中...</div>

      <!-- Instance Info -->
      <div v-else-if="instance" class="space-y-4">
        <!-- Basic Info -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 class="text-lg font-semibold text-gray-900">{{ instance.name }}</h2>
              <p class="text-sm text-gray-500">QQ: {{ instance.qq_number }}</p>
            </div>
            <span
              :class="[
                'px-3 py-1 text-sm rounded-full',
                instance.status === 'running' ? 'bg-green-100 text-green-700' :
                instance.status === 'stopped' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-700'
              ]"
            >
              {{ instance.status === 'running' ? '运行中' : instance.status === 'stopped' ? '已停止' : '未知' }}
            </span>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p class="text-gray-500">协议</p>
              <p class="font-medium">{{ instance.protocol.toUpperCase() }}</p>
            </div>
            <div>
              <p class="text-gray-500">端口</p>
              <p class="font-medium">{{ instance.port }}</p>
            </div>
            <div>
              <p class="text-gray-500">容器名</p>
              <p class="font-medium">{{ instance.container_name }}</p>
            </div>
            <div>
              <p class="text-gray-500">创建时间</p>
              <p class="font-medium">{{ new Date(instance.created_at).toLocaleString() }}</p>
            </div>
          </div>

          <p v-if="instance.description" class="mt-4 text-gray-600">{{ instance.description }}</p>

          <!-- Actions -->
          <div class="mt-6 flex gap-3">
            <button
              v-if="instance.status !== 'running'"
              @click="startInstance"
              class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white text-sm rounded-lg"
            >
              启动
            </button>
            <button
              v-else
              @click="stopInstance"
              class="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white text-sm rounded-lg"
            >
              停止
            </button>
            <button
              @click="deleteInstance"
              class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg"
            >
              删除实例
            </button>
          </div>
        </div>

        <!-- Logs -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-medium text-gray-900">日志</h3>
            <button
              @click="fetchLogs"
              :disabled="logsLoading"
              class="text-pink-500 hover:text-pink-600 text-sm"
            >
              {{ logsLoading ? '加载中...' : '刷新' }}
            </button>
          </div>
          <pre class="bg-gray-50 p-4 rounded-lg text-sm font-mono overflow-auto max-h-64 whitespace-pre-wrap">{{ logs || '暂无日志' }}</pre>
        </div>
      </div>
    </div>
  </main>
</template>
