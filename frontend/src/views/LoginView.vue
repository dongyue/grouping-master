<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login({ username: username.value, password: password.value })
    router.push('/')
  } catch (err) {
    console.error('登录错误:', err)
    error.value = err.response?.data?.detail || '登录失败，请检查账号密码是否正确'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-card">
    <h1 class="page-title">登录</h1>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>账号名</label>
        <input v-model="username" type="text" required placeholder="输入账号名" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" required placeholder="输入密码" />
      </div>
      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>
    <div class="form-footer">
      <a href="/register" @click.prevent="router.push('/register')">注册账号</a>
      <span style="margin: 0 10px">|</span>
      <a href="/forgot-password" @click.prevent="router.push('/forgot-password')">忘记密码</a>
    </div>
  </div>
</template>
