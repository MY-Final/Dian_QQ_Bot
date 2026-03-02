import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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

export default router
