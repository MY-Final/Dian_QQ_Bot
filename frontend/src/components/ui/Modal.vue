<script setup lang="ts">
defineProps<{
  show: boolean
  title: string
  subtitle?: string
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-gray-900/30" @click="emit('close')"></div>
      <div class="relative bg-white rounded-3xl shadow-xl w-full max-w-6xl overflow-hidden">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 class="font-semibold text-gray-900">{{ title }}</h3>
            <p v-if="subtitle" class="text-xs text-gray-500 mt-0.5">{{ subtitle }}</p>
          </div>
          <button @click="emit('close')" class="p-1 hover:bg-gray-100 rounded">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
        
        <!-- Content -->
        <div class="p-6">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>
