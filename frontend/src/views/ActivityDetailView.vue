<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getActivity, joinActivity, leaveActivity, deleteActivity } from '../api/activities'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activity = ref(null)
const loading = ref(true)
const error = ref('')
const copied = ref(false)
const joining = ref(false)
const joinError = ref('')
const joinSuccess = ref('')
const leaving = ref(false)
const leaveError = ref('')
const deleting = ref(false)
const deleteError = ref('')
const updated = ref(false)

onMounted(async () => {
  try {
    const res = await getActivity(route.params.slug)
    activity.value = res.data
  } catch (err) {
    console.error('加载活动详情错误:', err)
    if (err.response?.status === 404) {
      error.value = '活动不存在'
    } else {
      error.value = err.response?.data?.detail || '加载失败'
    }
  } finally {
    loading.value = false
  }

  if (route.query.updated === '1') {
    updated.value = true
    router.replace({ query: {} })
    setTimeout(() => (updated.value = false), 3000)
  }
})

function handleCopyLink() {
  const url = window.location.origin + router.resolve({ name: 'activity-detail', params: { slug: route.params.slug } }).href
  navigator.clipboard.writeText(url).then(() => {
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  })
}

async function handleJoin() {
  joining.value = true
  joinError.value = ''
  joinSuccess.value = ''
  try {
    await joinActivity(route.params.slug)
    activity.value.is_member = true
    joinSuccess.value = '加入成功'
    setTimeout(() => (joinSuccess.value = ''), 2000)
  } catch (err) {
    joinError.value = err.response?.data?.detail || '加入失败'
  } finally {
    joining.value = false
  }
}

async function handleLeave() {
  if (!confirm('确定要退出此活动吗？')) return
  leaving.value = true
  leaveError.value = ''
  try {
    await leaveActivity(route.params.slug)
    activity.value.is_member = false
    activity.value.members = activity.value.members.filter(m => m.user_id !== auth.user.id)
    router.push({ name: 'home', query: { left: '1' } })
  } catch (err) {
    leaveError.value = err.response?.data?.detail || '退出失败'
  } finally {
    leaving.value = false
  }
}

async function handleDelete() {
  if (!confirm('确定要删除此活动吗？删除后不可恢复。')) return
  deleting.value = true
  deleteError.value = ''
  try {
    await deleteActivity(route.params.slug)
    router.push({ name: 'home', query: { deleted: '1' } })
  } catch (err) {
    deleteError.value = err.response?.data?.detail || '删除失败'
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="page-card">
    <div v-if="loading" style="text-align: center; color: #999; padding: 40px;">加载中...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else-if="activity">
      <h1 class="page-title">{{ activity.title }}</h1>
      <div class="meta">
        <span class="creator">创建者：{{ activity.creator_nickname }}</span>
        <span class="time">{{ activity.created_at.slice(0, 10) }}</span>
      </div>
      <div class="desc-section">
        <p v-if="activity.description" class="description">{{ activity.description }}</p>
        <p v-else class="description" style="color: #bbb;">暂无描述</p>
      </div>
      <div class="members-section">
        <h3 class="members-title">已加入的成员（{{ activity.members?.length || 0 }}）</h3>
        <div v-if="activity.members?.length" class="members-list">
          <div v-for="member in activity.members" :key="member.user_id" class="member-item">
            <div class="member-avatar">
              <img v-if="member.avatar_path" :src="`http://localhost:8000/${member.avatar_path}`" />
              <span v-else class="avatar-placeholder">{{ member.nickname[0] }}</span>
            </div>
            <span class="member-nickname">{{ member.nickname }}</span>
          </div>
        </div>
        <p v-else class="members-empty">暂无成员</p>
      </div>
      <div v-if="updated" class="success-msg" style="margin-bottom: 12px;">活动信息已更新</div>
      <div v-if="joinError" class="error-msg" style="margin-bottom: 12px;">{{ joinError }}</div>
      <div v-if="joinSuccess" class="success-msg" style="margin-bottom: 12px;">{{ joinSuccess }}</div>
      <div v-if="leaveError" class="error-msg" style="margin-bottom: 12px;">{{ leaveError }}</div>
      <div v-if="deleteError" class="error-msg" style="margin-bottom: 12px;">{{ deleteError }}</div>
      <div class="actions">
        <button v-if="!activity.is_member" class="btn btn-primary" :disabled="joining" @click="handleJoin">
          {{ joining ? '加入中...' : '加入活动' }}
        </button>
        <button v-if="activity.is_member" class="btn btn-secondary" :disabled="leaving" @click="handleLeave">
          {{ leaving ? '退出中...' : '退出活动' }}
        </button>
        <button v-if="activity.is_creator" class="btn btn-secondary" @click="router.push({ name: 'activity-edit', params: { slug: route.params.slug } })">
          编辑活动
        </button>
        <button class="btn btn-secondary" @click="handleCopyLink" style="white-space: nowrap;">
          {{ copied ? '已复制！' : '分享链接' }}
        </button>
        <router-link to="/" class="btn btn-secondary" style="text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap;">
          返回首页
        </router-link>
        <button v-if="activity.is_creator" class="btn btn-danger" :disabled="deleting" @click="handleDelete">
          {{ deleting ? '删除中...' : '删除活动' }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.meta {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.creator {
  font-size: 13px;
  color: #888;
}

.time {
  font-size: 13px;
  color: #bbb;
}

.desc-section {
  margin-bottom: 24px;
}

.description {
  font-size: 14px;
  color: #555;
  line-height: 1.8;
  white-space: pre-wrap;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.actions .btn {
  width: auto;
  flex-shrink: 0;
  padding: 0 20px;
}

.members-section {
  margin-bottom: 24px;
}

.members-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
  font-weight: 600;
}

.members-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.member-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: #e0e0e0;
}

.member-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 12px;
  color: #888;
  font-weight: 600;
  text-transform: uppercase;
}

.member-nickname {
  font-size: 13px;
  color: #333;
}

.members-empty {
  font-size: 13px;
  color: #bbb;
}
</style>
