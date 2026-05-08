import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('../views/ForgotPasswordView.vue'),
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('../views/ResetPasswordView.vue'),
  },
  {
    path: '/activities',
    redirect: '/',
  },
  {
    path: '/activities/create',
    name: 'activity-create',
    component: () => import('../views/CreateActivityView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/activities/:slug/edit',
    name: 'activity-edit',
    component: () => import('../views/ActivityEditView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/activities/:slug/logs',
    name: 'activity-logs',
    component: () => import('../views/ActivityLogsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/activities/:slug',
    name: 'activity-detail',
    component: () => import('../views/ActivityDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings/change-password',
    name: 'change-password',
    component: () => import('../views/ChangePasswordView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.onError((error) => {
  if (error.message.includes('Failed to fetch dynamically imported module')) {
    window.location.reload()
  }
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 首次加载时获取用户状态
  if (!authStore.loaded) {
    await authStore.fetchUser()
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (to.meta.guest && authStore.isLoggedIn) {
    return next('/')
  }

  next()
})

export default router
