<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { createActivity, listActivities } from '../api/activities'

const auth = useAuthStore()

const title = ref('')
const description = ref('')
const error = ref('')
const success = ref('')
const creating = ref(false)
const activities = ref([])
const loading = ref(true)

async function fetchActivities() {
  try {
    const res = await listActivities()
    activities.value = res.data
  } catch (err) {
    console.error('加载活动列表错误:', err)
  } finally {
    loading.value = false
  }
}

onMounted(fetchActivities)

async function handleCreate() {
  error.value = ''
  success.value = ''
  creating.value = true
  try {
    const res = await createActivity({
      title: title.value,
      description: description.value || null,
    })
    activities.value.unshift(res.data)
    title.value = ''
    description.value = ''
    success.value = '活动创建成功'
    setTimeout(() => (success.value = ''), 3000)
  } catch (err) {
    console.error('创建活动错误:', err)
    error.value = err.response?.data?.detail || '创建失败'
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div class="page-card">
    <h1 class="page-title">我的活动</h1>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>

    <!-- 创建活动表单 -->
    <form @submit.prevent="handleCreate" class="create-form">
      <div class="form-group">
        <label>活动标题 *</label>
        <input v-model="title" type="text" required placeholder="输入活动标题" />
      </div>
      <div class="form-group">
        <label>活动描述 <span class="optional">(可选)</span></label>
        <textarea v-model="description" rows="3" placeholder="输入活动描述" class="textarea"></textarea>
      </div>
      <button type="submit" class="btn btn-primary" :disabled="creating">
        {{ creating ? '创建中...' : '创建活动' }}
      </button>
    </form>

    <!-- 活动列表 -->
    <div class="activity-list">
      <div v-if="loading" style="text-align: center; color: #999; padding: 20px;">加载中...</div>
      <div v-else-if="activities.length === 0" style="text-align: center; color: #999; padding: 20px;">
        还没有活动，创建一个吧
      </div>
      <div v-for="a in activities" :key="a.id" class="activity-item">
        <div class="activity-title">{{ a.title }}</div>
        <div v-if="a.description" class="activity-desc">
          {{ a.description.length > 50 ? a.description.slice(0, 50) + '...' : a.description }}
        </div>
        <div class="activity-time">{{ a.created_at.slice(0, 10) }}</div>
      </div>
    </div>
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
