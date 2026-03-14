import { createRouter, createWebHistory } from 'vue-router'

import { authApi, clearAuthSession, getAccessToken, getCurrentUserFromStorage, setupApi } from '@/api'
import MainLayout from '../layouts/MainLayout.vue'

const SETUP_STATUS_CACHE_MS = 30_000
const AUTH_STATUS_CACHE_MS = 60_000

type SetupStatusCache = {
  initialized: boolean
  timestamp: number
}

let setupStatusCache: SetupStatusCache | null = null
let authStatusCacheTimestamp = 0

async function getSetupInitializedStatus(): Promise<boolean> {
  const now = Date.now()
  if (setupStatusCache && now - setupStatusCache.timestamp < SETUP_STATUS_CACHE_MS) {
    return setupStatusCache.initialized
  }

  const response = await setupApi.getStatus()
  const data = response.data
  const initialized = Boolean(data.data?.initialized)
  setupStatusCache = {
    initialized,
    timestamp: now,
  }
  return initialized
}

async function ensureAuthenticated(): Promise<boolean> {
  const token = getAccessToken()
  if (!token) {
    return false
  }

  const now = Date.now()
  if (getCurrentUserFromStorage() && now - authStatusCacheTimestamp < AUTH_STATUS_CACHE_MS) {
    return true
  }

  try {
    const response = await authApi.me()
    if (!response.data.success || !response.data.data) {
      clearAuthSession()
      return false
    }
    authStatusCacheTimestamp = now
    return true
  } catch {
    clearAuthSession()
    return false
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/setup',
      name: 'setup',
      component: () => import('../views/Setup.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
    },
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('../views/InstanceList.vue'),
        },
        {
          path: 'logs',
          name: 'logs',
          component: () => import('../views/Logs.vue'),
        },
        {
          path: 'images',
          name: 'images',
          component: () => import('../views/ImageManager.vue'),
        },
        {
          path: 'instance/:id',
          name: 'detail',
          component: () => import('../views/InstanceDetail.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/Settings.vue'),
        },
      ],
    },
  ],
})

// 路由守卫：检查初始化状态
router.beforeEach(async (to, _from, next) => {
  // setup 和 login 页面优先处理
  if (to.name === 'setup' || to.name === 'login') {
    if (to.name === 'setup') {
      return next()
    }

    try {
      const initialized = await getSetupInitializedStatus()
      if (!initialized) {
        return next('/setup')
      }
    } catch {
      return next('/setup')
    }

    if (getAccessToken()) {
      return next('/')
    }

    return next()
  }
  
  // 检查是否刚从 setup 完成页面过来
  const justInitialized = sessionStorage.getItem('just_initialized')
  if (justInitialized === 'true') {
    sessionStorage.removeItem('just_initialized')
    return next()
  }
  
  try {
    const initialized = await getSetupInitializedStatus()

    if (!initialized) {
      // 未初始化，重定向到 setup 页面
      return next('/setup')
    }
  } catch {
    // 如果检查失败，也重定向到 setup
    return next('/setup')
  }

  const authenticated = await ensureAuthenticated()
  if (!authenticated) {
    return next('/login')
  }
  
  next()
})

export default router
