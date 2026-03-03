import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/setup',
      name: 'setup',
      component: () => import('../views/Setup.vue'),
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
router.beforeEach(async (to, from, next) => {
  // 如果是 setup 页面，直接放行
  if (to.name === 'setup') {
    return next()
  }
  
  // 检查是否刚从 setup 完成页面过来
  const justInitialized = sessionStorage.getItem('just_initialized')
  if (justInitialized === 'true') {
    sessionStorage.removeItem('just_initialized')
    return next()
  }
  
  try {
    // 直接调用接口，后端会自动使用已保存的配置
    const response = await fetch('/api/v1/setup/status')
    const data = await response.json()
    
    if (!data.data?.initialized) {
      // 未初始化，重定向到 setup 页面
      return next('/setup')
    }
  } catch (error) {
    console.error('检查初始化状态失败:', error)
    // 如果检查失败，也重定向到 setup
    return next('/setup')
  }
  
  next()
})

export default router
