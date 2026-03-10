<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Toast from '@/components/ui/Toast.vue'
import { useSetupWizard } from '@/composables/useSetupWizard'
import { useToast } from '@/composables/useToast'
import StepDatabase from '@/components/setup/StepDatabase.vue'
import StepInitDb from '@/components/setup/StepInitDb.vue'
import StepAdmin from '@/components/setup/StepAdmin.vue'

const router = useRouter()
const toast = useToast()
const {
  currentStep,
  dbMode,
  dbConfig,
  adminConfig,
  dbConnected,
  dbInitialized,
  testingConnection,
  initializingDb,
  creatingAdmin,
  showDbPassword,
  showAdminPassword,
  showConfirmPassword,
  toggleDbMode,
  loadInternalDbDefaults,
  togglePassword,
  testConnection,
  nextStep,
  prevStep,
  getStepStatus,
} = useSetupWizard()

// 检查是否已初始化
onMounted(async () => {
  try {
    await loadInternalDbDefaults()
    const response = await fetch('/api/v1/setup/status')
    const data = await response.json()
    if (data.data?.initialized) {
      router.push('/')
    }
  } catch {
    showToast('初始化状态检查失败，请稍后重试', true)
  }
})

// 显示 Toast
function showToast(message: string, isError: boolean) {
  if (isError) {
    toast.error(message)
    return
  }
  toast.success(message)
}

// 处理下一步
async function handleNext() {
  const result = await nextStep()
  if (!result.success && 'message' in result && result.message) {
    showToast(result.message, true)
  }
}

// 进入控制台
function enterDashboard() {
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-6 relative overflow-hidden bg-slate-50">
    <!-- 背景装饰 -->
    <div class="fixed top-[-10%] right-[-5%] w-[40%] h-[40%] bg-pink-100/20 rounded-full blur-[120px] -z-10"></div>
    <div class="fixed bottom-[-10%] left-[-5%] w-[40%] h-[40%] bg-blue-100/20 rounded-full blur-[120px] -z-10"></div>

    <div class="w-full max-w-2xl relative">
      <!-- Logo & Title -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-tr from-pink-500 to-rose-400 rounded-2xl text-white shadow-xl shadow-pink-100 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2c-4 0-8 4-8 9 0 3 2 6 5 8 1-2 2-3 3-3s2 1 3 3c3-2 5-5 5-8 0-5-4-9-8-9z"/>
            <circle cx="9" cy="9" r="1.5"/>
            <circle cx="15" cy="9" r="1.5"/>
            <path d="M12 14c-1.5 0-3 1-3 2"/>
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight">Dian_Bot 系统安装</h1>
        <p class="text-slate-500 text-[13px] mt-2 font-medium">欢迎使用！请完成以下配置以初始化您的机器人系统。</p>
      </div>

      <!-- 进度条 -->
      <div class="flex items-center justify-center mb-10 space-x-4">
        <div class="flex items-center space-x-2">
          <span 
            :class="[
              'w-2.5 h-2.5 rounded-full transition-all duration-500',
              getStepStatus(1) === 'active' ? 'bg-pink-500 shadow-[0_0_0_4px_rgba(244,63,94,0.15)]' :
              getStepStatus(1) === 'completed' ? 'bg-pink-500' : 'bg-slate-200'
            ]"
          ></span>
          <span 
            :class="[
              'text-[11px] font-bold uppercase tracking-widest transition-colors',
              getStepStatus(1) === 'active' || getStepStatus(1) === 'completed' ? 'text-slate-800' : 'text-slate-400'
            ]"
          >
            欢迎
          </span>
        </div>
        <div class="w-12 h-[1px] bg-slate-200"></div>
        <div class="flex items-center space-x-2">
          <span 
            :class="[
              'w-2.5 h-2.5 rounded-full transition-all duration-500',
              getStepStatus(2) === 'active' ? 'bg-pink-500 shadow-[0_0_0_4px_rgba(244,63,94,0.15)]' :
              getStepStatus(2) === 'completed' ? 'bg-pink-500' : 'bg-slate-200'
            ]"
          ></span>
          <span 
            :class="[
              'text-[11px] font-bold uppercase tracking-widest transition-colors',
              getStepStatus(2) === 'active' || getStepStatus(2) === 'completed' ? 'text-slate-800' : 'text-slate-400'
            ]"
          >
            数据库配置
          </span>
        </div>
        <div class="w-12 h-[1px] bg-slate-200"></div>
        <div class="flex items-center space-x-2">
          <span 
            :class="[
              'w-2.5 h-2.5 rounded-full transition-all duration-500',
              getStepStatus(3) === 'active' ? 'bg-pink-500 shadow-[0_0_0_4px_rgba(244,63,94,0.15)]' :
              getStepStatus(3) === 'completed' ? 'bg-pink-500' : 'bg-slate-200'
            ]"
          ></span>
          <span 
            :class="[
              'text-[11px] font-bold uppercase tracking-widest transition-colors',
              getStepStatus(3) === 'active' || getStepStatus(3) === 'completed' ? 'text-slate-800' : 'text-slate-400'
            ]"
          >
            初始化表
          </span>
        </div>
        <div class="w-12 h-[1px] bg-slate-200"></div>
        <div class="flex items-center space-x-2">
          <span 
            :class="[
              'w-2.5 h-2.5 rounded-full transition-all duration-500',
              getStepStatus(4) === 'active' ? 'bg-pink-500 shadow-[0_0_0_4px_rgba(244,63,94,0.15)]' :
              getStepStatus(4) === 'completed' ? 'bg-pink-500' : 'bg-slate-200'
            ]"
          ></span>
          <span 
            :class="[
              'text-[11px] font-bold uppercase tracking-widest transition-colors',
              getStepStatus(4) === 'active' || getStepStatus(4) === 'completed' ? 'text-slate-800' : 'text-slate-400'
            ]"
          >
            管理员
          </span>
        </div>
        <div class="w-12 h-[1px] bg-slate-200"></div>
        <div class="flex items-center space-x-2">
          <span 
            :class="[
              'w-2.5 h-2.5 rounded-full transition-all duration-500',
              getStepStatus(5) === 'active' ? 'bg-pink-500 shadow-[0_0_0_4px_rgba(244,63,94,0.15)]' :
              getStepStatus(5) === 'completed' ? 'bg-pink-500' : 'bg-slate-200'
            ]"
          ></span>
          <span 
            :class="[
              'text-[11px] font-bold uppercase tracking-widest transition-colors',
              getStepStatus(5) === 'active' || getStepStatus(5) === 'completed' ? 'text-slate-800' : 'text-slate-400'
            ]"
          >
            完成
          </span>
        </div>
      </div>

      <!-- 安装面板 -->
      <div class="glass-card rounded-[2.5rem] p-10 min-h-[520px] flex flex-col justify-center bg-white/70 backdrop-blur-xl border border-white/80 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.05)]">
        
        <!-- 步骤 1: 欢迎 -->
        <div v-show="currentStep === 1" class="text-center py-8">
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
            整个过程大约需要 2 分钟。
          </p>
          <button 
            @click="handleNext"
            class="inline-flex items-center px-12 py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-2xl font-bold text-[13px] hover:shadow-lg hover:shadow-pink-200 transition-all active:scale-95"
          >
            开始配置
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
              <path d="M5 12h14"/>
              <path d="m12 5 7 7-7 7"/>
            </svg>
          </button>
        </div>

        <!-- 步骤 2: 数据库配置 -->
        <StepDatabase
          v-show="currentStep === 2"
          :db-config="dbConfig"
          :db-mode="dbMode"
          :db-connected="dbConnected"
          :testing-connection="testingConnection"
          :show-db-password="showDbPassword"
          @update:db-config="Object.assign(dbConfig, $event)"
          @toggle:db-mode="toggleDbMode"
          @toggle:password="togglePassword"
          @test="testConnection"
          @submit="handleNext"
        />

        <!-- 步骤 3: 初始化数据库 -->
        <StepInitDb
          v-show="currentStep === 3"
          :db-initialized="dbInitialized"
          :initializing="initializingDb"
          @initialize="handleNext"
          @prev="prevStep"
        />

        <!-- 步骤 4: 管理员配置 -->
        <StepAdmin
          v-show="currentStep === 4"
          :admin-config="adminConfig"
          :show-admin-password="showAdminPassword"
          :show-confirm-password="showConfirmPassword"
          :creating="creatingAdmin"
          @update:admin-config="Object.assign(adminConfig, $event)"
          @toggle:password="togglePassword"
          @prev="prevStep"
          @submit="handleNext"
        />

        <!-- 步骤 5: 安装成功 -->
        <div v-show="currentStep === 5" class="transition-all duration-500 text-center py-8">
          <div class="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6 text-green-500 shadow-inner">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <h3 class="text-xl font-bold text-slate-800 mb-2">系统初始化完成！🎉</h3>
          <p class="text-slate-500 text-[13px] mb-10 max-w-[280px] mx-auto leading-relaxed">
            系统已准备就绪。您现在可以登录控制台开始管理您的 QQ 机器人实例了。<br/>
            <span class="text-pink-500 font-medium">献给点点 🐱💕</span>
          </p>
          <button 
            @click="enterDashboard" 
            class="inline-flex items-center px-12 py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-2xl font-bold text-[13px] hover:shadow-lg hover:shadow-pink-200 transition-all active:scale-95"
          >
            进入控制台
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
          </button>
        </div>

      </div>

      <p class="text-center mt-8 text-[11px] text-slate-400 font-medium">
        &copy; 2024 Dian Project. 如果遇到安装问题，请参阅官方文档。
      </p>
    </div>

    <Toast />
  </div>
</template>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 20px 50px -12px rgba(0, 0, 0, 0.05);
}

input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
