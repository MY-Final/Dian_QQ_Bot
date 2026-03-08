<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getErrorMessage, imageApi, type ImageRepositoryResult, type InstanceCreate } from '@/api'
import { useInstanceStore } from '../stores/instance'

const router = useRouter()
const store = useInstanceStore()

// 基本信息
const name = ref('')
const qqNumber = ref('')
const protocol = ref('napcat')
const description = ref('')

// 端口配置（对应截图中的字段）
const portWebUi = ref<number | null>(null)
const portHttp = ref<number | null>(null)
const portWs = ref<number | null>(null)

// NapCat 环境变量配置
const napcatUid = ref<number | null>(1000)
const napcatGid = ref<number | null>(1000)

// 镜像配置
const imageRegistry = ref('')
const imageRepo = ref('mlikiowa/napcat-docker')
const imageTag = ref('latest')
const imageSearchQuery = ref('napcat')
const imageSearchResults = ref<ImageRepositoryResult[]>([])
const imageTags = ref<string[]>([])
const searchingImages = ref(false)
const loadingTags = ref(false)
const pullingImage = ref(false)

const loading = ref(false)
const error = ref('')

const protocolOptions = [
  { value: 'napcat', label: 'NapCat (推荐)' },
  { value: 'llonebot', label: 'LLOneBot' },
  { value: 'custom', label: '自定义' },
]

// Docker 命令预览
const dockerCommandPreview = computed(() => {
  const ports: string[] = []
  if (portHttp.value) ports.push(`-p ${portHttp.value}:3000`)
  if (portWs.value) ports.push(`-p ${portWs.value}:3001`)
  if (portWebUi.value) ports.push(`-p ${portWebUi.value}:6099`)
  
  const envs: string[] = []
  if (napcatUid.value !== null) envs.push(`-e NAPCAT_UID=${napcatUid.value}`)
  if (napcatGid.value !== null) envs.push(`-e NAPCAT_GID=${napcatGid.value}`)
  
  const imageRef = imageRegistry.value
    ? `${imageRegistry.value.replace(/\/$/, '')}/${imageRepo.value}:${imageTag.value}`
    : `${imageRepo.value}:${imageTag.value}`

  return `docker run -d \\
  --name ${name.value || 'bot-name'} \\
${envs.map(e => `  ${e} \\\n`).join('')}${ports.map(p => `  ${p} \\\n`).join('')}  ${imageRef}`
})

// 验证端口输入
const portErrors = computed(() => {
  const errors: string[] = []
  
  const validatePort = (port: number | null, name: string) => {
    if (port === null || port === undefined || port === 0) return
    if (isNaN(port) || port < 1024 || port > 65535) {
      errors.push(`${name} 必须在 1024-65535 之间`)
    }
  }
  
  validatePort(portHttp.value, 'HTTP 端口')
  validatePort(portWs.value, 'WebSocket 端口')
  validatePort(portWebUi.value, 'Web UI 端口')
  
  return errors
})

// 表单是否有效
const isValid = computed(() => {
  return name.value && qqNumber.value && imageRepo.value && imageTag.value && portErrors.value.length === 0
})

async function searchImages() {
  if (!imageSearchQuery.value.trim()) {
    return
  }

  searchingImages.value = true
  try {
    const response = await imageApi.search(imageSearchQuery.value.trim(), imageRegistry.value || undefined)
    imageSearchResults.value = response.data.data || []
  } catch (err) {
    error.value = getErrorMessage(err, '搜索镜像失败')
  } finally {
    searchingImages.value = false
  }
}

async function loadTags() {
  if (!imageRepo.value.trim()) {
    return
  }

  loadingTags.value = true
  try {
    const response = await imageApi.tags(imageRepo.value.trim(), imageRegistry.value || undefined)
    imageTags.value = response.data.data?.tags || []
    if (imageTags.value.length > 0 && !imageTags.value.includes(imageTag.value)) {
      const firstTag = imageTags.value[0]
      if (firstTag) {
        imageTag.value = firstTag
      }
    }
  } catch (err) {
    error.value = getErrorMessage(err, '获取镜像版本失败')
  } finally {
    loadingTags.value = false
  }
}

function useSearchResult(result: ImageRepositoryResult) {
  imageRepo.value = result.name
  void loadTags()
}

async function pullImage() {
  if (!imageRepo.value.trim() || !imageTag.value.trim()) {
    error.value = '请先选择镜像仓库和版本'
    return
  }

  pullingImage.value = true
  try {
    await imageApi.pull(imageRepo.value.trim(), imageTag.value.trim(), imageRegistry.value || undefined)
  } catch (err) {
    error.value = getErrorMessage(err, '拉取镜像失败')
  } finally {
    pullingImage.value = false
  }
}

async function handleSubmit() {
  if (!name.value || !qqNumber.value) {
    error.value = '请填写名称和QQ号'
    return
  }

  if (portErrors.value.length > 0) {
    error.value = portErrors.value.join('；')
    return
  }

  loading.value = true
  error.value = ''

  // 构建提交数据，包含所有字段
  const createData: InstanceCreate = {
    name: name.value,
    qq_number: qqNumber.value,
    protocol: protocol.value as 'napcat' | 'llonebot' | 'custom',
    description: description.value || undefined,
    // NapCat 配置（始终传递）
    napcat_uid: napcatUid.value !== null ? napcatUid.value : undefined,
    napcat_gid: napcatGid.value !== null ? napcatGid.value : undefined,
    image_registry: imageRegistry.value || undefined,
    image_repo: imageRepo.value || undefined,
    image_tag: imageTag.value || undefined,
  }
  
  // 端口配置（只要有值就传递，不管是否勾选了自定义端口）
  if (portHttp.value !== null && portHttp.value !== undefined && portHttp.value !== 0) {
    createData.port_http = portHttp.value
  }
  if (portWs.value !== null && portWs.value !== undefined && portWs.value !== 0) {
    createData.port_ws = portWs.value
  }
  if (portWebUi.value !== null && portWebUi.value !== undefined && portWebUi.value !== 0) {
    createData.port_web_ui = portWebUi.value
  }

  try {
    await imageApi.ensure(
      imageRepo.value.trim(),
      imageTag.value.trim(),
      imageRegistry.value || undefined,
      false,
    )
  } catch {
    const shouldPull = window.confirm('本地未找到镜像，是否立即拉取？')
    if (!shouldPull) {
      loading.value = false
      error.value = '请先拉取镜像后再创建实例'
      return
    }

    try {
      await imageApi.pull(imageRepo.value.trim(), imageTag.value.trim(), imageRegistry.value || undefined)
    } catch (pullErr) {
      loading.value = false
      error.value = getErrorMessage(pullErr, '拉取镜像失败，无法创建实例')
      return
    }
  }

  const result = await store.createInstance(createData)

  loading.value = false

  if (result) {
    router.push('/')
  } else {
    error.value = store.error || '创建失败'
  }
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <button
          @click="goBack"
          class="text-pink-500 hover:text-pink-600 flex items-center gap-2"
        >
          ← 返回列表
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-2xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div class="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h1 class="text-2xl font-bold text-gray-900 mb-6">
          部署新机器人
        </h1>
        <p class="text-sm text-gray-500 mb-6">Docker 容器部署</p>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Error Message -->
          <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {{ error }}
          </div>

          <!-- 基本信息 -->
          <div class="grid grid-cols-2 gap-4">
            <!-- Name -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                实例名称 <span class="text-red-500">*</span>
              </label>
              <input
                v-model="name"
                type="text"
                required
                placeholder="test"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
              />
            </div>

            <!-- Protocol -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                选择框架
              </label>
              <select
                v-model="protocol"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none bg-white"
              >
                <option v-for="opt in protocolOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- QQ Number -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              QQ 号 <span class="text-red-500">*</span>
            </label>
            <input
              v-model="qqNumber"
              type="text"
              required
              placeholder="例如: 123456789"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
            />
          </div>

          <!-- 镜像配置 -->
          <div class="border border-gray-200 rounded-lg p-4 bg-gray-50 space-y-4">
            <div>
              <label class="block text-sm font-medium text-pink-600">镜像配置</label>
              <p class="text-xs text-gray-500 mt-1">支持 Docker Hub 和自定义镜像仓库。</p>
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block text-xs text-gray-500 mb-1">Registry（可选）</label>
                <input
                  v-model="imageRegistry"
                  type="text"
                  placeholder="registry.example.com"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">仓库</label>
                <input
                  v-model="imageRepo"
                  type="text"
                  placeholder="mlikiowa/napcat-docker"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
                  @blur="loadTags"
                />
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">版本</label>
                <input
                  v-model="imageTag"
                  list="image-tag-options"
                  type="text"
                  placeholder="latest"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
                />
                <datalist id="image-tag-options">
                  <option v-for="tag in imageTags" :key="tag" :value="tag"></option>
                </datalist>
              </div>
            </div>

            <div class="flex flex-wrap gap-2">
              <input
                v-model="imageSearchQuery"
                type="text"
                placeholder="搜索镜像，如 napcat"
                class="flex-1 min-w-[220px] px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
              />
              <button
                type="button"
                :disabled="searchingImages"
                class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50"
                @click="searchImages"
              >{{ searchingImages ? '搜索中...' : '搜索镜像' }}</button>
              <button
                type="button"
                :disabled="loadingTags"
                class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50"
                @click="loadTags"
              >{{ loadingTags ? '加载中...' : '加载版本' }}</button>
              <button
                type="button"
                :disabled="pullingImage"
                class="px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 disabled:opacity-50"
                @click="pullImage"
              >{{ pullingImage ? '拉取中...' : '拉取镜像' }}</button>
            </div>

            <div v-if="imageSearchResults.length > 0" class="max-h-40 overflow-auto rounded border border-gray-200 bg-white">
              <button
                v-for="item in imageSearchResults"
                :key="item.name"
                type="button"
                class="w-full text-left px-3 py-2 border-b border-gray-100 hover:bg-gray-50"
                @click="useSearchResult(item)"
              >
                <div class="text-sm font-medium text-gray-800">{{ item.name }}</div>
                <div class="text-xs text-gray-500 truncate">{{ item.description || '暂无描述' }}</div>
              </button>
            </div>
          </div>

          <!-- 端口配置 -->
          <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <div class="mb-4">
              <label class="block text-sm font-medium text-pink-600">
                宿主机映射端口配置
              </label>
            </div>

            <!-- 端口输入 -->
            <div class="grid grid-cols-3 gap-4">
              <!-- Web UI 端口 -->
              <div>
                <label class="block text-xs text-gray-500 mb-1">Web UI (6099)</label>
                <input
                  v-model.number="portWebUi"
                  type="number"
                  placeholder="自动分配"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
                />
              </div>

              <!-- HTTP 端口 -->
              <div>
                <label class="block text-xs text-gray-500 mb-1">HTTP (3000)</label>
                <input
                  v-model.number="portHttp"
                  type="number"
                  placeholder="自动分配"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
                />
              </div>

              <!-- WS 端口 -->
              <div>
                <label class="block text-xs text-gray-500 mb-1">WS (3001)</label>
                <input
                  v-model.number="portWs"
                  type="number"
                  placeholder="自动分配"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
                />
              </div>
            </div>

            <p class="mt-2 text-xs text-gray-500">
              填写端口则使用指定端口，留空则系统自动分配
            </p>
          </div>

          <!-- NapCat 环境变量配置 -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                NAPCAT_UID
              </label>
              <input
                v-model.number="napcatUid"
                type="number"
                placeholder="1000"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                NAPCAT_GID
              </label>
              <input
                v-model.number="napcatGid"
                type="number"
                placeholder="1000"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
              />
            </div>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              描述（可选）
            </label>
            <textarea
              v-model="description"
              rows="2"
              placeholder="对这个 Bot 的简单描述..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
            ></textarea>
          </div>

          <!-- Docker 指令预览 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Docker 指令预览
            </label>
            <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
              <pre class="text-sm text-pink-400 font-mono whitespace-pre-wrap">{{ dockerCommandPreview }}</pre>
            </div>
          </div>

          <!-- Submit -->
          <div class="flex gap-4">
            <button
              type="submit"
              :disabled="loading || !isValid"
              class="flex-1 bg-pink-500 hover:bg-pink-600 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg transition-colors font-medium"
            >
              {{ loading ? '创建中...' : '立即启动容器' }}
            </button>
            <button
              type="button"
              @click="goBack"
              class="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
