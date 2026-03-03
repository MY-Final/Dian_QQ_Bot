<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  dbMode: boolean
  onConfirm: (mode: 'local' | 'remote') => void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

interface Emits {
  (e: 'confirm', mode: 'local' | 'remote'): void
}

const selectedMode = ref<'local' | 'remote'>('local')
</script>

<template>
  <div class="text-center py-8">
    <div class="w-20 h-20 bg-pink-50 rounded-full flex items-center justify-center mx-auto mb-6 text-pink-500">
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2c-4 0-8 4-8 9 0 3 2 6 5 8 1-2 2-3 3-3s2 1 3 3c3-2 5-5 5-8 0-5-4-9-8-9z"/>
        <circle cx="9" cy="9" r="1.5"/>
        <circle cx="15" cy="9" r="1.5"/>
        <path d="M12 14c-1.5 0-3 1-3 2"/>
      </svg>
    </div>
    
    <h3 class="text-xl font-bold text-slate-800 mb-4">欢迎使用 Dian_Bot 🐱</h3>
    <p class="text-slate-500 text-[13px] mb-8 max-w-[320px] mx-auto leading-relaxed">
      这是第一次使用本系统，需要完成初始化配置。<br/>
      请选择部署模式：
    </p>
    
    <!-- 模式选择 -->
    <div class="grid grid-cols-2 gap-4 mb-8">
      <!-- 本地测试 -->
      <div 
        @click="selectedMode = 'local'"
        :class="[
          'p-6 rounded-2xl border-2 cursor-pointer transition-all',
          selectedMode === 'local' 
            ? 'border-pink-500 bg-pink-50' 
            : 'border-gray-200 bg-white hover:border-gray-300'
        ]"
      >
        <div class="w-12 h-12 rounded-xl bg-pink-100 flex items-center justify-center mx-auto mb-3 text-pink-500">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </div>
        <h4 class="font-bold text-slate-800 mb-1">本地测试</h4>
        <p class="text-[11px] text-slate-500">使用 .env 配置的数据库</p>
      </div>
      
      <!-- 远程部署 -->
      <div 
        @click="selectedMode = 'remote'"
        :class="[
          'p-6 rounded-2xl border-2 cursor-pointer transition-all',
          selectedMode === 'remote' 
            ? 'border-pink-500 bg-pink-50' 
            : 'border-gray-200 bg-white hover:border-gray-300'
        ]"
      >
        <div class="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center mx-auto mb-3 text-blue-500">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          </svg>
        </div>
        <h4 class="font-bold text-slate-800 mb-1">远程部署</h4>
        <p class="text-[11px] text-slate-500">手动配置 PostgreSQL 数据库</p>
      </div>
    </div>
    
    <!-- 模式说明 -->
    <div class="bg-slate-50 rounded-xl p-4 mb-8 text-left">
      <p class="text-[11px] text-slate-600 mb-2">
        <strong class="text-slate-800">本地测试：</strong>
        使用 .env 文件中的 DATABASE_URL 配置，适合开发环境。
      </p>
      <p class="text-[11px] text-slate-600">
        <strong class="text-slate-800">远程部署：</strong>
        手动指定 PostgreSQL 服务器地址，适合生产环境。
      </p>
    </div>
    
    <button 
      @click="emit('confirm', selectedMode)"
      class="inline-flex items-center px-12 py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-2xl font-bold text-[13px] hover:shadow-lg hover:shadow-pink-200 transition-all active:scale-95"
    >
      开始配置
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
        <path d="M5 12h14"/>
        <path d="m12 5 7 7-7 7"/>
      </svg>
    </button>
  </div>
</template>
