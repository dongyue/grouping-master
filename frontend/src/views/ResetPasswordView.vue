<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { resetPassword } from '../api/auth'

const route = useRoute()
const router = useRouter()

const password = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  success.value = ''
  const token = route.query.token
  if (!token) {
    error.value = '缺少重置令牌'
    return
  }
  loading.value = true
  try {
    await resetPassword({ token, new_password: password.value })
    success.value = '密码重置成功'
    setTimeout(() => router.push('/login'), 2000)
  } catch (err) {
    console.error('重置密码错误:', err)
    error.value = err.response?.data?.detail || '操作失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-card">
    <h1 class="page-title">重置密码</h1>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>
    <form @submit.prevent="handleSubmit" v-if="!success">
      <div class="form-group">
        <label>新密码</label>
        <input v-model="password" type="password" required placeholder="至少8位" />
      </div>
      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? '重置中...' : '重置密码' }}
      </button>
    </form>
  </div>
</template>
