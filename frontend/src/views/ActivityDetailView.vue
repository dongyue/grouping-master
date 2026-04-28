<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getActivity } from '../api/activities'

const route = useRoute()
const router = useRouter()

const activity = ref(null)
const loading = ref(true)
const error = ref('')
const copied = ref(false)

onMounted(async () => {
  try {
    const res = await getActivity(route.params.id)
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
})

function handleCopyLink() {
  const url = window.location.origin + router.resolve({ name: 'activity-detail', params: { id: route.params.id } }).href
  navigator.clipboard.writeText(url).then(() => {
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
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
        <span class="time">{{ activity.created_at.slice(0, 10) }}</span>
      </div>
      <div class="desc-section">
        <p v-if="activity.description" class="description">{{ activity.description }}</p>
        <p v-else class="description" style="color: #bbb;">暂无描述</p>
      </div>
      <div class="actions">
        <button class="btn btn-secondary" @click="handleCopyLink" style="white-space: nowrap;">
          {{ copied ? '已复制！' : '分享链接' }}
        </button>
        <router-link to="/" class="btn btn-secondary" style="text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap;">
          返回首页
        </router-link>
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
  gap: 12px;
}
</style>
