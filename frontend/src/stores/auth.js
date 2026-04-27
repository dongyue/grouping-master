import { defineStore } from 'pinia'
import { getCurrentUser, login as loginApi, logout as logoutApi } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loaded: false,
  }),
  getters: {
    isLoggedIn: (state) => !!state.user,
  },
  actions: {
    async fetchUser() {
      try {
        const res = await getCurrentUser()
        this.user = res.data
      } catch {
        this.user = null
      } finally {
        this.loaded = true
      }
    },
    async login(data) {
      const res = await loginApi(data)
      this.user = res.data
      return res.data
    },
    async logout() {
      await logoutApi()
      this.user = null
    },
  },
})
