<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { listActivities } from '../api/activities'
import { formatDate } from '../utils/date'

const router = useRouter()
const route = useRoute()

const success = ref('')
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

function truncate(text) {
  return text.length > 50 ? text.slice(0, 50) + '...' : text
}
</script>

<template>
  <div class="page-card">
    <div v-if="success" class="success-msg">{{ success }}</div>

    <div v-if="loading" style="text-align: center; color: #999; padding: 20px;">加载中...</div>

    <template v-else>
      <!-- 我创建的活动 -->
      <div class="activity-section">
        <div class="section-header">
          <h2 class="section-title">我创建的活动</h2>
          <button class="btn btn-primary btn-sm" @click="router.push({ name: 'activity-create' })">创建活动</button>
        </div>
        <div v-if="createdActivities.length === 0" class="empty-hint">暂无</div>
        <div v-for="a in createdActivities" :key="'created-' + a.id" class="activity-item" @click="router.push(`/activities/${a.slug}`)" style="cursor: pointer;">
          <div class="activity-title">{{ a.title }}</div>
          <div v-if="a.description" class="activity-desc">{{ truncate(a.description) }}</div>
          <div class="activity-time">{{ formatDate(a.created_at) }}</div>
        </div>
      </div>

      <!-- 我加入的活动 -->
      <div class="activity-section">
        <div class="section-header">
          <h2 class="section-title">我加入的活动</h2>
        </div>
        <div v-if="joinedActivities.length === 0" class="empty-hint">暂无</div>
        <div v-for="a in joinedActivities" :key="'joined-' + a.id" class="activity-item" @click="router.push(`/activities/${a.slug}`)" style="cursor: pointer;">
          <div class="activity-title">{{ a.title }}</div>
          <div v-if="a.description" class="activity-desc">{{ truncate(a.description) }}</div>
          <div class="activity-time">{{ formatDate(a.created_at) }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.activity-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2px solid #4f46e5;
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.btn-sm {
  padding: 4px 14px;
  font-size: 13px;
  width: auto;
  display: inline-block;
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
