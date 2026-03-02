<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useInstanceStore } from '../stores/instance'

const router = useRouter()
const store = useInstanceStore()

const name = ref('')
const qqNumber = ref('')
const protocol = ref('napcat')
const description = ref('')
const loading = ref(false)
const error = ref('')

const protocolOptions = [
  { value: 'napcat', label: 'NapCat (推荐)' },
  { value: 'llonebot', label: 'LLOneBot' },
  { value: 'custom', label: '自定义' },
]

async function handleSubmit() {
  if (!name.value || !qqNumber.value) {
    error.value = '请填写名称和QQ号'
    return
  }

  loading.value = true
  error.value = ''

  const result = await store.createInstance({
    name: name.value,
    qq_number: qqNumber.value,
    protocol: protocol.value as 'napcat' | 'llonebot' | 'custom',
    description: description.value || undefined,
  })

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
          创建新的 Bot 实例
        </h1>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Error Message -->
          <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {{ error }}
          </div>

          <!-- Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              实例名称 <span class="text-red-500">*</span>
            </label>
            <input
              v-model="name"
              type="text"
              required
              placeholder="例如: my-first-bot"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
            />
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

          <!-- Protocol -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              协议
            </label>
            <select
              v-model="protocol"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none bg-white"
            >
              <option v-for="opt in protocolOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
            <p class="mt-1 text-sm text-gray-500">当前选择: {{ protocol }}</p>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              描述（可选）
            </label>
            <textarea
              v-model="description"
              rows="3"
              placeholder="对这个 Bot 的简单描述..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 outline-none"
            ></textarea>
          </div>

          <!-- Submit -->
          <div class="flex gap-4">
            <button
              type="submit"
              :disabled="loading"
              class="flex-1 bg-pink-500 hover:bg-pink-600 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg transition-colors"
            >
              {{ loading ? '创建中...' : '创建实例' }}
            </button>
            <button
              type="button"
              @click="goBack"
              class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
