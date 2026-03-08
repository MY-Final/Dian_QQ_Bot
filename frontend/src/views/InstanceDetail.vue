<script setup lang="ts">
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getErrorMessage, instanceApi, type Instance } from '../api'
import { useInstanceStore } from '../stores/instance'
import ConfirmModal from '../components/ui/ConfirmModal.vue'
import Toast from '../components/ui/Toast.vue'
import { useToast } from '@/composables/useToast'
import { useUiPreferences } from '@/composables/useUiPreferences'

const route = useRoute()
const router = useRouter()
const store = useInstanceStore()
const toast = useToast()
const { preferences } = useUiPreferences()

const instance = ref<Instance | null>(null)
const logs = ref('')
const loading = ref(true)
const logsLoading = ref(false)
const actionLoading = ref(false)
const actionType = ref<'start' | 'stop' | 'restart' | null>(null)

// 实时日志相关
const isRealtime = ref(false)
const realtimeInterval = ref<number | null>(null)
const logsContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
const logLines = ref(preferences.value.defaultLogLines)
const logCursor = ref(0)

const instanceId = computed(() => route.params.id as string)

// Confirm modal state
const confirmModal = ref({
  show: false,
  title: '',
  message: '',
  type: 'warning' as 'danger' | 'warning' | 'info',
  confirmText: '确认',
  requireText: '',
  requireTextPlaceholder: '请输入实例名称',
  action: null as (() => Promise<void>) | null,
  loading: false,
})

onMounted(async () => {
  await fetchInstance()
  // 如果实例正在运行，默认开启实时日志
  if (instance.value?.status === 'running') {
    resetLogCursor()
    await fetchLogs()
    toggleRealtime(true)
  }
})

onUnmounted(() => {
  stopRealtime()
})

// 监听实例状态变化，如果停止则暂停实时刷新
watch(() => instance.value?.status, (newStatus) => {
  if (newStatus !== 'running' && isRealtime.value) {
    stopRealtime()
  }
})

async function fetchInstance() {
  loading.value = true
  try {
    const response = await instanceApi.get(instanceId.value)
    instance.value = response.data.data || null
  } catch (error) {
    toast.error(getErrorMessage(error, '获取实例详情失败'))
  } finally {
    loading.value = false
  }
}

async function fetchLogs() {
  if (!instanceId.value) return
  logsLoading.value = true
  try {
    const response = await instanceApi.logs(instanceId.value, logLines.value, logCursor.value)
    const logsPayload = response.data.data

    if (!logsPayload) {
      logs.value = logs.value || '暂无日志'
      return
    }

    if (logCursor.value === 0) {
      logs.value = logsPayload.logs || '暂无日志'
    } else if (logsPayload.logs) {
      logs.value = logs.value ? `${logs.value}\n${logsPayload.logs}` : logsPayload.logs
    }

    logCursor.value = logsPayload.next_cursor

    // 自动滚动到底部
    if (autoScroll.value && logsContainer.value) {
      setTimeout(() => {
        if (logsContainer.value) {
          logsContainer.value.scrollTop = logsContainer.value.scrollHeight
        }
      }, 100)
    }
  } catch {
    logs.value = '获取日志失败'
    toast.error('获取日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 开启/关闭实时日志
function toggleRealtime(enable: boolean) {
  if (enable) {
    if (instance.value?.status !== 'running') {
      toast.warning('容器未运行，无法开启实时日志')
      return
    }
    isRealtime.value = true
    // 立即刷新一次
    fetchLogs()
    // 每 3 秒刷新一次
    realtimeInterval.value = window.setInterval(() => {
      if (!logsLoading.value) {
        fetchLogs()
      }
    }, preferences.value.logRefreshIntervalMs)
    toast.success(`已开启实时日志（每 ${Math.round(preferences.value.logRefreshIntervalMs / 1000)} 秒刷新）`)
  } else {
    stopRealtime()
  }
}

function stopRealtime() {
  isRealtime.value = false
  if (realtimeInterval.value) {
    clearInterval(realtimeInterval.value)
    realtimeInterval.value = null
  }
}

function resetLogCursor() {
  logCursor.value = 0
}

async function reloadLogs() {
  resetLogCursor()
  await fetchLogs()
}

async function startInstance() {
  if (!instance.value) return
  actionLoading.value = true
  actionType.value = 'start'
  try {
    const response = await instanceApi.start(instanceId.value)
    if (response.data.success && response.data.data) {
      instance.value = response.data.data
      toast.success(`实例 "${instance.value.name}" 启动成功`)
      await store.fetchInstances(true)
      // 启动成功后自动开启实时日志
      setTimeout(() => {
        reloadLogs()
        toggleRealtime(true)
      }, 1000)
    } else {
      toast.error(response.data.message || '启动失败')
    }
  } catch (error) {
    toast.error(getErrorMessage(error, '启动实例失败'))
  } finally {
    actionLoading.value = false
    actionType.value = null
  }
}

async function stopInstance() {
  if (!instance.value) return
  showConfirm({
    title: '停止实例',
    message: `确定要停止实例 "${instance.value.name}" 吗？正在运行的服务将会中断。`,
    type: 'warning',
    confirmText: '停止',
    action: async () => {
      actionLoading.value = true
      actionType.value = 'stop'
      try {
        const response = await instanceApi.stop(instanceId.value)
        if (response.data.success && response.data.data && instance.value) {
          instance.value = response.data.data
          toast.success(`实例 "${instance.value.name}" 已停止`)
          await store.fetchInstances(true)
        } else {
          toast.error(response.data.message || '停止失败')
        }
      } catch (error) {
        toast.error(getErrorMessage(error, '停止实例失败'))
      } finally {
        actionLoading.value = false
        actionType.value = null
      }
    },
  })
}

async function restartInstance() {
  if (!instance.value) return
  showConfirm({
    title: '重启实例',
    message: `确定要重启实例 "${instance.value.name}" 吗？服务将会短暂中断。`,
    type: 'warning',
    confirmText: '重启',
    action: async () => {
      actionLoading.value = true
      actionType.value = 'restart'
      try {
        const response = await instanceApi.restart(instanceId.value)
        if (response.data.success && response.data.data && instance.value) {
          instance.value = response.data.data
          toast.success(`实例 "${instance.value.name}" 重启成功`)
          await store.fetchInstances(true)
        } else {
          toast.error(response.data.message || '重启失败')
        }
      } catch (error) {
        toast.error(getErrorMessage(error, '重启实例失败'))
      } finally {
        actionLoading.value = false
        actionType.value = null
      }
    },
  })
}

async function deleteInstance() {
  if (!instance.value) return
  showConfirm({
    title: '删除实例',
    message: `确定要删除实例 "${instance.value.name}" 吗？此操作不可恢复，所有数据将被永久删除。`,
    type: 'danger',
    confirmText: '删除',
    requireText: preferences.value.requireDeleteConfirmText ? instance.value.name : '',
    action: async () => {
      try {
        const response = await instanceApi.delete(instanceId.value)
        if (response.data.success) {
          toast.success(`实例 "${instance.value?.name}" 已删除`)
          await store.fetchInstances(true)
          router.push('/')
        } else {
          toast.error(response.data.message || '删除失败')
        }
      } catch (error) {
        toast.error(getErrorMessage(error, '删除实例失败'))
      }
    },
  })
}

function showConfirm(options: {
  title: string
  message: string
  type?: 'danger' | 'warning' | 'info'
  confirmText?: string
  requireText?: string
  action: () => Promise<void>
}) {
  confirmModal.value = {
    show: true,
    title: options.title,
    message: options.message,
    type: options.type || 'warning',
    confirmText: options.confirmText || '确认',
    requireText: options.requireText || '',
    requireTextPlaceholder: options.requireText ? '请输入实例名称后确认' : '请输入确认文本',
    action: options.action,
    loading: false,
  }
}

function closeConfirm() {
  confirmModal.value.show = false
  confirmModal.value.action = null
  confirmModal.value.loading = false
  confirmModal.value.requireText = ''
}

async function handleConfirm(_confirmText: string) {
  if (confirmModal.value.action) {
    confirmModal.value.loading = true
    try {
      await confirmModal.value.action()
      closeConfirm()
    } catch {
      toast.error('操作执行失败，请重试')
    } finally {
      confirmModal.value.loading = false
    }
  }
}

function goBack() {
  router.push('/')
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return dateStr
  }
}

function formatProtocol(protocol: string): string {
  const map: Record<string, string> = {
    'napcat': 'NapCat',
    'llonebot': 'LLOneBot',
    'custom': '自定义',
  }
  return map[protocol] || protocol?.toUpperCase() || '-'
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    'running': '运行中',
    'stopped': '已停止',
    'created': '已创建',
    'error': '异常',
  }
  return map[status] || status || '未知'
}

function getStatusClass(status: string): string {
  const map: Record<string, string> = {
    'running': 'bg-green-100 text-green-700',
    'stopped': 'bg-yellow-100 text-yellow-700',
    'created': 'bg-blue-100 text-blue-700',
    'error': 'bg-red-100 text-red-700',
  }
  return map[status] || 'bg-gray-100 text-gray-700'
}

function getStatusDotClass(status: string): string {
  const map: Record<string, string> = {
    'running': 'bg-green-500',
    'stopped': 'bg-yellow-500',
    'created': 'bg-blue-500',
    'error': 'bg-red-500',
  }
  return map[status] || 'bg-gray-500'
}

// 复制日志到剪贴板
async function copyLogs() {
  try {
    await navigator.clipboard.writeText(logs.value)
    toast.success('日志已复制到剪贴板')
  } catch {
    toast.error('复制失败')
  }
}

// 清空日志显示
function clearLogs() {
  logs.value = ''
  resetLogCursor()
}
</script>

<template>
  <!-- Header -->
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center">
      <button @click="goBack" class="text-gray-500 hover:text-gray-700 mr-3 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <span class="font-medium text-gray-900">实例详情</span>
    </div>
    <button
      @click="fetchInstance"
      :disabled="loading"
      class="text-gray-500 hover:text-pink-500 transition-colors disabled:opacity-50"
      title="刷新"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="{ 'animate-spin': loading }">
        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
        <path d="M3 3v5h5"/>
        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
        <path d="M16 21h5v-5"/>
      </svg>
    </button>
  </header>

  <!-- Main Content -->
  <main class="flex-1 p-6 overflow-auto">
    <div class="max-w-4xl mx-auto space-y-6">
      <!-- Loading -->
      <div v-if="loading" class="text-center py-12 text-gray-400">
        <div class="flex items-center justify-center">
          <svg class="animate-spin h-6 w-6 text-pink-500 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          加载中...
        </div>
      </div>

      <!-- Instance Info -->
      <template v-else-if="instance">
        <!-- Basic Info Card -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ instance.name || '-' }}</h2>
              <p class="text-sm text-gray-500 mt-1">
                <span class="inline-flex items-center gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  QQ: {{ instance.qq_number || '-' }}
                </span>
              </p>
            </div>
            <Transition name="status" mode="out-in">
              <span
                :key="instance.status"
                :class="[
                  'px-3 py-1.5 text-sm rounded-full font-medium inline-flex items-center gap-1.5',
                  getStatusClass(instance.status)
                ]"
              >
                <span 
                  class="w-2 h-2 rounded-full"
                  :class="[
                    getStatusDotClass(instance.status),
                    { 'animate-pulse': instance.status === 'running' }
                  ]"
                ></span>
                {{ getStatusText(instance.status) }}
              </span>
            </Transition>
          </div>

          <!-- Info Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- 基本信息 -->
            <div class="space-y-4">
              <h3 class="text-sm font-medium text-gray-900 border-b pb-2">基本信息</h3>
              <div class="space-y-3">
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">实例 ID</p>
                  <p class="text-sm font-medium text-gray-900 font-mono">{{ instance.id || '-' }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">协议类型</p>
                  <p class="text-sm font-medium text-gray-900">{{ formatProtocol(instance.protocol) }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">容器名称</p>
                  <p class="text-sm font-medium text-gray-900 font-mono break-all">{{ instance.container_name || '-' }}</p>
                </div>
              </div>
            </div>

            <!-- 网络信息 -->
            <div class="space-y-4">
              <h3 class="text-sm font-semibold text-gray-900 border-b pb-2">网络信息</h3>
              <div class="space-y-3">
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">Web UI 端口</p>
                  <p class="text-sm font-medium text-gray-900 font-mono">{{ instance.port_web_ui || '-' }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">HTTP 端口</p>
                  <p class="text-sm font-medium text-gray-900 font-mono">{{ instance.port || '-' }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">WebSocket 端口</p>
                  <p class="text-sm font-medium text-gray-900 font-mono">{{ instance.port_ws || '-' }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">API 地址</p>
                  <p class="text-sm font-medium text-gray-900 font-mono text-xs break-all">
                    {{ instance.port ? `http://localhost:${instance.port}` : '-' }}
                  </p>
                </div>
              </div>
            </div>

            <!-- 存储信息 -->
            <div class="space-y-4">
              <h3 class="text-sm font-medium text-gray-900 border-b pb-2">存储信息</h3>
              <div class="space-y-3">
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">数据卷路径</p>
                  <p class="text-sm font-medium text-gray-900 font-mono text-xs break-all">{{ instance.volume_path || '-' }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">创建时间</p>
                  <p class="text-sm font-medium text-gray-900">{{ formatDate(instance.created_at) }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-0.5">更新时间</p>
                  <p class="text-sm font-medium text-gray-900">{{ formatDate(instance.updated_at) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Description -->
          <div v-if="instance.description" class="mt-6 pt-4 border-t">
            <p class="text-xs text-gray-500 mb-1">描述</p>
            <p class="text-sm text-gray-700">{{ instance.description }}</p>
          </div>

          <!-- Actions -->
          <div class="mt-6 pt-4 border-t flex flex-wrap gap-3">
            <button
              v-if="instance.status !== 'running'"
              @click="startInstance"
              :disabled="actionLoading"
              class="px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white text-sm rounded-lg transition-all inline-flex items-center gap-2 disabled:cursor-not-allowed active:scale-95"
            >
              <template v-if="actionLoading && actionType === 'start'">
                <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                启动中...
              </template>
              <template v-else>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                启动
              </template>
            </button>
            
            <template v-else>
              <button
                @click="stopInstance"
                :disabled="actionLoading"
                class="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 disabled:bg-yellow-300 text-white text-sm rounded-lg transition-all inline-flex items-center gap-2 disabled:cursor-not-allowed active:scale-95"
              >
                <template v-if="actionLoading && actionType === 'stop'">
                  <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  停止中...
                </template>
                <template v-else>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                  停止
                </template>
              </button>

              <button
                @click="restartInstance"
                :disabled="actionLoading"
                class="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white text-sm rounded-lg transition-all inline-flex items-center gap-2 disabled:cursor-not-allowed active:scale-95"
              >
                <template v-if="actionLoading && actionType === 'restart'">
                  <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  重启中...
                </template>
                <template v-else>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 21h5v-5"/></svg>
                  重启
                </template>
              </button>
            </template>

            <button
              @click="deleteInstance"
              :disabled="actionLoading"
              class="px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-red-300 text-white text-sm rounded-lg transition-all inline-flex items-center gap-2 disabled:cursor-not-allowed active:scale-95"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
              删除实例
            </button>
          </div>
        </div>

        <!-- Logs Card -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <!-- Header with controls -->
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <h3 class="font-medium text-gray-900">容器日志</h3>
              <!-- 实时状态指示器 -->
              <span 
                v-if="isRealtime" 
                class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                实时
              </span>
              <span v-else class="text-xs text-gray-400">
                (最近 {{ logLines }} 行)
              </span>
            </div>
            
            <!-- Controls -->
            <div class="flex items-center gap-2">
              <!-- 实时开关 -->
              <button
                @click="toggleRealtime(!isRealtime)"
                :disabled="instance.status !== 'running'"
                :class="[
                  'px-3 py-1.5 text-xs font-medium rounded-lg transition-all inline-flex items-center gap-1.5',
                  isRealtime 
                    ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                    : 'bg-green-100 text-green-700 hover:bg-green-200 disabled:bg-gray-100 disabled:text-gray-400'
                ]"
                :title="instance.status !== 'running' ? '容器未运行' : (isRealtime ? '关闭实时刷新' : '开启实时刷新')"
              >
                <svg v-if="isRealtime" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                {{ isRealtime ? '暂停' : '实时' }}
              </button>

              <!-- 行数选择 -->
              <div class="relative">
                <select 
                  v-model="logLines" 
                  @change="reloadLogs"
                  class="appearance-none px-3 py-1.5 pr-8 text-xs bg-white border border-gray-300 rounded-lg text-gray-700 font-medium focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent cursor-pointer hover:border-gray-400 transition-colors min-w-[70px]"
                >
                  <option :value="50">50 行</option>
                  <option :value="100">100 行</option>
                  <option :value="200">200 行</option>
                  <option :value="500">500 行</option>
                </select>
                <!-- 下拉箭头 -->
                <div class="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                </div>
              </div>

              <!-- 复制按钮 -->
              <button
                @click="copyLogs"
                :disabled="!logs"
                class="p-1.5 text-gray-500 hover:text-pink-500 transition-colors disabled:opacity-30"
                title="复制日志"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>

              <!-- 清空按钮 -->
              <button
                @click="clearLogs"
                :disabled="!logs"
                class="p-1.5 text-gray-500 hover:text-red-500 transition-colors disabled:opacity-30"
                title="清空显示"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
              </button>

              <!-- 刷新按钮 -->
              <button
                @click="reloadLogs"
                :disabled="logsLoading"
                class="text-pink-500 hover:text-pink-600 text-sm disabled:opacity-50 inline-flex items-center gap-1 transition-colors"
              >
                <svg v-if="!logsLoading" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 21h5v-5"/></svg>
                <svg v-else class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </button>
            </div>
          </div>
          
          <!-- Terminal -->
          <div class="bg-gray-900 rounded-lg overflow-hidden">
            <!-- Terminal Header -->
            <div class="flex items-center justify-between px-3 py-2 bg-gray-800 border-b border-gray-700">
              <div class="flex items-center gap-1.5">
                <div class="w-3 h-3 rounded-full bg-red-500"></div>
                <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div class="w-3 h-3 rounded-full bg-green-500"></div>
                <span class="ml-2 text-xs text-gray-400">Terminal</span>
              </div>
              <div class="flex items-center gap-2">
                <!-- 自动滚动开关 -->
                <label class="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer hover:text-gray-300">
                  <input 
                    type="checkbox" 
                    v-model="autoScroll" 
                    class="w-3 h-3 rounded border-gray-600 text-pink-500 focus:ring-pink-500"
                  />
                  自动滚动
                </label>
              </div>
            </div>
            
            <!-- Log Content -->
            <div 
              ref="logsContainer"
              class="p-4 overflow-auto max-h-96 text-xs leading-relaxed font-mono"
            >
              <div v-if="logs" class="space-y-0.5">
                <div 
                  v-for="(line, index) in logs.split('\n')" 
                  :key="index"
                  class="text-gray-300 hover:bg-gray-800 px-1 -mx-1 rounded"
                >
                  <template v-if="line.trim()">
                    <!-- 时间戳 -->
                    <span v-if="line.match(/^\d{4}-\d{2}-\d{2}/)" class="text-gray-500">
                      {{ line.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?/)?.[0] || '' }}
                    </span>
                    <!-- 日志级别 -->
                    <span 
                      v-if="line.includes('[INFO]') || line.includes('INFO')" 
                      class="text-blue-400 font-medium"
                    >
                      [INFO]
                    </span>
                    <span 
                      v-else-if="line.includes('[WARN]') || line.includes('WARN') || line.includes('WARNING')" 
                      class="text-yellow-400 font-medium"
                    >
                      [WARN]
                    </span>
                    <span 
                      v-else-if="line.includes('[ERROR]') || line.includes('ERROR')" 
                      class="text-red-400 font-medium"
                    >
                      [ERROR]
                    </span>
                    <span 
                      v-else-if="line.includes('[DEBUG]') || line.includes('DEBUG')" 
                      class="text-purple-400 font-medium"
                    >
                      [DEBUG]
                    </span>
                    <!-- 日志内容 -->
                    <span class="text-gray-300 whitespace-pre-wrap">{{ line.replace(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?\s*/, '').replace(/\[(INFO|WARN|ERROR|DEBUG)\]\s*/, '') }}</span>
                  </template>
                  <span v-else class="text-gray-600">&nbsp;</span>
                </div>
              </div>
              <div v-else class="text-gray-500 italic">
                点击"刷新"按钮或开启"实时"模式加载日志
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Error State -->
      <div v-else class="text-center py-12">
        <div class="text-gray-400 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="mx-auto"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <p class="text-gray-500">实例不存在或已被删除</p>
        <button @click="goBack" class="mt-4 text-pink-500 hover:text-pink-600 text-sm">返回列表</button>
      </div>
    </div>
  </main>

  <!-- Confirm Modal -->
  <ConfirmModal
    :show="confirmModal.show"
    :title="confirmModal.title"
    :message="confirmModal.message"
    :type="confirmModal.type"
    :confirm-text="confirmModal.confirmText"
    :require-text="confirmModal.requireText"
    :require-text-placeholder="confirmModal.requireTextPlaceholder"
    :loading="confirmModal.loading"
    @confirm="handleConfirm"
    @cancel="closeConfirm"
  />

  <!-- Toast -->
  <Toast />
</template>

<style scoped>
.status-enter-active,
.status-leave-active {
  transition: all 0.3s ease;
}

.status-enter-from {
  opacity: 0;
  transform: scale(0.9);
}

.status-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

/* Custom scrollbar for terminal */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #1f2937;
}

::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}
</style>
