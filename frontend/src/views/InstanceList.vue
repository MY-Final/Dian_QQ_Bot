<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useInstanceStore } from '../stores/instance'
import { type Instance } from '../api'
import Modal from '../components/ui/Modal.vue'
import ConfirmModal from '../components/ui/ConfirmModal.vue'
import Input from '../components/ui/Input.vue'
import Select from '../components/ui/Select.vue'
import Toast from '../components/ui/Toast.vue'
import { useToast } from '@/composables/useToast'
import { useDockerStatus } from '@/composables/useDockerStatus'

const router = useRouter()
const store = useInstanceStore()
const toast = useToast()

// 使用 Docker 状态 composable
const { dockerStatus, loading: dockerLoading, statusText, statusClass, dotClass, fetchDockerStatus } = useDockerStatus()

// Modal state
const showCreateModal = ref(false)

// Confirm modal state
const confirmModal = ref({
  show: false,
  title: '',
  message: '',
  type: 'warning' as 'danger' | 'warning' | 'info',
  confirmText: '确认',
  action: null as (() => Promise<void>) | null,
  loading: false,
})

// Form state
const formName = ref('dian-bot')
const formFramework = ref('napcat')
const formWebPort = ref(6099)
const formHttpPort = ref(3000)
const formWsPort = ref(3001)
const formUid = ref(1000)
const formGid = ref(1000)
const formLlPort = ref(3080)

const frameworkOptions = [
  { value: 'napcat', label: 'NapCat Docker' },
  { value: 'llonebot', label: 'LLOneBot' },
]

onMounted(() => {
  store.fetchInstances()
  fetchDockerStatus()
})

const dockerCommand = computed(() => {
  if (formFramework.value === 'napcat') {
    return `docker run -d \\
  --name ${formName.value} \\
  -e NAPCAT_GID=${formGid.value} \\
  -e NAPCAT_UID=${formUid.value} \\
  -p ${formHttpPort.value}:3000 \\
  -p ${formWsPort.value}:3001 \\
  -p ${formWebPort.value}:6099 \\
  --restart=always \\
  mlikiowa/napcat-docker:latest`
  } else {
    return `docker run -d \\
  --name ${formName.value} \\
  -p ${formLlPort.value}:3080 \\
  initialencounter/llonebot:latest`
  }
})

function openModal() {
  showCreateModal.value = true
}

function closeModal() {
  showCreateModal.value = false
}

async function handleCreate() {
  // 构建完整的请求体
  const createData: any = {
    name: formName.value,
    qq_number: '123456789',
    protocol: formFramework.value as 'napcat' | 'llonebot' | 'custom',
  }
  
  // 如果是 NapCat，添加端口和环境变量配置
  if (formFramework.value === 'napcat') {
    if (formWebPort.value) createData.port_web_ui = formWebPort.value
    if (formHttpPort.value) createData.port_http = formHttpPort.value
    if (formWsPort.value) createData.port_ws = formWsPort.value
    if (formUid.value) createData.napcat_uid = formUid.value
    if (formGid.value) createData.napcat_gid = formGid.value
  }
  
  const result = await store.createInstance(createData)
  if (result) {
    closeModal()
    toast.success(`实例 "${formName.value}" 创建成功！`)
  }
}

function goToDetail(id: string) {
  router.push(`/instance/${id}`)
}

// 显示确认弹窗
function showConfirm(options: {
  title: string
  message: string
  type?: 'danger' | 'warning' | 'info'
  confirmText?: string
  action: () => Promise<void>
}) {
  confirmModal.value = {
    show: true,
    title: options.title,
    message: options.message,
    type: options.type || 'warning',
    confirmText: options.confirmText || '确认',
    action: options.action,
    loading: false,
  }
}

function closeConfirm() {
  confirmModal.value.show = false
  confirmModal.value.action = null
  confirmModal.value.loading = false
}

async function handleConfirm() {
  if (confirmModal.value.action) {
    confirmModal.value.loading = true
    try {
      await confirmModal.value.action()
    } finally {
      confirmModal.value.loading = false
      closeConfirm()
    }
  }
}

// 停止实例
function handleStopInstance(instance: Instance) {
  showConfirm({
    title: '停止实例',
    message: `确定要停止实例 "${instance.name}" 吗？正在运行的服务将会中断。`,
    type: 'warning',
    confirmText: '停止',
    action: async () => {
      const success = await store.stopInstance(instance.id)
      if (success) {
        toast.success(`实例 "${instance.name}" 已停止`)
        await store.fetchInstances(true)
      } else {
        toast.error(store.error || '停止实例失败')
      }
    },
  })
}

// 删除实例
function handleDeleteInstance(instance: Instance) {
  showConfirm({
    title: '删除实例',
    message: `确定要删除实例 "${instance.name}" 吗？此操作不可恢复，所有数据将被永久删除。`,
    type: 'danger',
    confirmText: '删除',
    action: async () => {
      const success = await store.deleteInstance(instance.id)
      if (success) {
        toast.success(`实例 "${instance.name}" 已删除`)
        await store.fetchInstances(true)
      } else {
        toast.error(store.error || '删除实例失败')
      }
    },
  })
}

// 启动实例
async function handleStartInstance(instance: Instance) {
  const success = await store.startInstance(instance.id)
  if (success) {
    toast.success(`实例 "${instance.name}" 已启动`)
    await store.fetchInstances(true)
  } else {
    toast.error(store.error || '启动实例失败')
  }
}

// 刷新列表
async function handleRefresh() {
  await store.fetchInstances(true)
  toast.success('列表已刷新')
}
</script>

<template>
  <!-- Header -->
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center text-sm text-gray-500">
      <span class="font-medium">控制台</span>
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-2"><path d="m9 18 6-6-6-6"/></svg>
      <span class="font-medium text-gray-900">实例管理</span>
    </div>
    <div class="flex items-center space-x-3">
      <!-- Docker 状态信息 -->
      <div class="relative group">
        <button 
          @click="fetchDockerStatus"
          :disabled="dockerLoading"
          :class="['flex items-center px-3 py-1.5 rounded-lg border transition-all', 
            dockerLoading ? 'border-gray-300 bg-gray-50 text-gray-500' :
            dockerStatus.running ? 'border-green-200 bg-green-50 text-green-700 hover:bg-green-100' :
            'border-red-200 bg-red-50 text-red-700 hover:bg-red-100'
          ]"
          title="点击刷新 Docker 状态"
        >
          <span :class="['w-2 h-2 rounded-full mr-2', 
            dockerLoading ? 'bg-gray-400 animate-pulse' :
            dockerStatus.running ? 'bg-green-500' : 'bg-red-500'
          ]"></span>
          <span class="text-xs font-medium">
            {{ dockerLoading ? '检查中...' : dockerStatus.running ? 'Docker 已连接' : 'Docker 未连接' }}
          </span>
          <svg 
            v-if="dockerLoading" 
            class="animate-spin ml-2 h-3 w-3" 
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg 
            v-else
            xmlns="http://www.w3.org/2000/svg" 
            width="14" 
            height="14" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            stroke-width="2" 
            stroke-linecap="round" 
            stroke-linejoin="round" 
            class="ml-1.5"
          >
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 16h5v5"/>
          </svg>
        </button>
        
        <!-- 详情弹窗 -->
        <div class="absolute right-0 top-full mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 p-4 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
          <div class="space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-gray-100">
              <span class="text-xs font-medium text-gray-500">Docker 状态</span>
              <span :class="['px-2 py-0.5 text-xs rounded-full', 
                dockerStatus.running ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              ]">
                {{ dockerStatus.running ? '运行正常' : '未运行' }}
              </span>
            </div>
            
            <div class="space-y-2">
              <div class="flex items-start gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400 mt-0.5">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                  <line x1="8" y1="21" x2="16" y2="21"/>
                  <line x1="12" y1="17" x2="12" y2="21"/>
                </svg>
                <div class="flex-1">
                  <p class="text-xs text-gray-500">平台</p>
                  <p class="text-sm font-medium text-gray-900 capitalize">{{ dockerStatus.platform || '-' }}</p>
                </div>
              </div>
              
              <div class="flex items-start gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400 mt-0.5">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"/>
                </svg>
                <div class="flex-1">
                  <p class="text-xs text-gray-500">版本</p>
                  <p class="text-sm font-medium text-gray-900">{{ dockerStatus.version || '-' }}</p>
                </div>
              </div>
              
              <div class="flex items-start gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400 mt-0.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
                <div class="flex-1">
                  <p class="text-xs text-gray-500">状态信息</p>
                  <p class="text-sm text-gray-700">{{ dockerStatus.message || '-' }}</p>
                </div>
              </div>
            </div>
            
            <div class="pt-2 border-t border-gray-100">
              <p class="text-xs text-gray-400 text-center">点击按钮刷新状态</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex-1 p-6 overflow-auto">
    <div class="max-w-6xl mx-auto">
      <!-- Title -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-semibold text-gray-900">实例概览</h1>
          <p class="text-sm text-gray-500 mt-0.5">管理运行中的 QQ Bot 容器实例</p>
        </div>
        <div class="flex items-center gap-3">
          <button
            @click="handleRefresh"
            :disabled="store.loading"
            class="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors flex items-center disabled:opacity-50"
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              class="mr-2"
              :class="{ 'animate-spin': store.loading }"
            >
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5" transform="rotate(180 18.5 18.5)"/></svg>
            刷新
          </button>
          <button
            @click="openModal"
            class="px-4 py-2 bg-pink-500 hover:bg-pink-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/></svg>
            创建实例
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table class="w-full text-sm text-left">
          <thead class="bg-gray-50 text-xs font-medium text-gray-500 uppercase">
            <tr>
              <th class="px-6 py-3">实例名称</th>
              <th class="px-6 py-3">协议</th>
              <th class="px-6 py-3">状态</th>
              <th class="px-6 py-3 text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-if="store.loading" class="hover:bg-gray-50">
              <td colspan="4" class="px-6 py-8 text-center text-gray-400">
                <div class="flex items-center justify-center">
                  <svg class="animate-spin h-5 w-5 text-pink-500 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  加载中...
                </div>
              </td>
            </tr>
            <tr v-else-if="store.instances.length === 0" class="hover:bg-gray-50">
              <td colspan="4" class="px-6 py-8 text-center text-gray-400">
                <div class="text-2xl mb-2">🐱</div>
                <div>暂无实例</div>
                <div class="text-xs mt-1">点击"创建实例"开始</div>
              </td>
            </tr>
            <tr
              v-else
              v-for="instance in store.instances"
              :key="instance.id"
              class="hover:bg-gray-50 cursor-pointer transition-colors"
              @click="goToDetail(instance.id)"
            >
              <td class="px-6 py-4 font-medium text-gray-900">{{ instance.name }}</td>
              <td class="px-6 py-4">
                <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                  {{ instance.protocol.toUpperCase() }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span
                  :class="[
                    'px-2.5 py-1 text-xs rounded-full font-medium inline-flex items-center gap-1.5',
                    instance.status === 'running' ? 'bg-green-100 text-green-700' :
                    instance.status === 'stopped' ? 'bg-yellow-100 text-yellow-700' :
                    instance.status === 'created' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  ]"
                >
                  <span 
                    class="w-1.5 h-1.5 rounded-full"
                    :class="{
                      'bg-green-500 animate-pulse': instance.status === 'running',
                      'bg-yellow-500': instance.status === 'stopped',
                      'bg-blue-500': instance.status === 'created',
                      'bg-gray-500': instance.status === 'error'
                    }"
                  ></span>
                  {{ 
                    instance.status === 'running' ? '运行中' : 
                    instance.status === 'stopped' ? '已停止' : 
                    instance.status === 'created' ? '已创建' :
                    '异常' 
                  }}
                </span>
              </td>
              <td class="px-6 py-4 text-right space-x-1">
                <button
                  @click.stop="handleStartInstance(instance)"
                  v-if="instance.status !== 'running'"
                  :disabled="store.loading || store.actionInstance === instance.id"
                  class="px-3 py-1.5 text-xs text-green-600 hover:bg-green-50 rounded-md transition-colors disabled:opacity-50 inline-flex items-center"
                  title="启动实例"
                >
                  <svg v-if="store.actionInstance === instance.id" class="animate-spin -ml-1 mr-1.5 h-3 w-3 text-green-600 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  启动
                </button>
                <button
                  @click.stop="handleStopInstance(instance)"
                  v-else
                  :disabled="store.loading || store.actionInstance === instance.id"
                  class="px-3 py-1.5 text-xs text-yellow-600 hover:bg-yellow-50 rounded-md transition-colors disabled:opacity-50 inline-flex items-center"
                  title="停止实例"
                >
                  <svg v-if="store.actionInstance === instance.id" class="animate-spin -ml-1 mr-1.5 h-3 w-3 text-yellow-600 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  停止
                </button>
                <button
                  @click.stop="handleDeleteInstance(instance)"
                  :disabled="store.loading || store.actionInstance === instance.id"
                  class="px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50 inline-flex items-center"
                  title="删除实例"
                >
                  <svg v-if="store.actionInstance === instance.id" class="animate-spin -ml-1 mr-1.5 h-3 w-3 text-red-600 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Footer info -->
      <div class="mt-4 flex items-center justify-between text-sm text-gray-500">
        <div>
          共 <span class="font-medium text-gray-900">{{ store.instances.length }}</span> 个实例
          <span v-if="store.runningInstances.length > 0" class="ml-2">
            · <span class="text-green-600 font-medium">{{ store.runningInstances.length }}</span> 个运行中
          </span>
        </div>
        <div v-if="store.lastFetchTime" class="text-xs">
          上次更新：{{ store.lastFetchTime.toLocaleTimeString() }}
        </div>
      </div>
    </div>
  </main>

  <!-- Create Modal -->
  <Modal
    :show="showCreateModal"
    title="部署新机器人"
    subtitle="Docker 容器部署"
    @close="closeModal"
  >
    <form class="space-y-4" @submit.prevent="handleCreate">
      <div class="grid grid-cols-2 gap-4">
        <Input
          v-model="formName"
          label="实例名称"
          placeholder="dian-bot"
          required
        />
        <Select
          v-model="formFramework"
          label="选择框架"
          :options="frameworkOptions"
        />
      </div>

      <!-- NapCat Fields -->
      <div v-if="formFramework === 'napcat'" class="space-y-3">
        <p class="text-xs text-pink-500 font-medium">宿主机映射端口配置</p>
        <div class="grid grid-cols-3 gap-3">
          <Input v-model="formWebPort" type="number" label="Web UI (6099)" />
          <Input v-model="formHttpPort" type="number" label="HTTP (3000)" />
          <Input v-model="formWsPort" type="number" label="WS (3001)" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <Input v-model="formUid" type="number" label="NAPCAT_UID" />
          <Input v-model="formGid" type="number" label="NAPCAT_GID" />
        </div>
      </div>

      <!-- LLOneBot Fields -->
      <div v-else>
        <Input v-model="formLlPort" type="number" label="宿主机映射端口 (容器内:3080)" />
      </div>

      <!-- Command Preview -->
      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1">Docker 指令预览</label>
        <div class="bg-gray-900 rounded-lg p-4 max-h-48 overflow-auto">
          <code class="text-pink-400 text-sm font-mono whitespace-pre">{{ dockerCommand }}</code>
        </div>
      </div>

      <button type="submit" class="w-full py-2.5 bg-pink-500 hover:bg-pink-600 text-white text-sm font-medium rounded-lg transition-colors">
        立即启动容器
      </button>
    </form>
  </Modal>

  <!-- Confirm Modal -->
  <ConfirmModal
    :show="confirmModal.show"
    :title="confirmModal.title"
    :message="confirmModal.message"
    :type="confirmModal.type"
    :confirm-text="confirmModal.confirmText"
    :loading="confirmModal.loading"
    @confirm="handleConfirm"
    @cancel="closeConfirm"
  />

  <!-- Toast -->
  <Toast />
</template>
