<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { changePassword } from '../api/auth'

const router = useRouter()
const oldPassword = ref('')
const newPassword = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleChangePassword() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await changePassword({
      old_password: oldPassword.value,
      new_password: newPassword.value,
    })
    success.value = '密码修改成功'
    oldPassword.value = ''
    newPassword.value = ''
  } catch (err) {
    console.error('修改密码错误:', err)
    error.value = err.response?.data?.detail || '修改失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-card">
    <h1 class="page-title">修改密码</h1>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>
    <form @submit.prevent="handleChangePassword">
      <div class="form-group">
        <label>旧密码</label>
        <input v-model="oldPassword" type="password" required placeholder="输入当前密码" />
      </div>
      <div class="form-group">
        <label>新密码</label>
        <input v-model="newPassword" type="password" required placeholder="至少8位" />
      </div>
      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? '修改中...' : '确认修改' }}
      </button>
    </form>
    <div class="form-footer">
      <a href="/settings" @click.prevent="router.push('/settings')">返回设置</a>
    </div>
  </div>
</template>
