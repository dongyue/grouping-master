<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { forgotPassword } from '../api/auth'

const router = useRouter()
const email = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    const res = await forgotPassword({ email: email.value })
    success.value = res.data.message
  } catch (err) {
    console.error('忘记密码错误:', err)
    error.value = err.response?.data?.detail || '操作失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-card">
    <h1 class="page-title">忘记密码</h1>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>
    <p style="color: #666; font-size: 14px; margin-bottom: 20px; text-align: center;">
      输入注册时填写的备用邮箱，我们将发送重置密码链接。
    </p>
    <form @submit.prevent="handleSubmit" v-if="!success">
      <div class="form-group">
        <label>备用邮箱</label>
        <input v-model="email" type="email" required placeholder="your@email.com" />
      </div>
      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? '发送中...' : '发送重置链接' }}
      </button>
    </form>
    <div class="form-footer">
      <a href="/login" @click.prevent="router.push('/login')">返回登录</a>
    </div>
  </div>
</template>
