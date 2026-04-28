<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getActivity, updateActivity } from '../api/activities'

const route = useRoute()
const router = useRouter()

const title = ref('')
const description = ref('')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const saveError = ref('')

onMounted(async () => {
  try {
    const res = await getActivity(route.params.slug)
    const data = res.data
    if (!data.is_creator) {
      router.replace({ name: 'activity-detail', params: { slug: route.params.slug } })
      return
    }
    title.value = data.title
    description.value = data.description || ''
  } catch (err) {
    error.value = err.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  saving.value = true
  saveError.value = ''
  try {
    await updateActivity(route.params.slug, {
      title: title.value,
      description: description.value || null,
    })
    router.push({ name: 'activity-detail', params: { slug: route.params.slug }, query: { updated: '1' } })
  } catch (err) {
    saveError.value = err.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.back()
}
</script>

<template>
  <div class="page-card">
    <div v-if="loading" style="text-align: center; color: #999; padding: 40px;">加载中...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else>
      <h1 class="page-title">编辑活动</h1>
      <div v-if="saveError" class="error-msg">{{ saveError }}</div>
      <form @submit.prevent="handleSave">
        <div class="form-group">
          <label>活动标题 *</label>
          <input v-model="title" type="text" required placeholder="输入活动标题" />
        </div>
        <div class="form-group">
          <label>活动描述 <span class="optional">(可选)</span></label>
          <textarea v-model="description" rows="4" placeholder="输入活动描述" class="textarea"></textarea>
        </div>
        <div class="actions">
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button type="button" class="btn btn-secondary" :disabled="saving" @click="handleCancel">
            取消
          </button>
        </div>
      </form>
    </template>
  </div>
</template>

<style scoped>
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

.actions {
  display: flex;
  gap: 12px;
}

.actions .btn {
  width: auto;
  flex: 1;
}
</style>
