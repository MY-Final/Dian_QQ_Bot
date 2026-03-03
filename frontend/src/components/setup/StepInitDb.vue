<script setup lang="ts">
interface Props {
  dbInitialized: boolean
  initializing: boolean
}

interface Emits {
  (e: 'initialize'): void
  (e: 'prev'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()
</script>

<template>
  <div class="text-center py-8">
    <div class="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6 text-blue-500">
      <svg v-if="!dbInitialized && !initializing" xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
      </svg>
      <svg v-else-if="initializing" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
        <path d="M3 3v5h5"/>
        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
        <path d="M16 16h5v5"/>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    </div>
    
    <h3 class="text-lg font-bold text-slate-800 mb-2">
      {{ dbInitialized ? '数据库表创建成功' : (initializing ? '正在初始化数据库...' : '初始化数据库表') }}
    </h3>
    <p class="text-slate-500 text-[13px] mb-8 max-w-[320px] mx-auto leading-relaxed">
      <template v-if="!dbInitialized && !initializing">
        点击按钮创建系统所需的数据库表结构。<br/>
        这将创建 users、system_settings 等表。
      </template>
      <template v-else-if="initializing">
        请稍候，正在创建数据库表...<br/>
        此过程大约需要 10-30 秒。
      </template>
      <template v-else>
        所有数据库表已创建成功！<br/>
        现在可以创建管理员账号了。
      </template>
    </p>
    
    <div class="flex items-center justify-center gap-4">
      <button 
        v-if="!dbInitialized"
        type="button"
        @click="emit('prev')"
        :disabled="initializing"
        class="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl font-bold text-[13px] hover:bg-gray-50 transition-colors disabled:opacity-50"
      >
        返回上一步
      </button>
      <button 
        v-if="!dbInitialized"
        type="button"
        @click="emit('initialize')"
        :disabled="initializing"
        class="px-10 py-3 bg-slate-900 text-white rounded-2xl font-bold text-[13px] hover:bg-pink-600 transition-all shadow-xl shadow-slate-200 active:scale-95 disabled:opacity-50 flex items-center"
      >
        <svg v-if="initializing" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        {{ initializing ? '初始化中...' : '创建表结构' }}
      </button>
      <button 
        v-if="dbInitialized"
        type="button"
        @click="emit('initialize')"
        class="px-10 py-3 bg-slate-900 text-white rounded-2xl font-bold text-[13px] hover:bg-pink-600 transition-all shadow-xl shadow-slate-200 active:scale-95 flex items-center"
      >
        下一步：创建管理员
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
          <path d="M5 12h14"/>
          <path d="m12 5 7 7-7 7"/>
        </svg>
      </button>
    </div>
  </div>
</template>
