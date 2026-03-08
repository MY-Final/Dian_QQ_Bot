<script setup lang="ts">
import { reactive } from 'vue'

import Toast from '@/components/ui/Toast.vue'
import { useToast } from '@/composables/useToast'
import { useUiPreferences } from '@/composables/useUiPreferences'

const toast = useToast()
const { preferences, savePreferences, resetPreferences, defaultPreferences } = useUiPreferences()

const form = reactive({
  logRefreshIntervalMs: preferences.value.logRefreshIntervalMs,
  defaultLogLines: preferences.value.defaultLogLines,
  requireDeleteConfirmText: preferences.value.requireDeleteConfirmText,
})

function save(): void {
  savePreferences({
    logRefreshIntervalMs: form.logRefreshIntervalMs,
    defaultLogLines: form.defaultLogLines,
    requireDeleteConfirmText: form.requireDeleteConfirmText,
  })
  toast.success('设置已保存')
}

function restoreDefaults(): void {
  resetPreferences()
  form.logRefreshIntervalMs = defaultPreferences.logRefreshIntervalMs
  form.defaultLogLines = defaultPreferences.defaultLogLines
  form.requireDeleteConfirmText = defaultPreferences.requireDeleteConfirmText
  toast.info('已恢复默认设置')
}
</script>

<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center text-sm text-gray-500">
      <span class="font-medium">控制台</span>
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-2"><path d="m9 18 6-6-6-6"/></svg>
      <span class="font-medium text-gray-900">系统设置</span>
    </div>
  </header>

  <main class="flex-1 p-6 overflow-auto">
    <div class="max-w-2xl mx-auto space-y-5">
      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <h2 class="text-base font-semibold text-slate-900">交互偏好</h2>
        <p class="mt-1 text-sm text-slate-500">这些设置会保存在当前浏览器，仅影响当前用户体验。</p>

        <div class="mt-5 space-y-4">
          <label class="block">
            <span class="text-sm text-slate-700">日志刷新间隔（毫秒）</span>
            <input
              v-model.number="form.logRefreshIntervalMs"
              type="number"
              min="1000"
              max="10000"
              step="500"
              class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
            />
          </label>

          <label class="block">
            <span class="text-sm text-slate-700">默认日志行数</span>
            <select
              v-model.number="form.defaultLogLines"
              class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
            >
              <option :value="50">50 行</option>
              <option :value="100">100 行</option>
              <option :value="200">200 行</option>
              <option :value="500">500 行</option>
            </select>
          </label>

          <label class="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2">
            <span class="text-sm text-slate-700">删除实例时要求输入实例名确认</span>
            <input v-model="form.requireDeleteConfirmText" type="checkbox" class="h-4 w-4" />
          </label>
        </div>

        <div class="mt-6 flex gap-3">
          <button
            class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            @click="save"
          >保存设置</button>
          <button
            class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            @click="restoreDefaults"
          >恢复默认</button>
        </div>
      </div>
    </div>
  </main>

  <Toast />
</template>
