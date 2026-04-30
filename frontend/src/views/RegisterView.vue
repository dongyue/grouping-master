<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { register } from '../api/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = ref({
  username: '',
  nickname: '',
  password: '',
  password_confirm: '',
  email: '',
})
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  if (form.value.password || form.value.password_confirm) {
    if (form.value.password !== form.value.password_confirm) {
      error.value = '两次输入的密码不一致'
      return
    }
    if (form.value.password.length < 8) {
      error.value = '密码长度至少8位'
      return
    }
  }
  loading.value = true
  try {
    const data = {
      username: form.value.username,
      nickname: form.value.nickname,
      password: form.value.password || null,
      password_confirm: form.value.password_confirm || null,
      email: form.value.email || null,
    }
    const res = await register(data)
    auth.user = res.data
    form.value = { username: '', nickname: '', password: '', password_confirm: '', email: '' }
    router.push(route.query.redirect || '/')
  } catch (err) {
    console.error('注册错误:', err)
    error.value = err.response?.data?.detail || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-card">
    <h1 class="page-title">注册账号</h1>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <form @submit.prevent="handleRegister">
      <div class="form-group">
        <label>账号名 *</label>
        <input v-model="form.username" type="text" required placeholder="字母、数字、下划线，3-50位" />
      </div>
      <div class="form-group">
        <label>昵称 *</label>
        <input v-model="form.nickname" type="text" required placeholder="你的昵称" />
      </div>
      <div class="form-group">
        <label>密码 *</label>
        <input v-model="form.password" type="password" placeholder="至少8位" />
      </div>
      <div class="form-group">
        <label>确认密码 *</label>
        <input v-model="form.password_confirm" type="password" placeholder="再次输入密码" />
      </div>
      <div class="form-group">
        <label>备用邮箱 <span class="optional">(可选，用于找回密码)</span></label>
        <input v-model="form.email" type="email" placeholder="your@email.com" />
      </div>
      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? '注册中...' : '注册' }}
      </button>
    </form>
    <div class="form-footer">
      已有账号？<a href="/login" @click.prevent="router.push('/login')">去登录</a>
    </div>
  </div>
</template>
