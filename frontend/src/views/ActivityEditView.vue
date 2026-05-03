<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getActivity, updateActivity } from '../api/activities'
import { presetAttributes } from '../utils/constraintPresets'
import ActivityForm from '../components/ActivityForm.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const saveError = ref('')
const initialData = ref(null)

onMounted(async () => {
  try {
    const res = await getActivity(route.params.slug)
    const data = res.data
    if (!data.is_creator) {
      router.replace({ name: 'activity-detail', params: { slug: route.params.slug } })
      return
    }
    initialData.value = {
      title: data.title,
      description: data.description || '',
      group_param: data.group_param ?? 2,
      group_strategy: data.group_strategy ?? 'fixed_group_size',
      allow_want_preferences: data.allow_want_preferences ?? false,
      max_want_count: data.max_want_count ?? 1,
      allow_avoid_preferences: data.allow_avoid_preferences ?? false,
      max_avoid_count: data.max_avoid_count ?? 1,
      constraints: data.constraints && data.constraints.length > 0
        ? data.constraints.map(c => ({
            attribute_name: c.attribute_name || '',
            attr_custom: !presetAttributes.includes(c.attribute_name),
            allowed_values_raw: (c.allowed_values || []).join('，'),
            constraint_type: c.constraint_type || 'min_diversity',
            constraint_value: c.constraint_value || 1,
          }))
        : [],
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
})

async function handleSave(payload) {
  saving.value = true
  saveError.value = ''
  try {
    await updateActivity(route.params.slug, payload)
    router.push({ name: 'activity-detail', params: { slug: route.params.slug }, query: { updated: '1' } })
  } catch (err) {
    saveError.value = err.response?.data?.detail || '保存失败'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'activity-detail', params: { slug: route.params.slug } })
}
</script>

<template>
  <ActivityForm
    page-title="编辑活动"
    :initial-data="initialData"
    :submitting="saving"
    :submit-error="saveError"
    :loading="loading"
    :error="error"
    @submit="handleSave"
  >
    <template #actions="{ submitting }">
      <button type="submit" class="btn btn-primary" :disabled="submitting">
        {{ submitting ? '保存中...' : '保存' }}
      </button>
      <button type="button" class="btn btn-secondary" :disabled="submitting" @click="handleCancel">
        取消
      </button>
    </template>
  </ActivityForm>
</template>
