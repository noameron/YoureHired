import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserSelectionStore } from '@/stores/userSelection'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'role-selection',
    component: () => import('@/views/RoleSelectionView.vue')
  },
  {
    path: '/practice',
    name: 'practice',
    component: () => import('@/views/PracticeView.vue'),
    beforeEnter: (_to, _from, next) => {
      const store = useUserSelectionStore()
      if (!store.sessionId) {
        next('/')
      } else {
        next()
      }
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
