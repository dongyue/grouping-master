<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { updateProfile, uploadAvatar, deleteAccount, getUserAttributes, saveUserAttributes } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import ConfirmModal from '../components/ConfirmModal.vue'
import { formatDate } from '../utils/date'

const uploadsUrl = import.meta.env.VITE_UPLOADS_URL || 'http://localhost:8000'

const router = useRouter()
const auth = useAuthStore()

const nickname = ref(auth.user?.nickname || '')
const error = ref('')
const success = ref('')
const saving = ref(false)
const uploading = ref(false)
const deleting = ref(false)
const confirmModal = ref({ show: false, title: '', message: '', onConfirm: null })
const userAttrs = ref({})
const newAttrName = ref('')
const newAttrValue = ref('')
const attrSaving = ref(false)
const showHelp = ref(false)
onMounted(async () => {
  try {
    const res = await getUserAttributes()
    userAttrs.value = res.data.attributes
  } catch {}
})

const avatarUrl = computed(() => {
  if (auth.user?.avatar_path) {
    return `${uploadsUrl}/${auth.user.avatar_path}`
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

async function handleDeleteAccount() {
  confirmModal.value = {
    show: true,
    title: '注销账号',
    message: '确定要注销账号吗？此操作不可撤销，所有数据将被永久删除。',
    onConfirm: async () => {
      error.value = ''
      deleting.value = true
      try {
        await deleteAccount()
        auth.user = null
        router.push('/login')
      } catch (err) {
        console.error('注销错误:', err)
        error.value = err.response?.data?.detail || '注销失败'
      } finally {
        deleting.value = false
      }
    },
  }
}

function addAttr() {
  if (!newAttrName.value.trim() || !newAttrValue.value.trim()) return
  const name = newAttrName.value.trim()
  if (userAttrs.value[name] !== undefined && name !== newAttrName.value) return
  userAttrs.value = { ...userAttrs.value, [name]: newAttrValue.value.trim() }
  newAttrName.value = ''
  newAttrValue.value = ''
  saveAttrs()
}

function updateAttr(name, value) {
  userAttrs.value = { ...userAttrs.value, [name]: value }
  saveAttrs()
}

function deleteAttr(name) {
  const updated = { ...userAttrs.value }
  delete updated[name]
  userAttrs.value = updated
  saveAttrs()
}

async function saveAttrs() {
  attrSaving.value = true
  try {
    await saveUserAttributes(userAttrs.value)
    const res = await getUserAttributes()
    userAttrs.value = res.data.attributes
  } catch {}
  attrSaving.value = false
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
      <span class="info-value">{{ formatDate(auth.user?.created_at) }}</span>
    </div>

    <!-- 修改昵称 -->
    <form @submit.prevent="handleUpdateProfile" style="margin-top: 24px;">
      <div class="form-group">
        <label>昵称 * <a href="#" @click.prevent="showHelp = !showHelp" class="help-link">&#x24D8;</a></label>
        <div v-if="showHelp" class="help-box">
          你在活动中的显示名。参加活动时可修改，修改后会反写回这里，下次加入新活动时自动预填。
        </div>
        <div class="nickname-row">
          <input v-model="nickname" type="text" required placeholder="你的昵称" />
          <button type="submit" class="btn-save" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </form>

    <div class="form-group">
      <label>属性值 <a href="#" @click.prevent="showHelp = !showHelp" class="help-link">&#x24D8;</a></label>
      <div v-if="showHelp" class="help-box">
        这里是各约束属性的个人默认值。参加活动时如有同名属性且值在活动选项中，自动预填。在活动中填写的属性值也会反写回这里。
      </div>
      <div class="attr-list">
        <div v-for="(val, name) in userAttrs" :key="name" class="attr-row">
          <input :value="name" disabled class="attr-name-disabled" />
          <input :value="val" @input="updateAttr(name, $event.target.value)" class="attr-value-input" />
          <button type="button" class="btn-attr-remove" @click="deleteAttr(name)">&times;</button>
        </div>
        <div class="attr-row attr-new">
          <input v-model="newAttrName" type="text" placeholder="属性名" class="attr-name-input" />
          <input v-model="newAttrValue" type="text" placeholder="属性值" class="attr-value-input" />
          <button type="button" class="btn-attr-add" @click="addAttr" :disabled="attrSaving">添加</button>
        </div>
      </div>
    </div>

    <!-- 修改密码 -->
    <a href="/settings/change-password" @click.prevent="router.push('/settings/change-password')" class="link-item">修改密码</a>
    <a href="#" @click.prevent="handleDeleteAccount" class="link-item link-danger" :class="{ disabled: deleting }">
      {{ deleting ? '注销中...' : '注销账号' }}
    </a>
  </div>
  <ConfirmModal
    v-if="confirmModal.show"
    :title="confirmModal.title"
    :message="confirmModal.message"
    @confirm="confirmModal.onConfirm(); confirmModal.show = false"
    @cancel="confirmModal.show = false"
  />
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

.nickname-row {
  display: flex;
  gap: 8px;
}

.nickname-row input {
  flex: 1;
}

.btn-save {
  height: 36px;
  padding: 0 14px;
  border: none;
  border-radius: 6px;
  background: #4f46e5;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  flex-shrink: 0;
}

.btn-save:hover {
  background: #3730a3;
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

.link-danger {
  color: #dc2626;
}

.link-danger.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.attr-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attr-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.attr-name-disabled,
.attr-name-input {
  width: 120px;
  height: 34px;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 13px;
  outline: none;
  flex-shrink: 0;
}

.attr-name-disabled {
  background: #f5f5f5;
  color: #999;
}

.attr-value-input {
  width: 120px;
  height: 34px;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 13px;
  outline: none;
  flex: 1;
}

.attr-value-input:focus,
.attr-name-input:focus {
  border-color: #4f46e5;
}

.btn-attr-remove {
  border: none;
  background: none;
  color: #dc2626;
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
}

.btn-attr-add {
  height: 34px;
  padding: 0 16px;
  border: 1px solid #4f46e5;
  border-radius: 6px;
  background: #4f46e5;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  flex-shrink: 0;
}

.btn-attr-add:hover {
  background: #3730a3;
}

.help-link {
  font-size: 14px;
  color: #999;
  text-decoration: none;
}

.help-link:hover {
  color: #4f46e5;
}

.help-box {
  font-size: 12px;
  color: #888;
  line-height: 1.8;
  padding: 10px 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-bottom: 8px;
}
</style>
