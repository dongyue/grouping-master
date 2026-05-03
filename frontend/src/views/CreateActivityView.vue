<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createActivity } from '../api/activities'
import ActivityForm from '../components/ActivityForm.vue'

const router = useRouter()

const joinActivity = ref(true)
const error = ref('')
const creating = ref(false)

async function handleCreate(payload) {
  error.value = ''
  creating.value = true
  try {
    const res = await createActivity(payload)
    const query = joinActivity.value ? { autojoin: '1' } : {}
    router.push({ name: 'activity-detail', params: { slug: res.data.slug }, query })
  } catch (err) {
    error.value = err.response?.data?.detail || '创建失败'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } finally {
    creating.value = false
  }
}

function handleCancel() {
  router.push({ name: 'home' })
}
</script>

<template>
  <ActivityForm
    page-title="创建活动"
    :submitting="creating"
    :submit-error="error"
    @submit="handleCreate"
  >
    <template #extra-fields>
      <div class="form-group checkbox-group">
        <label class="checkbox-label">
          <input v-model="joinActivity" type="checkbox" />
          <span>我作为创建者也要参加</span>
        </label>
      </div>
    </template>
    <template #extra-actions>
      <p class="rule-hint">创建后可在编辑页中修改上述设置</p>
    </template>
    <template #actions="{ submitting }">
      <button type="submit" class="btn btn-primary" :disabled="submitting">
        {{ submitting ? '创建中...' : '创建活动' }}
      </button>
      <button type="button" class="btn btn-secondary" :disabled="submitting" @click="handleCancel">
        取消
      </button>
    </template>
  </ActivityForm>
</template>

<style scoped>
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
  flex-shrink: 0;
}
</style>
