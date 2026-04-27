<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { updateProfile, uploadAvatar } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const nickname = ref(auth.user?.nickname || '')
const error = ref('')
const success = ref('')
const saving = ref(false)
const uploading = ref(false)

const avatarUrl = computed(() => {
  if (auth.user?.avatar_path) {
    return `http://localhost:8000/${auth.user.avatar_path}`
  }
  return null
})

async function handleUpdateProfile() {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    const res = await updateProfile({ nickname: nickname.value })
    auth.user = res.data
    success.value = '个人信息更新成功'
    setTimeout(() => (success.value = ''), 3000)
  } catch (err) {
    console.error('更新资料错误:', err)
    error.value = err.response?.data?.detail || '更新失败'
  } finally {
    saving.value = false
  }
}

async function handleAvatarUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  error.value = ''
  uploading.value = true
  try {
    const res = await uploadAvatar(file)
    auth.user = res.data
  } catch (err) {
    console.error('头像上传错误:', err)
    error.value = err.response?.data?.detail || '头像上传失败'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="page-card">
    <h1 class="page-title">个人设置</h1>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>

    <!-- 头像 -->
    <div style="text-align: center; margin-bottom: 24px;">
      <div
        :style="{
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          margin: '0 auto 10px',
          background: '#e8e8e8',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          fontSize: '28px',
          color: '#999',
        }"
      >
        <img v-if="avatarUrl" :src="avatarUrl" style="width: 100%; height: 100%; object-fit: cover;" />
        <span v-else>{{ auth.user?.nickname?.charAt(0) }}</span>
      </div>
      <label class="upload-btn">
        {{ uploading ? '上传中...' : '更换头像' }}
        <input type="file" accept="image/jpeg,image/png,image/gif" @change="handleAvatarUpload" hidden />
      </label>
    </div>

    <!-- 基本信息 -->
    <div class="info-row">
      <span class="info-label">账号名</span>
      <span class="info-value">{{ auth.user?.username }}</span>
    </div>
    <div class="info-row">
      <span class="info-label">注册时间</span>
      <span class="info-value">{{ auth.user?.created_at?.slice(0, 10) }}</span>
    </div>

    <!-- 修改昵称 -->
    <form @submit.prevent="handleUpdateProfile" style="margin-top: 24px;">
      <div class="form-group">
        <label>昵称 *</label>
        <input v-model="nickname" type="text" required placeholder="你的昵称" />
      </div>
      <button type="submit" class="btn btn-primary" :disabled="saving" style="margin-bottom: 20px;">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </form>

    <!-- 修改密码 -->
    <a href="/settings/change-password" @click.prevent="router.push('/settings/change-password')" class="link-item">修改密码</a>
  </div>
</template>

<style scoped>
.upload-btn {
  display: inline-block;
  font-size: 13px;
  color: #4f46e5;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 6px;
}

.upload-btn:hover {
  background: #eef2ff;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.info-label {
  color: #999;
}

.info-value {
  color: #333;
}

.link-item {
  display: block;
  padding: 10px 0;
  border-top: 1px solid #f0f0f0;
  color: #4f46e5;
  text-decoration: none;
  font-size: 14px;
}
</style>
