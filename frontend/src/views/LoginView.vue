<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const enablePasswordReset = import.meta.env.VITE_ENABLE_PASSWORD_RESET !== 'false'

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login({ username: username.value, password: password.value })
    router.push(route.query.redirect || '/')
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
    <h1 class="page-title">分组大师</h1>
    <p class="intro">
      按自定义约束自动平均分组，支持手动拖拽调整，实时追踪成员变动。适用于团建、课程分组、住宿分配等场景。
      <a href="https://github.com/dongyue/grouping-master" target="_blank" rel="noopener">GitHub</a>
    </p>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>账号名</label>
        <input v-model="username" type="text" required placeholder="输入账号名" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="输入密码" />
      </div>
      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>
    <div class="form-footer">
      <a href="/register" @click.prevent="router.push('/register')">注册账号</a>
      <template v-if="enablePasswordReset">
        <span style="margin: 0 10px">|</span>
        <a href="/forgot-password" @click.prevent="router.push('/forgot-password')">忘记密码</a>
      </template>
    </div>
  </div>
</template>

<style scoped>
.intro {
  font-size: 13px;
  color: #888;
  line-height: 1.8;
  margin: -12px 0 20px 0;
}
.intro a {
  color: #4f46e5;
  text-decoration: none;
}
</style>
