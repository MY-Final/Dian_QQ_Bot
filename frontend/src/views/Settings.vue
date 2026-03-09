<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { getErrorMessage, imageApi, type LocalImageResult } from '@/api'
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

const localImages = ref<LocalImageResult[]>([])
const loadingImages = ref(false)
const removingImageRef = ref<string | null>(null)
const forceRemove = ref(false)

type ImageVersionRow = {
  imageId: string
  imageRef: string
  displayTag: string
  size: number
  created: string
}

const imageVersionRows = computed<ImageVersionRow[]>(() => {
  const rows: ImageVersionRow[] = []
  localImages.value.forEach((image: LocalImageResult) => {
    if (image.tags.length > 0) {
      image.tags.forEach((tag: string) => {
        rows.push({
          imageId: image.id,
          imageRef: tag,
          displayTag: tag,
          size: image.size,
          created: image.created,
        })
      })
      return
    }
    rows.push({
      imageId: image.id,
      imageRef: image.id,
      displayTag: '<none>:<none>',
      size: image.size,
      created: image.created,
    })
  })
  return rows
})

function formatImageSize(sizeInBytes: number): string {
  const units: string[] = ['B', 'KB', 'MB', 'GB']
  let value = sizeInBytes
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

function formatCreatedAt(value: string): string {
  if (!value) {
    return '-'
  }
  const parsedDate = new Date(value)
  if (Number.isNaN(parsedDate.getTime())) {
    return value
  }
  return parsedDate.toLocaleString()
}

async function loadLocalImages(): Promise<void> {
  loadingImages.value = true
  try {
    const response = await imageApi.local()
    localImages.value = response.data.data || []
  } catch (err) {
    toast.error(getErrorMessage(err, '加载本地镜像失败'))
  } finally {
    loadingImages.value = false
  }
}

async function removeImageVersion(imageRef: string): Promise<void> {
  const shouldDelete = window.confirm(
    `确定删除镜像版本 ${imageRef} 吗？${forceRemove.value ? '将使用强制删除。' : ''}`,
  )
  if (!shouldDelete) {
    return
  }

  removingImageRef.value = imageRef
  try {
    await imageApi.removeLocal(imageRef, forceRemove.value)
    toast.success(`镜像版本 ${imageRef} 删除成功`)
    await loadLocalImages()
  } catch (err) {
    toast.error(getErrorMessage(err, '删除镜像失败，可能仍被容器占用'))
  } finally {
    removingImageRef.value = null
  }
}

onMounted(() => {
  void loadLocalImages()
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
    <div class="max-w-5xl mx-auto space-y-5">
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

      <div class="rounded-xl border border-slate-200 bg-white p-5">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-base font-semibold text-slate-900">镜像版本管理</h2>
            <p class="mt-1 text-sm text-slate-500">查看和清理本地镜像版本，避免磁盘空间被占满。</p>
          </div>
          <button
            class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            :disabled="loadingImages"
            @click="loadLocalImages"
          >{{ loadingImages ? '刷新中...' : '刷新列表' }}</button>
        </div>

        <label class="mt-4 inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
          <input v-model="forceRemove" type="checkbox" class="h-4 w-4" />
          <span class="text-sm text-slate-700">强制删除镜像（镜像被占用时再启用）</span>
        </label>

        <div class="mt-4 overflow-hidden rounded-lg border border-slate-200">
          <table class="min-w-full text-sm">
            <thead class="bg-slate-50 text-slate-600">
              <tr>
                <th class="px-4 py-3 text-left">镜像版本</th>
                <th class="px-4 py-3 text-left">镜像 ID</th>
                <th class="px-4 py-3 text-left">大小</th>
                <th class="px-4 py-3 text-left">创建时间</th>
                <th class="px-4 py-3 text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingImages">
                <td colspan="5" class="px-4 py-6 text-center text-slate-500">正在加载镜像列表...</td>
              </tr>
              <tr v-else-if="imageVersionRows.length === 0">
                <td colspan="5" class="px-4 py-6 text-center text-slate-500">暂无本地镜像版本</td>
              </tr>
              <tr
                v-for="row in imageVersionRows"
                :key="`${row.imageId}-${row.imageRef}`"
                class="border-t border-slate-100"
              >
                <td class="px-4 py-3 font-medium text-slate-800">{{ row.displayTag }}</td>
                <td class="px-4 py-3 text-slate-500">{{ row.imageId }}</td>
                <td class="px-4 py-3 text-slate-500">{{ formatImageSize(row.size) }}</td>
                <td class="px-4 py-3 text-slate-500">{{ formatCreatedAt(row.created) }}</td>
                <td class="px-4 py-3 text-right">
                  <button
                    class="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                    :disabled="removingImageRef === row.imageRef"
                    @click="removeImageVersion(row.imageRef)"
                  >{{ removingImageRef === row.imageRef ? '删除中...' : '删除' }}</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </main>

  <Toast />
</template>
