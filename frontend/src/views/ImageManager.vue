<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { getErrorMessage, imageApi, instanceApi, type Instance, type LocalImageResult } from '@/api'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import Toast from '@/components/ui/Toast.vue'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const localImages = ref<LocalImageResult[]>([])
const loadingImages = ref(false)
const removingImageRef = ref<string | null>(null)
const forceRemove = ref(false)
const searchKeyword = ref('')
const onlyDangling = ref(false)
const pruningDangling = ref(false)
const instances = ref<Instance[]>([])
const expandedRepoGroups = ref<Record<string, boolean>>({})
const selectedImageRefs = ref<string[]>([])
const batchRemoving = ref(false)
const confirmModal = ref<{
  show: boolean
  title: string
  message: string
  confirmText: string
  type: 'danger' | 'warning' | 'info'
  loading: boolean
  action: (() => Promise<void>) | null
}>({
  show: false,
  title: '',
  message: '',
  confirmText: '确认',
  type: 'warning',
  loading: false,
  action: null,
})

type ImageVersionRow = {
  imageId: string
  imageRef: string
  displayTag: string
  repository: string
  tag: string
  size: number
  created: string
}

type ImageGroup = {
  repository: string
  rows: ImageVersionRow[]
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
          repository: parseRepositoryFromImageRef(tag),
          tag: parseTagFromImageRef(tag),
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
      repository: 'dangling',
      tag: '<none>',
      size: image.size,
      created: image.created,
    })
  })
  return rows
})

const filteredImageVersionRows = computed<ImageVersionRow[]>(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()

  return imageVersionRows.value.filter((row: ImageVersionRow) => {
    const isDangling = row.displayTag === '<none>:<none>'
    if (onlyDangling.value && !isDangling) {
      return false
    }
    if (!keyword) {
      return true
    }
    return (
      row.displayTag.toLowerCase().includes(keyword) ||
      row.imageRef.toLowerCase().includes(keyword) ||
      row.imageId.toLowerCase().includes(keyword)
    )
  })
})

const danglingImageRows = computed<ImageVersionRow[]>(() => {
  return imageVersionRows.value.filter((row: ImageVersionRow) => row.displayTag === '<none>:<none>')
})

const totalImageSize = computed<number>(() => {
  return imageVersionRows.value.reduce((sum: number, row: ImageVersionRow) => sum + row.size, 0)
})

const groupedImageRows = computed<ImageGroup[]>(() => {
  const grouped = new Map<string, ImageVersionRow[]>()
  filteredImageVersionRows.value.forEach((row: ImageVersionRow) => {
    if (!grouped.has(row.repository)) {
      grouped.set(row.repository, [])
    }
    const currentRows = grouped.get(row.repository)
    if (currentRows) {
      currentRows.push(row)
    }
  })

  return Array.from(grouped.entries()).map(([repository, rows]) => ({
    repository,
    rows,
  }))
})

const selectableImageRefs = computed<string[]>(() => {
  return Array.from(new Set(filteredImageVersionRows.value.map((row: ImageVersionRow) => row.imageRef)))
})

const isAllFilteredSelected = computed<boolean>(() => {
  if (selectableImageRefs.value.length === 0) {
    return false
  }
  return selectableImageRefs.value.every((imageRef: string) => selectedImageRefs.value.includes(imageRef))
})

const selectedCount = computed<number>(() => selectedImageRefs.value.length)

function parseRepositoryFromImageRef(imageRef: string): string {
  if (imageRef === '<none>:<none>') {
    return 'dangling'
  }
  const lastColonIndex = imageRef.lastIndexOf(':')
  if (lastColonIndex <= 0) {
    return imageRef
  }
  return imageRef.slice(0, lastColonIndex)
}

function parseTagFromImageRef(imageRef: string): string {
  if (imageRef === '<none>:<none>') {
    return '<none>'
  }
  const lastColonIndex = imageRef.lastIndexOf(':')
  if (lastColonIndex < 0 || lastColonIndex === imageRef.length - 1) {
    return 'latest'
  }
  return imageRef.slice(lastColonIndex + 1)
}

function buildInstanceImageRef(instance: Instance): string {
  return `${instance.image_repo}:${instance.image_tag}`
}

function findUsingInstances(imageRef: string): Instance[] {
  return instances.value.filter((instance: Instance) => buildInstanceImageRef(instance) === imageRef)
}

function isImageInUse(imageRef: string): boolean {
  return findUsingInstances(imageRef).length > 0
}

function getUsingInstanceNames(imageRef: string): string {
  return findUsingInstances(imageRef)
    .map((instance: Instance) => instance.name)
    .join('、')
}

function toggleSelectImageRef(imageRef: string): void {
  if (isImageInUse(imageRef)) {
    return
  }
  if (selectedImageRefs.value.includes(imageRef)) {
    selectedImageRefs.value = selectedImageRefs.value.filter((item: string) => item !== imageRef)
    return
  }
  selectedImageRefs.value = [...selectedImageRefs.value, imageRef]
}

function toggleSelectAllFiltered(): void {
  if (isAllFilteredSelected.value) {
    const filteredSet = new Set(selectableImageRefs.value)
    selectedImageRefs.value = selectedImageRefs.value.filter((imageRef: string) => !filteredSet.has(imageRef))
    return
  }

  const availableRefs = selectableImageRefs.value.filter((imageRef: string) => !isImageInUse(imageRef))
  selectedImageRefs.value = Array.from(new Set([...selectedImageRefs.value, ...availableRefs]))
}

function toggleGroup(repository: string): void {
  expandedRepoGroups.value[repository] = !expandedRepoGroups.value[repository]
}

function ensureGroupState(): void {
  const nextState: Record<string, boolean> = { ...expandedRepoGroups.value }
  groupedImageRows.value.forEach((group: ImageGroup) => {
    if (!(group.repository in nextState)) {
      nextState[group.repository] = true
    }
  })
  expandedRepoGroups.value = nextState
}

function syncSelectedRefs(): void {
  const currentRefSet = new Set(imageVersionRows.value.map((row: ImageVersionRow) => row.imageRef))
  selectedImageRefs.value = selectedImageRefs.value.filter((imageRef: string) => currentRefSet.has(imageRef))
}

function openConfirm(options: {
  title: string
  message: string
  confirmText?: string
  type?: 'danger' | 'warning' | 'info'
  action: () => Promise<void>
}): void {
  confirmModal.value = {
    show: true,
    title: options.title,
    message: options.message,
    confirmText: options.confirmText || '确认',
    type: options.type || 'warning',
    loading: false,
    action: options.action,
  }
}

function closeConfirm(): void {
  if (confirmModal.value.loading) {
    return
  }
  confirmModal.value.show = false
  confirmModal.value.action = null
}

async function handleConfirm(): Promise<void> {
  if (!confirmModal.value.action) {
    return
  }

  confirmModal.value.loading = true
  try {
    await confirmModal.value.action()
    confirmModal.value.show = false
    confirmModal.value.action = null
  } finally {
    confirmModal.value.loading = false
  }
}

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
    ensureGroupState()
  }
}

async function loadInstances(): Promise<void> {
  try {
    const response = await instanceApi.list()
    instances.value = response.data.data || []
  } catch (err) {
    toast.error(getErrorMessage(err, '加载实例列表失败，无法判断镜像占用'))
  }
}

async function doRemoveImageVersion(imageRef: string): Promise<void> {
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

async function removeImageVersion(imageRef: string): Promise<void> {
  const usingInstances = findUsingInstances(imageRef)
  if (usingInstances.length > 0) {
    const instanceNames = usingInstances.map((instance: Instance) => instance.name).join('、')
    toast.error(`镜像正在被实例使用：${instanceNames}，请先切换或停止后再删除`)
    return
  }

  openConfirm({
    title: '删除镜像版本',
    message: `确定删除镜像版本 ${imageRef} 吗？${forceRemove.value ? '将使用强制删除。' : ''}`,
    confirmText: '删除',
    type: 'danger',
    action: async () => {
      await doRemoveImageVersion(imageRef)
    },
  })
}

async function doRemoveSelectedImageVersions(removableRefs: string[]): Promise<void> {
  batchRemoving.value = true
  let successCount = 0
  let failureCount = 0

  try {
    for (const imageRef of removableRefs) {
      removingImageRef.value = imageRef
      try {
        await imageApi.removeLocal(imageRef, forceRemove.value)
        successCount += 1
      } catch {
        failureCount += 1
      }
    }

    if (successCount > 0 && failureCount === 0) {
      toast.success(`批量删除成功，共删除 ${successCount} 个镜像版本`)
    } else if (successCount > 0 && failureCount > 0) {
      toast.info(`批量删除完成：成功 ${successCount} 个，失败 ${failureCount} 个`)
    } else {
      toast.error('批量删除失败，请检查镜像占用状态')
    }
    selectedImageRefs.value = []
    await loadLocalImages()
  } finally {
    removingImageRef.value = null
    batchRemoving.value = false
  }
}

async function removeSelectedImageVersions(): Promise<void> {
  if (selectedImageRefs.value.length === 0) {
    toast.info('请先选择要删除的镜像版本')
    return
  }

  const inUseRefs = selectedImageRefs.value.filter((imageRef: string) => isImageInUse(imageRef))
  const removableRefs = selectedImageRefs.value.filter((imageRef: string) => !isImageInUse(imageRef))

  if (inUseRefs.length > 0) {
    toast.error('部分镜像被实例占用，已自动跳过占用项')
  }

  if (removableRefs.length === 0) {
    return
  }

  openConfirm({
    title: '批量删除镜像版本',
    message: `确定批量删除 ${removableRefs.length} 个镜像版本吗？${forceRemove.value ? '将使用强制删除。' : ''}`,
    confirmText: '批量删除',
    type: 'danger',
    action: async () => {
      await doRemoveSelectedImageVersions(removableRefs)
    },
  })
}

async function doPruneDanglingImages(): Promise<void> {
  pruningDangling.value = true
  try {
    for (const row of danglingImageRows.value) {
      await imageApi.removeLocal(row.imageRef, forceRemove.value)
    }
    toast.success(`已清理 ${danglingImageRows.value.length} 个悬空镜像`)
    await loadLocalImages()
  } catch (err) {
    toast.error(getErrorMessage(err, '清理悬空镜像失败，请检查镜像占用状态'))
  } finally {
    pruningDangling.value = false
  }
}

async function pruneDanglingImages(): Promise<void> {
  if (danglingImageRows.value.length === 0) {
    toast.info('当前没有可清理的悬空镜像')
    return
  }

  openConfirm({
    title: '清理悬空镜像',
    message: `确定清理 ${danglingImageRows.value.length} 个悬空镜像吗？${forceRemove.value ? '将使用强制删除。' : ''}`,
    confirmText: '立即清理',
    type: 'warning',
    action: async () => {
      await doPruneDanglingImages()
    },
  })
}

onMounted(() => {
  void loadInstances()
  void loadLocalImages()
})

watch(
  () => imageVersionRows.value.map((row: ImageVersionRow) => row.imageRef),
  () => {
    syncSelectedRefs()
  },
  { immediate: true },
)
</script>

<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center text-sm text-gray-500">
      <span class="font-medium">控制台</span>
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-2"><path d="m9 18 6-6-6-6"/></svg>
      <span class="font-medium text-gray-900">镜像管理</span>
    </div>
  </header>

  <main class="flex-1 p-6 overflow-auto">
    <div class="max-w-5xl mx-auto rounded-xl border border-slate-200 bg-white p-5">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 class="text-base font-semibold text-slate-900">镜像版本管理</h2>
          <p class="mt-1 text-sm text-slate-500">查看和清理本地镜像版本，避免磁盘空间被占满。</p>
          <p class="mt-1 text-xs text-slate-400">
            共 {{ imageVersionRows.length }} 个版本，约 {{ formatImageSize(totalImageSize) }}
          </p>
        </div>
        <div class="flex gap-2">
          <button
            class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            :disabled="loadingImages"
            @click="loadLocalImages"
          >{{ loadingImages ? '刷新中...' : '刷新列表' }}</button>
          <button
            class="rounded-lg border border-amber-300 px-4 py-2 text-sm font-medium text-amber-700 hover:bg-amber-50 disabled:opacity-50"
            :disabled="pruningDangling || danglingImageRows.length === 0"
            @click="pruneDanglingImages"
          >{{ pruningDangling ? '清理中...' : `清理悬空(${danglingImageRows.length})` }}</button>
          <button
            class="rounded-lg border border-rose-300 px-4 py-2 text-sm font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-50"
            :disabled="batchRemoving || selectedCount === 0"
            @click="removeSelectedImageVersions"
          >{{ batchRemoving ? '批量删除中...' : `批量删除(${selectedCount})` }}</button>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap gap-3">
        <label class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
          <input v-model="forceRemove" type="checkbox" class="h-4 w-4" />
          <span class="text-sm text-slate-700">强制删除镜像（镜像被占用时再启用）</span>
        </label>
        <label class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
          <input v-model="onlyDangling" type="checkbox" class="h-4 w-4" />
          <span class="text-sm text-slate-700">只看悬空镜像</span>
        </label>
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索 tag / 镜像 ID"
          class="min-w-[240px] rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
        />
      </div>

      <div class="mt-4 overflow-hidden rounded-lg border border-slate-200">
        <table class="min-w-full text-sm">
          <thead class="bg-slate-50 text-slate-600">
            <tr>
              <th class="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  :checked="isAllFilteredSelected"
                  class="h-4 w-4"
                  @change="toggleSelectAllFiltered"
                />
              </th>
              <th class="px-4 py-3 text-left">仓库 / 版本</th>
              <th class="px-4 py-3 text-left">镜像 ID</th>
              <th class="px-4 py-3 text-left">大小</th>
              <th class="px-4 py-3 text-left">创建时间</th>
              <th class="px-4 py-3 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingImages">
              <td colspan="6" class="px-4 py-6 text-center text-slate-500">正在加载镜像列表...</td>
            </tr>
            <tr v-else-if="filteredImageVersionRows.length === 0">
              <td colspan="6" class="px-4 py-6 text-center text-slate-500">暂无本地镜像版本</td>
            </tr>
            <template v-for="group in groupedImageRows" :key="group.repository">
              <tr class="border-t border-slate-100 bg-slate-50/70">
                <td colspan="6" class="px-4 py-2">
                  <button
                    type="button"
                    class="w-full flex items-center justify-between text-left text-xs text-slate-600 font-semibold"
                    @click="toggleGroup(group.repository)"
                  >
                    <span>{{ group.repository }} ({{ group.rows.length }})</span>
                    <span>{{ expandedRepoGroups[group.repository] ? '收起' : '展开' }}</span>
                  </button>
                </td>
              </tr>
              <tr
                v-for="row in group.rows"
                v-show="expandedRepoGroups[group.repository]"
                :key="`${row.imageId}-${row.imageRef}`"
                class="border-t border-slate-100"
              >
                <td class="px-4 py-3 align-top">
                  <input
                    type="checkbox"
                    :checked="selectedImageRefs.includes(row.imageRef)"
                    :disabled="isImageInUse(row.imageRef) || batchRemoving"
                    class="h-4 w-4"
                    @change="toggleSelectImageRef(row.imageRef)"
                  />
                </td>
                <td class="px-4 py-3">
                  <div class="font-medium text-slate-800">{{ row.tag }}</div>
                  <div class="text-xs text-slate-500">{{ row.imageRef }}</div>
                  <div v-if="isImageInUse(row.imageRef)" class="text-xs text-amber-600 mt-1">
                    占用实例：{{ getUsingInstanceNames(row.imageRef) }}
                  </div>
                </td>
                <td class="px-4 py-3 text-slate-500">{{ row.imageId }}</td>
                <td class="px-4 py-3 text-slate-500">{{ formatImageSize(row.size) }}</td>
                <td class="px-4 py-3 text-slate-500">{{ formatCreatedAt(row.created) }}</td>
                <td class="px-4 py-3 text-right">
                  <button
                    class="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                    :disabled="removingImageRef === row.imageRef || isImageInUse(row.imageRef) || batchRemoving"
                    @click="removeImageVersion(row.imageRef)"
                  >{{ removingImageRef === row.imageRef ? '删除中...' : '删除' }}</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </main>

  <Toast />

  <ConfirmModal
    :show="confirmModal.show"
    :title="confirmModal.title"
    :message="confirmModal.message"
    :confirm-text="confirmModal.confirmText"
    :type="confirmModal.type"
    :loading="confirmModal.loading"
    @confirm="handleConfirm"
    @cancel="closeConfirm"
  />
</template>
