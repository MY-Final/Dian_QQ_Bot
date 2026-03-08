<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { authApi, getErrorMessage, setAuthSession } from '@/api'

const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleLogin(): Promise<void> {
  if (!username.value.trim() || !password.value.trim()) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const response = await authApi.login(username.value.trim(), password.value)
    if (!response.data.success || !response.data.data) {
      errorMessage.value = response.data.message || '登录失败，请重试'
      return
    }

    setAuthSession(response.data.data)
    await router.replace('/')
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-xl shadow-slate-200/60">
      <div class="mb-6 text-center">
        <div class="mx-auto mb-3 h-12 w-12 rounded-xl bg-pink-500 text-white grid place-items-center font-bold text-lg">D</div>
        <h1 class="text-xl font-semibold text-slate-900">登录 Dian QQ Bot</h1>
        <p class="mt-1 text-sm text-slate-500">继续管理你的 NapCat 实例</p>
      </div>

      <form class="space-y-4" @submit.prevent="handleLogin">
        <div>
          <label class="mb-1 block text-sm text-slate-700">用户名</label>
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
            placeholder="请输入用户名"
          />
        </div>

        <div>
          <label class="mb-1 block text-sm text-slate-700">密码</label>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
            placeholder="请输入密码"
          />
        </div>

        <div v-if="errorMessage" class="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {{ errorMessage }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-lg bg-pink-500 py-2.5 text-sm font-medium text-white transition hover:bg-pink-600 disabled:cursor-not-allowed disabled:bg-pink-300"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>
