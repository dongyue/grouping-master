<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { createActivity, listActivities } from '../api/activities'

const router = useRouter()
const route = useRoute()

const auth = useAuthStore()

const title = ref('')
const description = ref('')
const joinActivity = ref(true)
const error = ref('')
const success = ref('')
const creating = ref(false)
const createdActivities = ref([])
const joinedActivities = ref([])
const loading = ref(true)

async function fetchActivities() {
  try {
    const [createdRes, joinedRes] = await Promise.all([
      listActivities('created'),
      listActivities('joined'),
    ])
    createdActivities.value = createdRes.data
    joinedActivities.value = joinedRes.data
  } catch (err) {
    console.error('加载活动列表错误:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchActivities()
  if (route.query.deleted === '1') {
    success.value = '活动已删除'
    router.replace({ query: {} })
    setTimeout(() => (success.value = ''), 3000)
  }
  if (route.query.left === '1') {
    success.value = '已退出活动'
    router.replace({ query: {} })
    setTimeout(() => (success.value = ''), 3000)
  }
})

async function handleCreate() {
  error.value = ''
  success.value = ''
  creating.value = true
  try {
    const res = await createActivity({
      title: title.value,
      description: description.value || null,
      join_activity: joinActivity.value,
    })
    createdActivities.value.unshift(res.data)
    if (joinActivity.value) {
      joinedActivities.value.unshift(res.data)
    }
    title.value = ''
    description.value = ''
    joinActivity.value = true
    success.value = '活动创建成功'
    setTimeout(() => (success.value = ''), 3000)
  } catch (err) {
    console.error('创建活动错误:', err)
    error.value = err.response?.data?.detail || '创建失败'
  } finally {
    creating.value = false
  }
}

function truncate(text) {
  return text.length > 50 ? text.slice(0, 50) + '...' : text
}
</script>

<template>
  <div class="page-card">
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>

    <!-- 创建活动表单 -->
    <form @submit.prevent="handleCreate" class="create-form">
      <h2 class="section-title">创建活动</h2>
      <div class="form-group">
        <label>活动标题 *</label>
        <input v-model="title" type="text" required placeholder="输入活动标题" />
      </div>
      <div class="form-group">
        <label>活动描述 <span class="optional">(可选)</span></label>
        <textarea v-model="description" rows="3" placeholder="输入活动描述" class="textarea"></textarea>
      </div>
      <div class="form-group checkbox-group">
        <label class="checkbox-label">
          <input v-model="joinActivity" type="checkbox" />
          <span>同时加入活动</span>
        </label>
      </div>
      <button type="submit" class="btn btn-primary" :disabled="creating">
        {{ creating ? '创建中...' : '创建活动' }}
      </button>
    </form>

    <div v-if="loading" style="text-align: center; color: #999; padding: 20px;">加载中...</div>

    <template v-else>
      <!-- 我创建的活动 -->
      <div class="activity-section">
        <h2 class="section-title">我创建的活动</h2>
        <div v-if="createdActivities.length === 0" class="empty-hint">暂无</div>
        <div v-for="a in createdActivities" :key="'created-' + a.id" class="activity-item" @click="router.push(`/activities/${a.id}`)" style="cursor: pointer;">
          <div class="activity-title">{{ a.title }}</div>
          <div v-if="a.description" class="activity-desc">{{ truncate(a.description) }}</div>
          <div class="activity-time">{{ a.created_at.slice(0, 10) }}</div>
        </div>
      </div>

      <!-- 我加入的活动 -->
      <div class="activity-section">
        <h2 class="section-title">我加入的活动</h2>
        <div v-if="joinedActivities.length === 0" class="empty-hint">暂无</div>
        <div v-for="a in joinedActivities" :key="'joined-' + a.id" class="activity-item" @click="router.push(`/activities/${a.id}`)" style="cursor: pointer;">
          <div class="activity-title">{{ a.title }}</div>
          <div v-if="a.description" class="activity-desc">{{ truncate(a.description) }}</div>
          <div class="activity-time">{{ a.created_at.slice(0, 10) }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.create-form {
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 20px;
}

.textarea {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  resize: vertical;
  font-family: inherit;
  transition: border-color 0.2s;
}

.textarea:focus {
  border-color: #4f46e5;
}

.checkbox-group {
  margin-bottom: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #555;
}

.checkbox-label input[type="checkbox"] {
  width: 15px;
  height: 15px;
  margin: 0;
  accent-color: #4f46e5;
  cursor: pointer;
}

.activity-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #4f46e5;
}

.empty-hint {
  text-align: center;
  color: #bbb;
  padding: 16px 0;
  font-size: 14px;
}

.activity-item {
  padding: 14px 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.activity-desc {
  font-size: 13px;
  color: #888;
  margin-bottom: 4px;
  line-height: 1.5;
}

.activity-time {
  font-size: 12px;
  color: #bbb;
}
</style>
