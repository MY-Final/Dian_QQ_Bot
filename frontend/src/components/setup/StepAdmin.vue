<script setup lang="ts">
import type { AdminConfig } from '@/types/setup'

interface Props {
  adminConfig: AdminConfig
  showAdminPassword: boolean
  showConfirmPassword: boolean
  creating: boolean
}

interface Emits {
  (e: 'update:adminConfig', value: AdminConfig): void
  (e: 'toggle:password', field: 'admin' | 'confirm'): void
  (e: 'prev'): void
  (e: 'submit'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

function updateField<K extends keyof AdminConfig>(field: K, value: AdminConfig[K]) {
  emit('update:adminConfig', { ...props.adminConfig, [field]: value })
}
</script>

<template>
  <form class="space-y-6">
    <div class="space-y-1.5 text-center mb-6">
      <div class="inline-flex items-center justify-center w-12 h-12 bg-slate-100 rounded-full text-slate-600 mb-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
          <path d="m9 12 2 2 4-4"/>
        </svg>
      </div>
      <h3 class="text-sm font-bold text-slate-800">设置超级管理员</h3>
      <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider">该账号将拥有系统的最高控制权限</p>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-1.5 col-span-2">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">管理员用户名</label>
        <input 
          type="text" 
          :value="adminConfig.username"
          @input="updateField('username', ($event.target as HTMLInputElement).value)"
          placeholder="例如：admin" 
          class="w-full bg-white border border-white rounded-xl px-4 py-3 outline-none focus:ring-4 focus:ring-pink-50/50 text-[13px] font-medium text-slate-700 transition-all"
        >
      </div>
      <div class="space-y-1.5 col-span-2">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">电子邮箱</label>
        <input 
          type="email" 
          :value="adminConfig.email"
          @input="updateField('email', ($event.target as HTMLInputElement).value)"
          placeholder="admin@example.com" 
          class="w-full bg-white border border-white rounded-xl px-4 py-3 outline-none focus:ring-4 focus:ring-pink-50/50 text-[13px] font-medium text-slate-700 transition-all"
        >
      </div>
      <div class="space-y-1.5">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">登录密码</label>
        <div class="relative w-full">
          <input 
            :type="showAdminPassword ? 'text' : 'password'" 
            :value="adminConfig.password"
            @input="updateField('password', ($event.target as HTMLInputElement).value)"
            maxlength="72"
            placeholder="••••••••" 
            class="w-full bg-white border border-white rounded-xl px-4 py-3 pr-12 outline-none focus:ring-4 focus:ring-pink-50/50 text-[13px] font-medium text-slate-700 transition-all"
          >
          <button 
            type="button" 
            @click="emit('toggle:password', 'admin')" 
            class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500 transition-colors focus:outline-none z-10 flex items-center justify-center min-w-[24px] min-h-[24px]"
          >
            <svg v-if="showAdminPassword" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>
              <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/>
              <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/>
              <line x1="2" y1="2" x2="22" y2="22"/>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2c-4 0-8 4-8 9 0 3 2 6 5 8 1-2 2-3 3-3s2 1 3 3c3-2 5-5 5-8 0-5-4-9-8-9z"/>
              <circle cx="9" cy="9" r="1.5"/>
              <circle cx="15" cy="9" r="1.5"/>
              <path d="M12 14c-1.5 0-3 1-3 2"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="space-y-1.5">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">确认密码</label>
        <div class="relative w-full">
          <input 
            :type="showConfirmPassword ? 'text' : 'password'" 
            :value="adminConfig.confirmPassword"
            @input="updateField('confirmPassword', ($event.target as HTMLInputElement).value)"
            maxlength="72"
            placeholder="••••••••" 
            class="w-full bg-white border border-white rounded-xl px-4 py-3 pr-12 outline-none focus:ring-4 focus:ring-pink-50/50 text-[13px] font-medium text-slate-700 transition-all"
          >
          <button 
            type="button" 
            @click="emit('toggle:password', 'confirm')" 
            class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500 transition-colors focus:outline-none z-10 flex items-center justify-center min-w-[24px] min-h-[24px]"
          >
            <svg v-if="showConfirmPassword" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>
              <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/>
              <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/>
              <line x1="2" y1="2" x2="22" y2="22"/>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2c-4 0-8 4-8 9 0 3 2 6 5 8 1-2 2-3 3-3s2 1 3 3c3-2 5-5 5-8 0-5-4-9-8-9z"/>
              <circle cx="9" cy="9" r="1.5"/>
              <circle cx="15" cy="9" r="1.5"/>
              <path d="M12 14c-1.5 0-3 1-3 2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div class="pt-6 flex items-center justify-between">
      <button 
        type="button" 
        @click="emit('prev')" 
        class="text-[12px] font-bold text-slate-400 hover:text-slate-600 transition-colors flex items-center"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-1">
          <path d="m15 18-6-6 6-6"/>
        </svg>
        返回上一步
      </button>
      <button 
        type="button"
        @click="emit('submit')"
        :disabled="creating"
        class="px-10 py-3.5 bg-slate-900 text-white rounded-2xl font-bold text-[13px] hover:bg-pink-600 transition-all shadow-xl shadow-slate-200 active:scale-95 flex items-center disabled:opacity-50"
      >
        <svg v-if="creating" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        {{ creating ? '创建中...' : '完成初始化' }}
        <svg v-if="!creating" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
      </button>
    </div>
  </form>
</template>
