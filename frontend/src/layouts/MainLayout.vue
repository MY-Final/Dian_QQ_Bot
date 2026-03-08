<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { clearAuthSession } from '@/api'

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const mobile_menu_open = ref(false)

const menuItems = [
  { path: '/', name: '实例管理', icon: 'grid' },
  { path: '/logs', name: '实时日志', icon: 'terminal' },
  { path: '/settings', name: '系统设置', icon: 'settings' },
]

function toggleSidebar() {
  collapsed.value = !collapsed.value
}

function toggleMobileMenu() {
  mobile_menu_open.value = !mobile_menu_open.value
}

async function logout(): Promise<void> {
  clearAuthSession()
  await router.replace('/login')
}

watch(
  () => route.fullPath,
  () => {
    mobile_menu_open.value = false
  },
)
</script>

<template>
  <div class="flex h-screen bg-slate-50">
    <div
      v-if="mobile_menu_open"
      class="fixed inset-0 z-30 bg-slate-900/35 backdrop-blur-[1px] lg:hidden"
      @click="mobile_menu_open = false"
    ></div>

    <!-- Sidebar -->
    <aside
      :class="[
        'fixed inset-y-0 left-0 z-40 bg-white/95 border-r border-slate-200 flex flex-col shrink-0 transition-all duration-300 lg:static lg:translate-x-0',
        collapsed ? 'w-16' : 'w-56',
        mobile_menu_open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      ]"
    >
      <!-- Logo -->
      <div class="h-16 flex items-center px-4 border-b border-slate-200">
        <div class="w-8 h-8 bg-pink-500 rounded-lg flex items-center justify-center text-white font-bold">
          D
        </div>
        <span v-if="!collapsed" class="ml-3 font-semibold text-slate-800">Dian Bot</span>
      </div>

      <!-- Nav -->
      <nav class="flex-1 py-4 px-2">
        <RouterLink
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center px-3 py-2.5 rounded-lg text-sm font-medium mb-1 transition-colors',
            route.path === item.path
              ? 'bg-pink-50 text-pink-600'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          ]"
        >
          <svg v-if="item.icon === 'grid'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
          <svg v-else-if="item.icon === 'terminal'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/></svg>
          <svg v-else-if="item.icon === 'settings'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          <span v-if="!collapsed" class="ml-3">{{ item.name }}</span>
        </RouterLink>
      </nav>

      <!-- Footer -->
      <div class="p-3 border-t border-slate-200">
        <button
          @click="logout"
          class="mb-2 w-full flex items-center justify-center py-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/><path d="M13 5V3a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v18a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2"/></svg>
          <span v-if="!collapsed" class="ml-2 text-sm">退出登录</span>
        </button>
        <div v-if="!collapsed" class="text-xs text-slate-400 mb-2 text-center">
          点点 🐱
        </div>
        <button
          @click="toggleSidebar"
          class="w-full flex items-center justify-center py-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg"
        >
          <svg v-if="collapsed" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="relative flex-1 flex flex-col min-w-0 overflow-hidden">
      <button
        class="fixed bottom-5 right-5 z-20 h-11 w-11 rounded-full border border-slate-200 bg-white text-slate-700 shadow-lg lg:hidden"
        @click="toggleMobileMenu"
        aria-label="切换菜单"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-auto">
          <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
      <router-view />
    </div>
  </div>
</template>
