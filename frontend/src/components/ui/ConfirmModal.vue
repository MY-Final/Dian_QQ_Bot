<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface ConfirmModalProps {
  show: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
  loading?: boolean
  requireText?: string
  requireTextPlaceholder?: string
}

const props = withDefaults(defineProps<ConfirmModalProps>(), {
  confirmText: '确认',
  cancelText: '取消',
  type: 'warning',
  loading: false,
  requireText: '',
  requireTextPlaceholder: '请输入确认文本',
})

const emit = defineEmits<{
  confirm: [text: string]
  cancel: []
}>()

const confirmInput = ref('')

const canConfirm = computed(() => {
  if (!props.requireText) {
    return true
  }
  return confirmInput.value.trim() === props.requireText.trim()
})

watch(
  () => props.show,
  (visible) => {
    if (visible) {
      confirmInput.value = ''
    }
  },
)

const typeStyles = {
  danger: {
    icon: 'text-red-500',
    bg: 'bg-red-50',
    button: 'bg-red-500 hover:bg-red-600',
  },
  warning: {
    icon: 'text-yellow-500',
    bg: 'bg-yellow-50',
    button: 'bg-yellow-500 hover:bg-yellow-600',
  },
  info: {
    icon: 'text-blue-500',
    bg: 'bg-blue-50',
    button: 'bg-blue-500 hover:bg-blue-600',
  },
}
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div 
        class="absolute inset-0 bg-gray-900/40 backdrop-blur-sm transition-opacity" 
        @click="emit('cancel')"
      ></div>
      
      <!-- Modal -->
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden transform transition-all">
        <div class="p-6">
          <!-- Icon -->
          <div class="mx-auto flex items-center justify-center h-14 w-14 rounded-full mb-4" :class="typeStyles[type].bg">
            <svg v-if="type === 'danger'" xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="typeStyles[type].icon">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
            <svg v-else-if="type === 'warning'" xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="typeStyles[type].icon">
              <circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="typeStyles[type].icon">
              <circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="16" y2="12"/><line x1="12" x2="12.01" y1="8" y2="8"/>
            </svg>
          </div>
          
          <!-- Content -->
          <h3 class="text-lg font-semibold text-center text-gray-900 mb-2">
            {{ title }}
          </h3>
          <p class="text-sm text-center text-gray-500 mb-6">
            {{ message }}
          </p>
          
          <div v-if="requireText" class="mb-4">
            <p class="mb-1 text-xs text-gray-500">请输入 <span class="font-semibold text-gray-700">{{ requireText }}</span> 以确认操作</p>
            <input
              v-model="confirmInput"
              type="text"
              :placeholder="requireTextPlaceholder"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-pink-400 focus:ring-2 focus:ring-pink-100"
            />
          </div>

          <!-- Buttons -->
          <div class="flex gap-3">
            <button
              @click="emit('cancel')"
              :disabled="loading"
              class="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ cancelText }}
            </button>
            <button
              @click="emit('confirm', confirmInput.trim())"
              :disabled="loading || !canConfirm"
              :class="['flex-1 px-4 py-2.5 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed', typeStyles[type].button]"
            >
              <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
