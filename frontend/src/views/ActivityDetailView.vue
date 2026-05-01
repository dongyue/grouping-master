<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getActivity, joinActivity, leaveActivity, deleteActivity, kickMember, createGroups, deleteGroups } from '../api/activities'
import ConfirmModal from '../components/ConfirmModal.vue'
import { formatDate } from '../utils/date'

const uploadsUrl = import.meta.env.VITE_UPLOADS_URL || 'http://localhost:8000'

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
const kickingUserId = ref(null)
const kickError = ref('')
const grouping = ref(false)
const groupError = ref('')
const groupSuccess = ref('')
const frozenMsg = ref('')
const showMore = ref(false)
const showKick = ref(false)
const confirmModal = ref({ show: false, title: '', message: '', onConfirm: null })

const hasMoreItems = computed(() => {
  return activity.value?.is_member || activity.value?.is_creator
})

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

  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(event) {
  if (showMore.value && !event.target.closest('.more-wrapper')) {
    showMore.value = false
  }
}

function showConfirm(title, message, onConfirm) {
  confirmModal.value = { show: true, title, message, onConfirm }
}

function handleCopyLink() {
  const url = window.location.origin + router.resolve({ name: 'activity-detail', params: { slug: route.params.slug } }).href
  navigator.clipboard.writeText(url).then(() => {
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  })
}

async function handleJoin() {
  if (activity.value.has_groups) {
    frozenMsg.value = '该活动已分组，无法操作'
    setTimeout(() => (frozenMsg.value = ''), 2000)
    return
  }
  joining.value = true
  joinError.value = ''
  joinSuccess.value = ''
  try {
    await joinActivity(route.params.slug)
    activity.value.is_member = true
    activity.value.members.push({
      user_id: auth.user.id,
      nickname: auth.user.nickname,
      avatar_path: auth.user.avatar_path,
      joined_at: new Date().toISOString(),
    })
    joinSuccess.value = '加入成功'
    setTimeout(() => (joinSuccess.value = ''), 2000)
  } catch (err) {
    joinError.value = err.response?.data?.detail || '加入失败'
  } finally {
    joining.value = false
  }
}

async function handleLeave() {
  if (activity.value.has_groups) {
    frozenMsg.value = '该活动已分组，无法操作'
    setTimeout(() => (frozenMsg.value = ''), 2000)
    return
  }
  showConfirm('退出活动', '确定要退出此活动吗？', async () => {
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
  })
}

async function handleDelete() {
  showConfirm('删除活动', '确定要删除此活动吗？删除后不可恢复。', async () => {
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
  })
}

async function handleKick(userId, nickname) {
  showConfirm('踢出成员', `确定要将 ${nickname} 踢出此活动吗？`, async () => {
    kickingUserId.value = userId
    kickError.value = ''
    try {
      await kickMember(route.params.slug, userId)
      activity.value.members = activity.value.members.filter(m => m.user_id !== userId)
    } catch (err) {
      kickError.value = err.response?.data?.detail || '踢出失败'
    } finally {
      kickingUserId.value = null
    }
  })
}

async function handleGroup() {
  grouping.value = true
  groupError.value = ''
  groupSuccess.value = ''
  try {
    const res = await createGroups(route.params.slug)
    activity.value.groups = res.data.groups
    activity.value.ungrouped_members = res.data.ungrouped_members
    activity.value.has_groups = true
    groupSuccess.value = '分组完成'
    setTimeout(() => (groupSuccess.value = ''), 2000)
  } catch (err) {
    groupError.value = err.response?.data?.detail || '分组失败'
  } finally {
    grouping.value = false
  }
}

async function handleUngroup() {
  showConfirm('解除分组', '确定要解除分组吗？', async () => {
    grouping.value = true
    groupError.value = ''
    try {
      await deleteGroups(route.params.slug)
      activity.value.groups = []
      activity.value.ungrouped_members = []
      activity.value.has_groups = false
      groupSuccess.value = '已解除分组'
      setTimeout(() => (groupSuccess.value = ''), 2000)
    } catch (err) {
      groupError.value = err.response?.data?.detail || '解除分组失败'
    } finally {
      grouping.value = false
    }
  })
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
        <span class="time">{{ formatDate(activity.created_at) }}</span>
      </div>
      <div class="desc-section">
        <p v-if="activity.description" class="description">{{ activity.description }}</p>
        <p v-else class="description" style="color: #bbb;">暂无描述</p>
      </div>
      <div class="rule-section">
        <span class="rule-badge" v-if="activity.group_strategy === 'fixed_group_count'">
          分组规则：共分 {{ activity.group_param }} 组
        </span>
        <span class="rule-badge" v-else>
          分组规则：每组 {{ activity.group_param }} 人
        </span>
        <template v-if="activity.constraints?.length">
          <span class="rule-badge" v-for="(c, idx) in activity.constraints" :key="idx">
            组内限定：每组{{ c.constraint_type === 'min_diversity' ? '至少' : '最多' }}{{ c.constraint_value }}种{{ c.attribute_name }}
          </span>
        </template>
      </div>
      <div class="members-section">
        <h3 class="members-title">
          已加入的成员 {{ activity.members?.length || 0 }} 人<template v-if="activity.has_groups && activity.groups?.length">，共 {{ activity.groups.length }} 组</template>
          <button
            v-if="activity.is_creator && !activity.has_groups"
            class="btn-toggle-kick"
            :class="{ active: showKick }"
            @click="showKick = !showKick"
          >
            {{ showKick ? '完成管理' : '管理成员' }}
          </button>
        </h3>
        <div v-if="activity.has_groups && activity.groups?.length">
          <div v-for="group in activity.groups" :key="group.group_number" class="group-card">
            <h4 class="group-title">第 {{ group.group_number }} 组 {{ group.members.length }} 人</h4>
            <div class="members-list">
              <div v-for="member in group.members" :key="member.user_id" class="member-item">
                <div class="member-avatar">
                  <img v-if="member.avatar_path" :src="`${uploadsUrl}/${member.avatar_path}`" />
                  <span v-else class="avatar-placeholder">{{ member.nickname[0] }}</span>
                </div>
                <span class="member-nickname">{{ member.nickname }}</span>
              </div>
            </div>
          </div>
          <div v-if="activity.ungrouped_members?.length" class="group-card ungrouped-card">
            <h4 class="group-title">尚未分组 {{ activity.ungrouped_members.length }} 人</h4>
            <div class="members-list">
              <div v-for="member in activity.ungrouped_members" :key="member.user_id" class="member-item">
                <div class="member-avatar">
                  <img v-if="member.avatar_path" :src="`${uploadsUrl}/${member.avatar_path}`" />
                  <span v-else class="avatar-placeholder">{{ member.nickname[0] }}</span>
                </div>
                <span class="member-nickname">{{ member.nickname }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="activity.members?.length" class="members-list">
          <div v-for="member in activity.members" :key="member.user_id" class="member-item">
            <div class="member-avatar">
              <img v-if="member.avatar_path" :src="`${uploadsUrl}/${member.avatar_path}`" />
              <span v-else class="avatar-placeholder">{{ member.nickname[0] }}</span>
            </div>
            <span class="member-nickname">{{ member.nickname }}</span>
            <button
              v-if="activity.is_creator && member.user_id !== auth.user.id && showKick"
              class="btn-kick"
              :disabled="kickingUserId === member.user_id"
              @click="handleKick(member.user_id, member.nickname)"
            >
              {{ kickingUserId === member.user_id ? '踢出中...' : '踢出' }}
            </button>
          </div>
        </div>
        <p v-else class="members-empty">暂无成员</p>
      </div>
      <div v-if="updated" class="success-msg" style="margin-bottom: 12px;">活动信息已更新</div>
      <div v-if="joinError" class="error-msg" style="margin-bottom: 12px;">{{ joinError }}</div>
      <div v-if="joinSuccess" class="success-msg" style="margin-bottom: 12px;">{{ joinSuccess }}</div>
      <div v-if="leaveError" class="error-msg" style="margin-bottom: 12px;">{{ leaveError }}</div>
      <div v-if="deleteError" class="error-msg" style="margin-bottom: 12px;">{{ deleteError }}</div>
      <div v-if="kickError" class="error-msg" style="margin-bottom: 12px;">{{ kickError }}</div>
      <div v-if="groupError" class="error-msg" style="margin-bottom: 12px;">{{ groupError }}</div>
      <div v-if="groupSuccess" class="success-msg" style="margin-bottom: 12px;">{{ groupSuccess }}</div>
      <div v-if="frozenMsg" class="warning-msg" style="margin-bottom: 12px;">{{ frozenMsg }}</div>
      <div class="actions">
        <button v-if="!activity.is_member" class="btn btn-primary" :class="{ 'btn-disabled': activity.has_groups }" :disabled="joining" @click="handleJoin">
          {{ joining ? '加入中...' : '加入活动' }}
        </button>
        <button v-if="activity.is_creator && !activity.has_groups" class="btn btn-primary" :disabled="grouping" @click="handleGroup">
          {{ grouping ? '分组中...' : '开始分组' }}
        </button>
        <button class="btn btn-secondary" @click="handleCopyLink" style="white-space: nowrap;">
          {{ copied ? '已复制！' : '分享链接' }}
        </button>
        <div v-if="hasMoreItems" class="more-wrapper">
          <button class="btn btn-secondary" @click="showMore = !showMore">
            更多 ▾
          </button>
          <div v-if="showMore" class="more-menu">
            <button
              v-if="activity.is_member"
              class="btn btn-secondary btn-warning"
              :class="{ 'btn-disabled': activity.has_groups }"
              :disabled="leaving"
              @click="handleLeave(); showMore = false"
            >
              {{ leaving ? '退出中...' : '退出活动' }}
            </button>
            <button
              v-if="activity.is_creator && activity.has_groups"
              class="btn btn-secondary btn-warning"
              :disabled="grouping"
              @click="handleUngroup(); showMore = false"
            >
              {{ grouping ? '解除中...' : '解除分组' }}
            </button>
            <button
              v-if="activity.is_creator"
              class="btn btn-secondary"
              @click="router.push({ name: 'activity-edit', params: { slug: route.params.slug } }); showMore = false"
            >
              编辑活动
            </button>
            <button
              v-if="activity.is_creator"
              class="btn btn-danger"
              :disabled="deleting"
              @click="handleDelete(); showMore = false"
            >
              {{ deleting ? '删除中...' : '删除活动' }}
            </button>
          </div>
        </div>
      </div>
    </template>
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

.rule-section {
  margin-bottom: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rule-badge {
  display: inline-block;
  padding: 6px 14px;
  background: #f0eefc;
  color: #4f46e5;
  border-radius: 6px;
  font-size: 13px;
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
  position: relative;
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-toggle-kick {
  font-size: 11px;
  padding: 2px 10px;
  border: 1px solid #bbb;
  border-radius: 4px;
  background: #f3f4f6;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-toggle-kick:hover {
  border-color: #aaa;
  color: #555;
}

.btn-toggle-kick.active {
  border-color: #4f46e5;
  color: #4f46e5;
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

.btn-kick {
  font-size: 11px;
  padding: 2px 10px;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  background: transparent;
  color: #e74c3c;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: auto;
}

.btn-kick:hover:not(:disabled) {
  background: #e74c3c;
  color: #fff;
}

.btn-kick:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.group-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
}

.group-title {
  font-size: 13px;
  color: #555;
  margin-bottom: 8px;
  font-weight: 600;
}

.ungrouped-card {
  background: #fef9e7;
  border: 1px dashed #e6a23c;
}

.btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.more-wrapper {
  position: relative;
  display: inline-block;
}

.more-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 120px;
  z-index: 10;
}

.more-menu .btn {
  width: 100%;
  text-align: left;
  padding: 6px 14px;
  border: none;
  background: transparent;
  font-size: 13px;
  border-radius: 4px;
  color: #555;
}

.more-menu .btn:hover:not(:disabled) {
  background: #f0f0f0;
}

.more-menu .btn-danger {
  color: #e74c3c;
}

.more-menu .btn-danger:hover:not(:disabled) {
  background: #fde;
  color: #e74c3c;
}

.more-menu .btn-warning {
  color: #e6a23c;
}

.more-menu .btn-warning:hover:not(:disabled) {
  background: #fef5e7;
  color: #e6a23c;
}

.warning-msg {
  color: #e6a23c;
  font-size: 13px;
}
</style>
