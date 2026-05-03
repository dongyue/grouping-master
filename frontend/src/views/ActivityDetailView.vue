<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getActivity, joinActivity, leaveActivity, deleteActivity, kickMember, createGroups, deleteGroups, updateAttributes } from '../api/activities'
import { getUserAttributes } from '../api/auth'
import ConfirmModal from '../components/ConfirmModal.vue'
import AttributeSelector from '../components/AttributeSelector.vue'
import MemberItem from '../components/MemberItem.vue'
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
const showMore = ref(false)
const showKick = ref(false)
const confirmModal = ref({ show: false, title: '', message: '', onConfirm: null })
const showAttributeSelector = ref(false)
const attributeSubmitting = ref(false)
const editAttrValues = ref({})
const editAttrLabel = ref('确认')
const isEditingAttrs = ref(false)
const userAttributes = ref({})
const sortKey = ref('joined')

const groupMap = computed(() => {
  const map = {}
  if (!activity.value) return map
  if (activity.value.has_groups) {
    if (activity.value.groups) {
      for (const g of activity.value.groups) {
        for (const m of g.members) {
          map[m.user_id] = `第${g.group_number}组`
        }
      }
    }
    if (activity.value.ungrouped_members) {
      for (const m of activity.value.ungrouped_members) {
        map[m.user_id] = '落单'
      }
    }
  }
  return map
})

const memberTitle = computed(() => {
  const count = activity.value?.members?.length || 0
  if (!activity.value?.has_groups || !activity.value?.groups?.length) {
    return `成员 ${count} 人`
  }
  const groupCount = activity.value.groups.length
  const ungroupedCount = activity.value.ungrouped_members?.length || 0
  if (ungroupedCount === 0) {
    return `成员 ${count} 人，分为 ${groupCount} 组。`
  }
  return `成员 ${count} 人，分为 ${groupCount} 组，另有 ${ungroupedCount} 人落单。`
})

const sortOptions = computed(() => {
  const options = [
    { value: 'joined', label: '按加入时间' },
    { value: 'nickname', label: '按昵称' },
  ]
  if (activity.value?.constraints) {
    for (const c of activity.value.constraints) {
      options.push({ value: 'attr:' + c.attribute_name, label: '按' + c.attribute_name })
    }
  }
  if (activity.value?.has_groups) {
    options.push({ value: 'group', label: '按分组' })
  }
  return options
})

const sortedMembers = computed(() => {
  const members = activity.value?.members || []
  if (!members.length || !sortKey.value) return { flat: members }

  if (sortKey.value === 'joined') return { flat: [...members] }
  if (sortKey.value === 'nickname') {
    return { flat: [...members].sort((a, b) => a.nickname.localeCompare(b.nickname, 'zh-CN')) }
  }

  if (sortKey.value.startsWith('attr:')) {
    const attrName = sortKey.value.slice(5)
    const groups = {}
    for (const m of members) {
      const v = m.attributes?.[attrName] || '未填写'
      if (!groups[v]) groups[v] = []
      groups[v].push(m)
    }
    return { grouped: groups }
  }

  return { flat: members }
})

const hasMemberItems = computed(() => {
  return activity.value?.is_member
})

const hasCreatorItems = computed(() => {
  return activity.value?.is_creator
})

onMounted(async () => {
  try {
    const res = await getActivity(route.params.slug)
    activity.value = res.data
    if (res.data.has_groups) sortKey.value = 'group'
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

  try {
    const attrRes = await getUserAttributes()
    userAttributes.value = attrRes.data.attributes
  } catch {} // silently ignore

  if (route.query.updated === '1') {
    updated.value = true
    router.replace({ query: {} })
    setTimeout(() => (updated.value = false), 3000)
  }

  if (route.query.autojoin === '1') {
    router.replace({ query: {} })
    handleJoin()
  }

  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

function getGroupLabel(userId) {
  if (!activity.value?.has_groups || sortKey.value === 'group') return ''
  return groupMap.value[userId] || ''
}

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

async function refetchActivity() {
  try {
    const res = await getActivity(route.params.slug)
    activity.value = res.data
    sortKey.value = res.data.has_groups ? 'group' : 'joined'
  } catch {} // silently ignore refetch failures
}

async function handleJoin() {
  isEditingAttrs.value = false
  showAttributeSelector.value = true
}

async function handleAttributeConfirm({ nickname, attributeValues }) {
  showAttributeSelector.value = false
  attributeSubmitting.value = true
  joinError.value = ''
  joinSuccess.value = ''
  try {
    await joinActivity(route.params.slug, {
      nickname,
      attribute_values: Object.keys(attributeValues).length ? attributeValues : null,
    })
    await refetchActivity()
    joinSuccess.value = '加入成功'
    setTimeout(() => (joinSuccess.value = ''), 2000)
  } catch (err) {
    joinError.value = err.response?.data?.detail || '加入失败'
  } finally {
    attributeSubmitting.value = false
  }
}

function openAttrEditor() {
  const me = activity.value.members?.find(m => m.user_id === auth.user.id)
  editAttrValues.value = me?.attributes || {}
  editAttrLabel.value = '保存'
  isEditingAttrs.value = true
  showAttributeSelector.value = true
}

async function handleAttrEditConfirm({ nickname, attributeValues }) {
  showAttributeSelector.value = false
  attributeSubmitting.value = true
  joinError.value = ''
  joinSuccess.value = ''
  try {
    await updateAttributes(route.params.slug, {
      nickname,
      attribute_values: Object.keys(attributeValues).length ? attributeValues : null,
    })
    await refetchActivity()
    joinSuccess.value = '个人信息已更新'
    setTimeout(() => (joinSuccess.value = ''), 2000)
  } catch (err) {
    joinError.value = err.response?.data?.detail || '更新失败'
  } finally {
    attributeSubmitting.value = false
  }
}

function handleAttrCancel() {
  showAttributeSelector.value = false
  editAttrValues.value = {}
  editAttrLabel.value = '确认'
  isEditingAttrs.value = false
}

async function handleLeave() {
  showConfirm('退出活动', '确定要退出此活动吗？', async () => {
    leaving.value = true
    leaveError.value = ''
    try {
      await leaveActivity(route.params.slug)
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
      await refetchActivity()
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
    await createGroups(route.params.slug)
    await refetchActivity()
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
      await refetchActivity()
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
      <h3 class="rule-heading">分组规则</h3>
      <div class="rule-section">
        <span class="rule-badge" v-if="activity.group_strategy === 'fixed_group_count'">
          分组方式：共分 {{ activity.group_param }} 组
        </span>
        <span class="rule-badge" v-else>
          分组方式：每组 {{ activity.group_param }} 人
        </span>
        <template v-if="activity.constraints?.length">
          <span class="rule-badge" v-for="(c, idx) in activity.constraints" :key="idx">
            组内限定：每组{{ c.constraint_type === 'min_diversity' ? '至少' : '最多' }}{{ c.constraint_value }}种{{ c.attribute_name }}
          </span>
        </template>
        <AttributeSelector
          v-if="showAttributeSelector"
          :constraints="activity.constraints || []"
          :submitting="attributeSubmitting"
          :initial-nickname="auth.user?.nickname || ''"
          :initial-values="editAttrValues"
          :user-attributes="userAttributes"
          :confirm-label="editAttrLabel"
          @confirm="isEditingAttrs ? handleAttrEditConfirm($event) : handleAttributeConfirm($event)"
          @cancel="handleAttrCancel"
        />
      </div>
      <div class="members-section">
        <h3 class="members-title">
          {{ memberTitle }}
          <select
            v-if="activity.members?.length && sortOptions.length > 2"
            v-model="sortKey"
            class="sort-select"
          >
            <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <button
            v-if="activity.is_creator"
            class="btn-toggle-kick"
            :class="{ active: showKick }"
            @click="showKick = !showKick"
          >
            {{ showKick ? '完成管理' : '管理成员' }}
          </button>
        </h3>
        <div v-if="activity.has_groups && sortKey === 'group' && activity.groups?.length">
          <div v-for="group in activity.groups" :key="group.group_number" class="group-card" :class="{ 'my-group': group.members.some(m => m.user_id === auth.user.id) }">
            <h4 class="group-title">第 {{ group.group_number }} 组 {{ group.members.length }} 人</h4>
            <div class="members-list">
              <MemberItem
                v-for="member in group.members"
                :key="member.user_id"
                :member="member"
                :current-user-id="auth.user.id"
                :is-creator="activity.is_creator"
                :show-kick="showKick"
                :kicking-user-id="kickingUserId"
                :uploads-url="uploadsUrl"
                @edit="openAttrEditor()"
                @kick="handleKick"
              />
            </div>
          </div>
          <div v-if="activity.ungrouped_members?.length" class="group-card ungrouped-card" :class="{ 'my-group': activity.ungrouped_members.some(m => m.user_id === auth.user.id) }">
            <h4 class="group-title">落单 {{ activity.ungrouped_members.length }} 人</h4>
            <div class="members-list">
              <MemberItem
                v-for="member in activity.ungrouped_members"
                :key="member.user_id"
                :member="member"
                :current-user-id="auth.user.id"
                :is-creator="activity.is_creator"
                :show-kick="showKick"
                :kicking-user-id="kickingUserId"
                :uploads-url="uploadsUrl"
                @edit="openAttrEditor()"
                @kick="handleKick"
              />
            </div>
          </div>
        </div>
        <div v-else-if="sortedMembers.flat?.length" class="members-list">
          <MemberItem
            v-for="member in sortedMembers.flat"
            :key="member.user_id"
            :member="member"
            :current-user-id="auth.user.id"
            :is-creator="activity.is_creator"
            :show-kick="showKick"
            :kicking-user-id="kickingUserId"
            :group-label="getGroupLabel(member.user_id)"
            :uploads-url="uploadsUrl"
            @edit="openAttrEditor()"
            @kick="handleKick"
          />
        </div>
        <div v-else-if="sortedMembers.grouped">
          <div v-for="(members, groupLabel) in sortedMembers.grouped" :key="groupLabel" class="group-card" :class="{ 'my-group': members.some(m => m.user_id === auth.user.id) }">
            <h4 class="group-title">{{ groupLabel }} {{ members.length }} 人</h4>
            <div class="members-list">
              <MemberItem
                v-for="member in members"
                :key="member.user_id"
                :member="member"
                :current-user-id="auth.user.id"
                :is-creator="activity.is_creator"
                :show-kick="showKick"
                :kicking-user-id="kickingUserId"
                :group-label="getGroupLabel(member.user_id)"
                :uploads-url="uploadsUrl"
                @edit="openAttrEditor()"
                @kick="handleKick"
              />
            </div>
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
      <div class="actions">
        <button v-if="!activity.is_member" class="btn btn-primary" :disabled="joining" @click="handleJoin">
          {{ joining ? '加入中...' : '加入活动' }}
        </button>
        <button v-if="activity.is_creator && !activity.has_groups" class="btn btn-primary" :disabled="grouping" @click="handleGroup">
          {{ grouping ? '分组中...' : '开始分组' }}
        </button>
        <button class="btn btn-secondary" @click="handleCopyLink" style="white-space: nowrap;">
          {{ copied ? '已复制！' : '分享链接' }}
        </button>
        <div v-if="hasMemberItems || hasCreatorItems" class="more-wrapper">
          <button class="btn btn-secondary" @click="showMore = !showMore">
            更多 ▾
          </button>
          <div v-if="showMore" class="more-menu">
            <button
              v-if="activity.is_creator && activity.has_groups"
              class="btn btn-secondary"
              :disabled="grouping"
              @click="handleGroup(); showMore = false"
            >
              {{ grouping ? '分组中...' : '重新分组' }}
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
              class="btn btn-secondary"
              @click="router.push({ name: 'activity-logs', params: { slug: route.params.slug } }); showMore = false"
            >
              查看日志
            </button>
            <button
              v-if="activity.is_creator"
              class="btn btn-danger"
              :disabled="deleting"
              @click="handleDelete(); showMore = false"
            >
              {{ deleting ? '删除中...' : '删除活动' }}
            </button>
            <div v-if="hasCreatorItems && hasMemberItems" class="more-divider"></div>
            <button
              v-if="activity.is_member"
              class="btn btn-secondary"
              @click="openAttrEditor(); showMore = false"
            >
              编辑我的信息
            </button>
            <button
              v-if="activity.is_member"
              class="btn btn-secondary btn-warning"
              :disabled="leaving"
              @click="handleLeave(); showMore = false"
            >
              {{ leaving ? '退出中...' : '退出活动' }}
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

.rule-heading {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0 0 10px 0;
}

.rule-section {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 6px;
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
  white-space: nowrap;
  flex-shrink: 0;
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

.members-empty {
  font-size: 13px;
  color: #bbb;
}

.group-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
}

.group-card.my-group {
  background: #f5f3ff;
  border: 2px solid #a78bfa;
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

.more-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 4px 0;
}
</style>
