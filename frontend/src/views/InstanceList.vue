<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useInstanceStore } from '../stores/instance'
import { getErrorMessage, imageApi, type Instance, type InstanceCreate } from '../api'
import Modal from '../components/ui/Modal.vue'
import ConfirmModal from '../components/ui/ConfirmModal.vue'
import Toast from '../components/ui/Toast.vue'
import { useToast } from '@/composables/useToast'
import { useDockerStatus } from '@/composables/useDockerStatus'

const router = useRouter()
const store = useInstanceStore()
const toast = useToast()

// 使用 Docker 状态 composable
const { dockerStatus, loading: dockerLoading, fetchDockerStatus } = useDockerStatus()

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
const formQqNumber = ref('')
const formFramework = ref<'napcat' | 'llonebot'>('napcat')
const formWebPort = ref(6099)
const formHttpPort = ref(3000)
const formWsPort = ref(3001)
const formUid = ref(1000)
const formGid = ref(1000)
const formLlPort = ref(3080)
const formDescription = ref('')
const formImageTag = ref('latest')
const imageTagOptions = ref<string[]>([])
const loadingImageTags = ref(false)
const showImageTagDropdown = ref(false)
const imageTagDropdownRef = ref<HTMLElement | null>(null)
const creatingInstance = ref(false)
const createStatusMessage = ref('')
const createStatusStage = ref<'idle' | 'ensure' | 'create'>('idle')
const searchKeyword = ref('')
const statusFilter = ref<'all' | 'running' | 'stopped' | 'created' | 'error'>('all')

const frameworkOptions = [
  { value: 'napcat', label: 'NapCat Docker' },
  { value: 'llonebot', label: 'LLOneBot' },
]

const selectedImageRepo = computed<string>(() => {
  if (formFramework.value === 'napcat') {
    return 'mlikiowa/napcat-docker'
  }
  return 'initialencounter/llonebot'
})

const filteredImageTagOptions = computed<string[]>(() => {
  const keyword = formImageTag.value.trim().toLowerCase()
  if (!keyword) {
    return imageTagOptions.value
  }
  return imageTagOptions.value.filter((tag: string) => tag.toLowerCase().includes(keyword))
})

const isDeploying = computed<boolean>(() => creatingInstance.value || store.loading)

const deploySteps = [
  { key: 'ensure', label: '检查并准备镜像' },
  { key: 'create', label: '创建实例容器' },
] as const

const currentDeployStepIndex = computed<number>(() => {
  if (createStatusStage.value === 'create') {
    return 1
  }
  if (createStatusStage.value === 'ensure') {
    return 0
  }
  return -1
})

const filteredInstances = computed(() => {
  return store.instances.filter((instance) => {
    const matchKeyword =
      instance.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      instance.qq_number.includes(searchKeyword.value)
    const matchStatus = statusFilter.value === 'all' || instance.status === statusFilter.value
    return matchKeyword && matchStatus
  })
})

onMounted(() => {
  store.fetchInstances()
  fetchDockerStatus()
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
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
  ${selectedImageRepo.value}:${formImageTag.value}`
  } else {
    return `docker run -d \\
  --name ${formName.value} \\
  -p ${formLlPort.value}:3080 \\
  ${selectedImageRepo.value}:${formImageTag.value}`
  }
})

async function loadImageTags() {
  loadingImageTags.value = true
  try {
    const response = await imageApi.tags(selectedImageRepo.value)
    imageTagOptions.value = response.data.data?.tags || []
    if (imageTagOptions.value.length > 0 && !imageTagOptions.value.includes(formImageTag.value)) {
      const firstTag = imageTagOptions.value[0]
      if (firstTag) {
        formImageTag.value = firstTag
      }
    }
  } catch (err) {
    toast.error(getErrorMessage(err, '获取镜像版本失败'))
    imageTagOptions.value = []
  } finally {
    loadingImageTags.value = false
  }
}

function toggleImageTagDropdown() {
  showImageTagDropdown.value = !showImageTagDropdown.value
  if (showImageTagDropdown.value && imageTagOptions.value.length === 0 && !loadingImageTags.value) {
    void loadImageTags()
  }
}

function selectImageTag(tag: string) {
  formImageTag.value = tag
  showImageTagDropdown.value = false
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target
  if (!(target instanceof Node)) {
    return
  }
  if (imageTagDropdownRef.value && !imageTagDropdownRef.value.contains(target)) {
    showImageTagDropdown.value = false
  }
}

function openModal() {
  showCreateModal.value = true
  createStatusMessage.value = ''
  creatingInstance.value = false
  createStatusStage.value = 'idle'
  void loadImageTags()
}

function closeModal() {
  showCreateModal.value = false
  createStatusMessage.value = ''
  creatingInstance.value = false
  createStatusStage.value = 'idle'
}

async function handleCreate() {
  // 验证 QQ 号
  if (!formQqNumber.value || formQqNumber.value.length < 5) {
    toast.error('请输入有效的 QQ 号码（至少 5 位）')
    return
  }
  
  // 构建完整的请求体
  const createData: InstanceCreate = {
    name: formName.value,
    qq_number: formQqNumber.value,
    protocol: formFramework.value,
    description: formDescription.value || undefined,
    image_repo: selectedImageRepo.value,
    image_tag: formImageTag.value,
  }

  creatingInstance.value = true
  createStatusStage.value = 'ensure'
  createStatusMessage.value = '正在准备镜像，首次部署可能需要等待 1-3 分钟...'

  try {
    await imageApi.ensure(selectedImageRepo.value, formImageTag.value, undefined, true)
  } catch (err) {
    toast.error(getErrorMessage(err, '镜像检查失败，请确认版本是否存在'))
    creatingInstance.value = false
    createStatusStage.value = 'idle'
    createStatusMessage.value = ''
    return
  }
  
  // 如果是 NapCat，添加端口和环境变量配置
  if (formFramework.value === 'napcat') {
    if (formWebPort.value) createData.port_web_ui = formWebPort.value
    if (formHttpPort.value) createData.port_http = formHttpPort.value
    if (formWsPort.value) createData.port_ws = formWsPort.value
    if (formUid.value) createData.napcat_uid = formUid.value
    if (formGid.value) createData.napcat_gid = formGid.value
  }
  
  createStatusStage.value = 'create'
  createStatusMessage.value = '镜像就绪，正在创建实例容器...'
  const result = await store.createInstance(createData)
  creatingInstance.value = false

  if (result) {
    createStatusMessage.value = ''
    createStatusStage.value = 'idle'
    closeModal()
    toast.success(`实例 "${formName.value}" 创建成功！`)
    formQqNumber.value = '' // 清空 QQ 号
  } else {
    createStatusMessage.value = ''
    createStatusStage.value = 'idle'
    toast.error(store.error || '创建实例失败，请稍后重试')
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

function clearFilters() {
  searchKeyword.value = ''
  statusFilter.value = 'all'
}

watch(formFramework, () => {
  formImageTag.value = 'latest'
  showImageTagDropdown.value = false
  void loadImageTags()
})
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

      <div class="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div class="rounded-xl border border-slate-200 bg-white px-4 py-3">
          <div class="text-xs text-slate-500">总实例数</div>
          <div class="mt-1 text-xl font-semibold text-slate-900">{{ store.instanceCount }}</div>
        </div>
        <div class="rounded-xl border border-emerald-200 bg-emerald-50/60 px-4 py-3">
          <div class="text-xs text-emerald-700">运行中</div>
          <div class="mt-1 text-xl font-semibold text-emerald-800">{{ store.runningInstances.length }}</div>
        </div>
        <div class="rounded-xl border border-rose-200 bg-rose-50/60 px-4 py-3">
          <div class="text-xs text-rose-700">异常实例</div>
          <div class="mt-1 text-xl font-semibold text-rose-800">{{ store.errorInstances.length }}</div>
        </div>
      </div>

      <div class="mb-4 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-3 sm:flex-row sm:items-center">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="按实例名或 QQ 号搜索..."
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
        />
        <select
          v-model="statusFilter"
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
        >
          <option value="all">全部状态</option>
          <option value="running">运行中</option>
          <option value="stopped">已停止</option>
          <option value="created">已创建</option>
          <option value="error">异常</option>
        </select>
        <button class="text-sm text-slate-500 hover:text-slate-700" @click="clearFilters">清空筛选</button>
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
            <tr v-else-if="store.error" class="hover:bg-gray-50">
              <td colspan="4" class="px-6 py-8 text-center text-rose-500">
                <div class="text-2xl mb-2">:(</div>
                <div>实例列表加载失败</div>
                <div class="text-xs mt-1">{{ store.error }}</div>
                <button
                  class="mt-3 inline-flex items-center rounded-md bg-rose-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-rose-600"
                  @click="store.fetchInstances(true)"
                >
                  重试
                </button>
              </td>
            </tr>
            <tr v-else-if="filteredInstances.length === 0" class="hover:bg-gray-50">
              <td colspan="4" class="px-6 py-8 text-center text-gray-400">
                <div class="text-2xl mb-2">🐱</div>
                <div>{{ store.instances.length === 0 ? '暂无实例' : '没有匹配筛选条件的实例' }}</div>
                <div class="text-xs mt-1">{{ store.instances.length === 0 ? '点击"创建实例"开始' : '试试清空筛选条件' }}</div>
              </td>
            </tr>
            <tr
              v-else
              v-for="instance in filteredInstances"
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
          共 <span class="font-medium text-gray-900">{{ filteredInstances.length }}</span> / {{ store.instances.length }} 个实例
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
    <form class="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-5" @submit.prevent="handleCreate">
      <div class="space-y-5">
        <section class="space-y-3">
          <div class="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span class="w-1 h-3 rounded-full bg-pink-500"></span>
            基础配置
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-500">实例名称 *</label>
              <input
                v-model="formName"
                type="text"
                placeholder="dian-bot"
                required
                class="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
              />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-500">QQ 号码 *</label>
              <input
                v-model="formQqNumber"
                type="text"
                placeholder="123456789"
                required
                class="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
              />
            </div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-500">镜像名称</label>
              <select
                v-model="formFramework"
                class="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
              >
                <option v-for="opt in frameworkOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-500">描述（可选）</label>
              <input
                v-model="formDescription"
                type="text"
                placeholder="我的 QQ Bot"
                class="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-800 outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
              />
            </div>
          </div>
          <div ref="imageTagDropdownRef" class="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 relative">
            <div class="flex items-center justify-between gap-3 mb-2">
              <div>
                <p class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">镜像版本 (Tag)</p>
                <p class="text-xs text-gray-500">仓库：{{ selectedImageRepo }}</p>
              </div>
              <button
                type="button"
                :disabled="loadingImageTags"
                class="px-3 py-1.5 text-xs rounded-full border border-gray-300 bg-white hover:bg-pink-50 disabled:opacity-50"
                @click="loadImageTags"
              >{{ loadingImageTags ? '检查中...' : '检查更新' }}</button>
            </div>
            <div class="flex gap-2">
              <input
                v-model="formImageTag"
                type="text"
                placeholder="latest"
                class="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm font-semibold text-gray-800 outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
                @focus="showImageTagDropdown = true"
              />
              <button
                type="button"
                class="px-3 py-2 rounded-xl border border-gray-200 bg-white hover:bg-gray-50"
                @click="toggleImageTagDropdown"
              >
                ▾
              </button>
            </div>
            <div
              v-if="showImageTagDropdown"
              class="absolute left-4 right-4 top-full mt-2 z-20 rounded-xl border border-gray-200 bg-white shadow-lg max-h-48 overflow-auto"
            >
              <button
                v-for="tag in filteredImageTagOptions"
                :key="tag"
                type="button"
                class="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-pink-50 flex items-center justify-between"
                @click="selectImageTag(tag)"
              >
                <span>{{ tag }}</span>
                <span v-if="formImageTag === tag" class="text-xs text-pink-500 font-semibold">已选中</span>
              </button>
              <div v-if="loadingImageTags" class="px-3 py-2 text-xs text-gray-500">版本加载中...</div>
              <div v-else-if="filteredImageTagOptions.length === 0" class="px-3 py-2 text-xs text-gray-500">
                暂无匹配版本
              </div>
            </div>
          </div>
        </section>

        <section v-if="formFramework === 'napcat'" class="space-y-3">
          <div class="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span class="w-1 h-3 rounded-full bg-pink-500"></span>
            环境权限变量
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="rounded-xl border border-gray-200 bg-white px-4 py-3 flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-500">NAPCAT_UID</span>
              <input v-model.number="formUid" type="number" class="w-20 text-right font-semibold text-gray-800 outline-none" />
            </div>
            <div class="rounded-xl border border-gray-200 bg-white px-4 py-3 flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-500">NAPCAT_GID</span>
              <input v-model.number="formGid" type="number" class="w-20 text-right font-semibold text-gray-800 outline-none" />
            </div>
          </div>
        </section>

        <section class="space-y-3">
          <div class="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span class="w-1 h-3 rounded-full bg-pink-500"></span>
            端口映射 (Host)
          </div>
          <div v-if="formFramework === 'napcat'" class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div class="rounded-xl border border-gray-200 bg-white px-3 py-3 text-center">
              <p class="text-[11px] uppercase tracking-wider text-gray-400">Web UI</p>
              <input v-model.number="formWebPort" type="number" class="mt-1 w-full text-center text-lg font-semibold text-gray-800 outline-none" />
            </div>
            <div class="rounded-xl border border-gray-200 bg-white px-3 py-3 text-center">
              <p class="text-[11px] uppercase tracking-wider text-gray-400">HTTP</p>
              <input v-model.number="formHttpPort" type="number" class="mt-1 w-full text-center text-lg font-semibold text-gray-800 outline-none" />
            </div>
            <div class="rounded-xl border border-gray-200 bg-white px-3 py-3 text-center">
              <p class="text-[11px] uppercase tracking-wider text-gray-400">WS</p>
              <input v-model.number="formWsPort" type="number" class="mt-1 w-full text-center text-lg font-semibold text-gray-800 outline-none" />
            </div>
          </div>
          <div v-else class="rounded-xl border border-gray-200 bg-white px-4 py-3 flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">容器内 3080 端口</span>
            <input v-model.number="formLlPort" type="number" class="w-24 text-right text-lg font-semibold text-gray-800 outline-none" />
          </div>
        </section>
      </div>

      <div class="rounded-[1.8rem] bg-slate-100 p-2">
        <div class="h-full rounded-[1.4rem] bg-[#0f172a] p-5 flex flex-col">
          <div class="flex items-center justify-between mb-4">
            <div class="flex gap-1.5">
              <span class="w-2 h-2 rounded-full bg-rose-400/40"></span>
              <span class="w-2 h-2 rounded-full bg-amber-400/40"></span>
              <span class="w-2 h-2 rounded-full bg-emerald-400/40"></span>
            </div>
            <span class="text-[10px] uppercase tracking-[0.2em] text-slate-500">Docker Preview</span>
          </div>
          <pre class="flex-1 overflow-auto text-[12px] leading-7 text-rose-400 font-mono whitespace-pre-wrap">{{ dockerCommand }}</pre>
          <div v-if="isDeploying" class="mt-3 space-y-2">
            <div
              v-for="(step, index) in deploySteps"
              :key="step.key"
              class="flex items-center justify-between text-xs"
            >
              <span
                :class="index <= currentDeployStepIndex ? 'text-pink-300' : 'text-slate-500'"
              >{{ step.label }}</span>
              <span
                :class="index < currentDeployStepIndex ? 'text-emerald-300' : index === currentDeployStepIndex ? 'text-pink-300' : 'text-slate-500'"
              >{{ index < currentDeployStepIndex ? '已完成' : index === currentDeployStepIndex ? '进行中' : '等待中' }}</span>
            </div>
          </div>
          <p v-if="createStatusMessage" class="mt-3 text-xs text-slate-300">
            {{ createStatusMessage }}
          </p>
          <button
            type="submit"
            :disabled="isDeploying"
            class="mt-4 w-full py-3 rounded-xl bg-pink-500 hover:bg-pink-600 text-white font-semibold transition-colors disabled:opacity-70"
          >{{ isDeploying ? '部署进行中...' : '开始部署' }}</button>
        </div>
      </div>
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
