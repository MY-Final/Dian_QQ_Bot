import { ref, computed } from 'vue'

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

const toasts = ref<ToastMessage[]>([])

let idCounter = 0

export function show(message: string, type: ToastMessage['type'] = 'info', duration = 3000) {
  const id = `toast-${++idCounter}`
  const toast: ToastMessage = {
    id,
    type,
    message,
    duration,
  }
  toasts.value.push(toast)
  
  if (duration > 0) {
    setTimeout(() => remove(id), duration)
  }
  
  return id
}

export function remove(id: string) {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

export function success(message: string, duration?: number) {
  return show(message, 'success', duration)
}

export function error(message: string, duration?: number) {
  return show(message, 'error', duration)
}

export function warning(message: string, duration?: number) {
  return show(message, 'warning', duration)
}

export function info(message: string, duration?: number) {
  return show(message, 'info', duration)
}

export function useToast() {
  const toastsComputed = computed(() => toasts.value)
  
  return {
    toasts: toastsComputed,
    show,
    success,
    error,
    warning,
    info,
    remove,
  }
}
