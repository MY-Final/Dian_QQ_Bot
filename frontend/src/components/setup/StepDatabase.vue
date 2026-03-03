<script setup lang="ts">
import type { DatabaseConfig } from '@/types/setup'

interface Props {
  dbConfig: DatabaseConfig
  dbMode: boolean
  dbConnected: boolean
  testingConnection: boolean
  showDbPassword: boolean
}

interface Emits {
  (e: 'update:dbConfig', value: DatabaseConfig): void
  (e: 'toggle:dbMode'): void
  (e: 'toggle:password', field: 'db'): void
  (e: 'test'): void
  (e: 'submit'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

function updateField<K extends keyof DatabaseConfig>(field: K, value: DatabaseConfig[K]) {
  emit('update:dbConfig', { ...props.dbConfig, [field]: value })
}

function handleSubmit() {
  // 直接触发 submit 事件，由父组件验证
  emit('submit')
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <!-- 数据库模式切换 -->
    <div class="flex items-center justify-between bg-white/40 p-5 rounded-2xl border border-white/60">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-pink-500 border border-white shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          </svg>
        </div>
        <div>
          <h3 class="text-[13px] font-bold text-slate-800">数据库部署模式</h3>
          <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
            当前：{{ dbMode ? '使用外部 PostgreSQL 服务' : '内置 PostgreSQL (Docker)' }}
          </p>
        </div>
      </div>
      <label class="relative inline-flex items-center cursor-pointer">
        <input 
          type="checkbox" 
          :checked="dbMode" 
          @change="emit('toggle:dbMode')"
          class="sr-only peer"
        >
        <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-pink-500"></div>
      </label>
    </div>
    
    <!-- 连接状态提示 -->
    <div v-if="dbMode" class="flex items-center justify-center p-3 rounded-xl border-2 transition-all"
      :class="dbConnected ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'">
      <div class="flex items-center space-x-2">
        <svg v-if="dbConnected" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-green-600">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-600">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span class="text-xs font-bold" :class="dbConnected ? 'text-green-700' : 'text-amber-700'">
          {{ dbConnected ? '✓ 数据库已连接成功' : '⚠ 未测试连接，请先测试数据库连接' }}
        </span>
      </div>
    </div>

    <!-- 数据库配置表单 -->
    <div class="grid grid-cols-2 gap-x-6 gap-y-4">
      <div class="space-y-1.5 col-span-2 sm:col-span-1">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">主机地址 (Host)</label>
        <input 
          type="text" 
          :value="dbConfig.host"
          @input="updateField('host', ($event.target as HTMLInputElement).value)"
          :readonly="!dbMode"
          :class="[
            'w-full rounded-xl px-4 py-3 outline-none text-[13px] font-medium transition-all',
            dbMode ? 'bg-white border border-white focus:ring-4 focus:ring-pink-50/50 text-slate-700' : 'bg-white/50 border border-white/80 text-slate-400 cursor-not-allowed'
          ]"
        >
      </div>
      <div class="space-y-1.5 col-span-2 sm:col-span-1">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">端口 (Port)</label>
        <input 
          type="number" 
          :value="dbConfig.port"
          @input="updateField('port', Number(($event.target as HTMLInputElement).value))"
          :readonly="!dbMode"
          :class="[
            'w-full rounded-xl px-4 py-3 outline-none text-[13px] font-medium transition-all',
            dbMode ? 'bg-white border border-white focus:ring-4 focus:ring-pink-50/50 text-slate-700' : 'bg-white/50 border border-white/80 text-slate-400 cursor-not-allowed'
          ]"
        >
      </div>
      <div class="space-y-1.5">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">数据库名称</label>
        <input 
          type="text" 
          :value="dbConfig.database"
          @input="updateField('database', ($event.target as HTMLInputElement).value)"
          :readonly="!dbMode"
          :class="[
            'w-full rounded-xl px-4 py-3 outline-none text-[13px] font-medium transition-all',
            dbMode ? 'bg-white border border-white focus:ring-4 focus:ring-pink-50/50 text-slate-700' : 'bg-white/50 border border-white/80 text-slate-400 cursor-not-allowed'
          ]"
        >
      </div>
      <div class="space-y-1.5">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">用户名</label>
        <input 
          type="text" 
          :value="dbConfig.username"
          @input="updateField('username', ($event.target as HTMLInputElement).value)"
          :readonly="!dbMode"
          :class="[
            'w-full rounded-xl px-4 py-3 outline-none text-[13px] font-medium transition-all',
            dbMode ? 'bg-white border border-white focus:ring-4 focus:ring-pink-50/50 text-slate-700' : 'bg-white/50 border border-white/80 text-slate-400 cursor-not-allowed'
          ]"
        >
      </div>
      <div class="space-y-1.5 col-span-2">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">数据库密码</label>
        <div class="relative w-full">
          <input 
            :type="showDbPassword ? 'text' : 'password'" 
            :value="dbConfig.password"
            @input="updateField('password', ($event.target as HTMLInputElement).value)"
            placeholder="请输入密码" 
            class="w-full bg-white border border-white rounded-xl px-4 py-3 pr-12 outline-none focus:ring-4 focus:ring-pink-50/50 text-[13px] font-medium text-slate-700 transition-all"
          >
          <button 
            type="button" 
            @click="emit('toggle:password', 'db')" 
            class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500 transition-colors focus:outline-none z-10 flex items-center justify-center min-w-[24px] min-h-[24px]"
          >
            <svg v-if="showDbPassword" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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

    <!-- 操作按钮 -->
    <div class="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
      <button 
        type="button" 
        @click="emit('test')" 
        :disabled="testingConnection"
        class="flex items-center text-[12px] font-bold text-slate-500 hover:text-pink-600 transition-colors px-4 py-2 disabled:opacity-50"
      >
        <svg 
          :class="['w-4 h-4 mr-2', { 'animate-spin': testingConnection }]" 
          xmlns="http://www.w3.org/2000/svg" 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          stroke-width="2" 
          stroke-linecap="round" 
          stroke-linejoin="round"
        >
          <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
          <path d="M3 3v5h5"/>
          <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
          <path d="M16 16h5v5"/>
        </svg>
        测试数据库连接
      </button>
      <button 
        type="submit"
        :disabled="testingConnection"
        class="w-full sm:w-auto px-10 py-3.5 bg-slate-900 text-white rounded-2xl font-bold text-[13px] hover:bg-pink-600 transition-all shadow-xl shadow-slate-200 active:scale-95 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
      >
        下一步：配置管理员
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
          <path d="M5 12h14"/>
          <path d="m12 5 7 7-7 7"/>
        </svg>
      </button>
    </div>
  </form>
</template>
