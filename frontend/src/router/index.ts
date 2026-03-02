import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/InstanceList.vue'),
    },
    {
      path: '/create',
      name: 'create',
      component: () => import('@/views/InstanceCreate.vue'),
    },
    {
      path: '/instance/:id',
      name: 'detail',
      component: () => import('@/views/InstanceDetail.vue'),
    },
  ],
})

export default router
