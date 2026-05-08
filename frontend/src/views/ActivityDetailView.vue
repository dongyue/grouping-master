<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getActivity, joinActivity, leaveActivity, deleteActivity, kickMember, createGroups, deleteGroups, updateMemberInfo, moveMember, createGroup, deleteGroup, getActivityLogs } from '../api/activities'
import { getUserAttributes } from '../api/auth'
import ConfirmModal from '../components/ConfirmModal.vue'
import AttributeSelector from '../components/AttributeSelector.vue'
import MemberItem from '../components/MemberItem.vue'
import { formatDate } from '../utils/date'

const uploadsUrl = import.meta.env.VITE_UPLOADS_URL ?? 'http://localhost:8000'

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
const showManualAdjust = ref(false)
const changeLogs = ref([])

const actionLabels = { join: '新加入', leave: '已退出', kick: '已被踢' }
const confirmModal = ref({ show: false, title: '', message: '', onConfirm: null })
const showAttributeSelector = ref(false)
const attributeSubmitting = ref(false)
const editAttrValues = ref({})
const editNickname = ref('')
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
    return `成员 ${count} 人，分为 ${groupCount} 组`
  }
  return `成员 ${count} 人，分为 ${groupCount} 组，另有 ${ungroupedCount} 人落单`
})

const sectionTitle = computed(() => {
  return activity.value?.has_groups ? '成员与分组情况' : '成员情况'
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
    if (res.data.is_creator && res.data.has_groups) fetchChangeLogs()
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

function showConfirm(title, message, onConfirm, onCancel, confirmText, cancelText) {
  confirmModal.value = { show: true, title, message, onConfirm, onCancel, confirmText, cancelText }
}

function handleCopyLink() {
  const url = window.location.origin + router.resolve({ name: 'activity-detail', params: { slug: route.params.slug } }).href
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(() => {
      copied.value = true
      setTimeout(() => (copied.value = false), 2000)
    }).catch(() => {})
  } else {
    const ta = document.createElement('textarea')
    ta.value = url
    ta.style.position = 'fixed'
    ta.style.left = '-9999px'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  }
}

function handleDragStart(event, userId) {
  event.dataTransfer.setData('application/json', JSON.stringify({ user_id: userId }))
  event.dataTransfer.effectAllowed = 'move'
}

async function handleDrop(event, targetGroupNumber) {
  event.preventDefault()
  const data = JSON.parse(event.dataTransfer.getData('application/json'))
  if (!data.user_id) return
  try {
    await moveMember(route.params.slug, { user_id: data.user_id, target_group_number: targetGroupNumber })
    await refetchActivity()
  } catch {}
}

async function handleCreateGroup() {
  const ungroupedCount = activity.value?.ungrouped_members?.length || 0
  if (ungroupedCount === 0) {
    try {
      await createGroup(route.params.slug, { move_ungrouped: false })
      await refetchActivity()
    } catch (e) { console.error(e) }
    return
  }

  showConfirm('新增组', `当前有 ${ungroupedCount} 人落单，是否将他们移入新组？`,
    async () => {
      try {
        await createGroup(route.params.slug, { move_ungrouped: true })
        await refetchActivity()
      } catch (e) { console.error(e) }
    },
    async () => {
      try {
        await createGroup(route.params.slug, { move_ungrouped: false })
        await refetchActivity()
      } catch (e) { console.error(e) }
    },
    '是', '否'
  )
}

async function handleDeleteGroup(groupNumber) {
  try {
    await deleteGroup(route.params.slug, { group_number: groupNumber })
    await refetchActivity()
  } catch {}
}

async function refetchActivity() {
  try {
    const res = await getActivity(route.params.slug)
    activity.value = res.data
    sortKey.value = res.data.has_groups ? 'group' : 'joined'
    if (!res.data.has_groups) showManualAdjust.value = false
    changeLogs.value = []
    if (res.data.is_creator && res.data.has_groups) fetchChangeLogs()
  } catch {} // silently ignore refetch failures
}

async function fetchChangeLogs() {
  try {
    const res = await getActivityLogs(route.params.slug, { after_group: true })
    changeLogs.value = res.data
  } catch {}
}

async function handleJoin() {
  isEditingAttrs.value = false
  editNickname.value = auth.user?.nickname || ''
  showAttributeSelector.value = true
}

async function handleAttributeConfirm({ nickname, attributeValues, preferences }) {
  showAttributeSelector.value = false
  attributeSubmitting.value = true
  joinError.value = ''
  joinSuccess.value = ''
  try {
    await joinActivity(route.params.slug, {
      nickname,
      attribute_values: Object.keys(attributeValues).length ? attributeValues : null,
      preferences: preferences || null,
    })
    await refetchActivity()
    joinSuccess.value = '加入成功'
    if (auth.user && nickname) {
      auth.user = { ...auth.user, nickname }
    }
    setTimeout(() => (joinSuccess.value = ''), 2000)
  } catch (err) {
    joinError.value = err.response?.data?.detail || '加入失败'
  } finally {
    attributeSubmitting.value = false
  }
}

function openAttrEditor() {
  const me = activity.value.members?.find(m => m.user_id === auth.user?.id)
  editAttrValues.value = me?.attributes || {}
  editNickname.value = me?.nickname || auth.user?.nickname || ''
  editAttrLabel.value = '保存'
  isEditingAttrs.value = true
  showAttributeSelector.value = true
}
async function handleAttrEditConfirm({ nickname, attributeValues, preferences }) {
  showAttributeSelector.value = false
  attributeSubmitting.value = true
  joinError.value = ''
  joinSuccess.value = ''
  try {
    await updateMemberInfo(route.params.slug, {
      nickname,
      attribute_values: Object.keys(attributeValues).length ? attributeValues : null,
      preferences: preferences || null,
    })
    await refetchActivity()
    joinSuccess.value = '个人信息已更新'
    if (auth.user && nickname) {
      auth.user = { ...auth.user, nickname }
    }
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
      <h3 class="rule-heading">
        分组规则
        <span v-if="activity.is_creator" class="edit-icon" @click="router.push({ name: 'activity-edit', params: { slug: route.params.slug } })" title="编辑活动">&nbsp;&#x270E;</span>
      </h3>
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
        <span v-if="activity.allow_want_preferences" class="rule-badge">
          成员偏好：允许成员设置「想和谁同组」，最多 {{ activity.max_want_count }} 人
        </span>
        <span v-if="activity.allow_avoid_preferences" class="rule-badge">
          成员偏好：允许成员设置「不想和谁同组」，最多 {{ activity.max_avoid_count }} 人
        </span>
        <AttributeSelector
          v-if="showAttributeSelector"
          :constraints="activity.constraints || []"
          :submitting="attributeSubmitting"
          :initial-nickname="editNickname"
          :initial-values="editAttrValues"
          :user-attributes="userAttributes"
          :confirm-label="editAttrLabel"
          :activity-members="activity.members || []"
          :allow-want-preferences="activity.allow_want_preferences"
          :max-want-count="activity.max_want_count"
          :allow-avoid-preferences="activity.allow_avoid_preferences"
          :max-avoid-count="activity.max_avoid_count"
          :initial-preferences="activity.my_preferences || { want: [], avoid: [] }"
          :current-user-id="auth.user?.id"
          :uploads-url="uploadsUrl"
          @confirm="isEditingAttrs ? handleAttrEditConfirm($event) : handleAttributeConfirm($event)"
          @cancel="handleAttrCancel"
        />
      </div>
      <h3 class="rule-heading section-heading">
        <span class="section-heading-text">{{ sectionTitle }}</span>
        <select
          v-if="!showManualAdjust && activity.members?.length && sortOptions.length > 2"
          v-model="sortKey"
          class="sort-select"
        >
          <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <button
          v-if="activity.is_creator && activity.has_groups"
          class="btn-toggle-kick"
          :class="{ active: showManualAdjust }"
          @click="showManualAdjust = !showManualAdjust"
        >
          {{ showManualAdjust ? '完成调整' : '手动调整分组' }}
        </button>
        <button
          v-if="activity.is_creator"
          class="btn-toggle-kick"
          :class="{ active: showKick }"
          @click="showKick = !showKick"
        >
          {{ showKick ? '踢毕' : '踢人' }}
        </button>
      </h3>
      <div class="members-section">
        <div class="members-toolbar">
          <span class="members-summary">{{ memberTitle }}</span>
        </div>
        <div v-if="activity.has_groups && (showManualAdjust || sortKey === 'group') && activity.groups?.length">
          <div
            v-for="group in activity.groups"
            :key="group.group_number"
            class="group-card"
            :class="{
              'my-group': group.members.some(m => m.user_id === auth.user?.id),
              'group-card-adjust': showManualAdjust
            }"
            @dragover.prevent
            @drop="showManualAdjust && handleDrop($event, group.group_number)"
          >
            <h4 class="group-title">第 {{ group.group_number }} 组 {{ group.members.length }} 人</h4>
            <button v-if="showManualAdjust" class="group-remove" @click="handleDeleteGroup(group.group_number)" title="删除此组">&times;</button>
            <div class="members-list">
              <div
                v-for="member in group.members"
                :key="member.user_id"
                :draggable="showManualAdjust ? 'true' : 'false'"
                :class="{ 'drag-member': showManualAdjust }"
                @dragstart="showManualAdjust && handleDragStart($event, member.user_id)"
              >
                <MemberItem
                  :member="member"
                  :current-user-id="auth.user?.id"
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
          <div
            v-if="showManualAdjust || activity.ungrouped_members?.length"
            class="group-card ungrouped-card"
            :class="{
              'my-group': activity.ungrouped_members?.some(m => m.user_id === auth.user?.id)
            }"
            @dragover.prevent
            @drop="showManualAdjust && handleDrop($event, null)"
          >
            <h4 class="group-title">落单 {{ activity.ungrouped_members?.length || 0 }} 人</h4>
            <div class="members-list">
              <div
                v-for="member in activity.ungrouped_members || []"
                :key="member.user_id"
                :draggable="showManualAdjust ? 'true' : 'false'"
                :class="{ 'drag-member': showManualAdjust }"
                @dragstart="showManualAdjust && handleDragStart($event, member.user_id)"
              >
                <MemberItem
                  :member="member"
                  :current-user-id="auth.user?.id"
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
          <div v-if="showManualAdjust" class="add-group-area">
            <button class="btn-add-group" @click="handleCreateGroup">+ 新增组</button>
          </div>
        </div>
        <div v-else-if="sortedMembers.flat?.length" class="members-list">
          <MemberItem
            v-for="member in sortedMembers.flat"
            :key="member.user_id"
            :member="member"
            :current-user-id="auth.user?.id"
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
          <div v-for="(members, groupLabel) in sortedMembers.grouped" :key="groupLabel" class="group-card" :class="{ 'my-group': members.some(m => m.user_id === auth.user?.id) }">
            <h4 class="group-title">{{ groupLabel }} {{ members.length }} 人</h4>
            <div class="members-list">
              <MemberItem
                v-for="member in members"
                :key="member.user_id"
                :member="member"
                :current-user-id="auth.user?.id"
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
        <div v-if="changeLogs.length" class="change-logs">
          <h4 class="change-logs-title">自动分组后成员变动</h4>
          <div v-for="log in changeLogs" :key="log.id" class="change-log-item" :class="'cl-' + log.action_type">
            <span class="cl-tag">{{ actionLabels[log.action_type] || log.action_type }}</span>
            {{ log.content }}
          </div>
        </div>
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
          {{ grouping ? '分组中...' : '自动分组' }}
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
      @cancel="confirmModal.show = false; confirmModal.onCancel?.()"
      :confirm-text="confirmModal.confirmText"
      :cancel-text="confirmModal.cancelText"
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

.edit-icon {
  cursor: pointer;
  color: #bbb;
  font-size: 14px;
  transition: color 0.15s;
  flex-shrink: 0;
}

.edit-icon:hover {
  color: #666;
}

.change-logs {
  margin-top: 20px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
}

.change-logs-title {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.change-log-item {
  font-size: 13px;
  padding: 4px 0;
  color: #555;
}

.cl-tag {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  margin-right: 6px;
}

.cl-join .cl-tag { background: #f6ffed; color: #52c41a; }
.cl-leave .cl-tag { background: #fff7e6; color: #fa8c16; }
.cl-kick .cl-tag { background: #fff1f0; color: #f5222d; }

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

.section-heading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-heading-text {
  flex: 1;
}

.members-toolbar {
  margin-bottom: 12px;
}

.members-summary {
  font-size: 13px;
  color: #666;
}

.sort-select {
  font-size: 11px;
  padding: 2px 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  color: #666;
  cursor: pointer;
  flex-shrink: 0;
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

.group-card-adjust {
  position: relative;
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

.drag-member {
  cursor: grab;
}

.drag-member:active {
  cursor: grabbing;
  opacity: 0.7;
}

.add-group-area {
  margin-bottom: 12px;
}

.btn-add-group {
  background: transparent;
  border: 1px dashed #bbb;
  border-radius: 8px;
  color: #888;
  font-size: 13px;
  padding: 8px 24px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.btn-add-group:hover {
  border-color: #666;
  color: #555;
}

.group-remove {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 28px;
  height: 28px;
  border: none;
  background: #fff;
  color: #999;
  font-size: 18px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.group-remove:hover {
  color: #dc2626;
  background: #fef2f2;
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
