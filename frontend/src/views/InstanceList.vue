<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useInstanceStore } from '../stores/instance'
import Modal from '../components/ui/Modal.vue'
import Input from '../components/ui/Input.vue'
import Select from '../components/ui/Select.vue'

const router = useRouter()
const store = useInstanceStore()

// Modal state
const showCreateModal = ref(false)

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
  const result = await store.createInstance({
    name: formName.value,
    qq_number: '123456789',
    protocol: formFramework.value as 'napcat' | 'llonebot' | 'custom',
  })
  if (result) {
    closeModal()
  }
}

function goToDetail(id: string) {
  router.push(`/instance/${id}`)
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
      <span class="flex items-center text-xs text-green-600">
        <span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
        Docker 已连接
      </span>
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
        <button
          @click="openModal"
          class="px-4 py-2 bg-pink-500 hover:bg-pink-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/></svg>
          创建实例
        </button>
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
                加载中...
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
              class="hover:bg-gray-50 cursor-pointer"
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
                    'px-2 py-1 text-xs rounded-full',
                    instance.status === 'running' ? 'bg-green-100 text-green-700' :
                    instance.status === 'stopped' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-700'
                  ]"
                >
                  {{ instance.status === 'running' ? '运行中' : instance.status === 'stopped' ? '已停止' : '未知' }}
                </span>
              </td>
              <td class="px-6 py-4 text-right space-x-2">
                <button
                  @click.stop="store.startInstance(instance.id)"
                  v-if="instance.status !== 'running'"
                  class="px-3 py-1 text-xs text-green-600 hover:bg-green-50 rounded"
                >
                  启动
                </button>
                <button
                  @click.stop="store.stopInstance(instance.id)"
                  v-else
                  class="px-3 py-1 text-xs text-yellow-600 hover:bg-yellow-50 rounded"
                >
                  停止
                </button>
                <button
                  @click.stop="store.deleteInstance(instance.id)"
                  class="px-3 py-1 text-xs text-red-600 hover:bg-red-50 rounded"
                >
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
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
</template>
