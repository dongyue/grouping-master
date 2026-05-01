<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getActivity, updateActivity } from '../api/activities'
import { groupStrategyOptions } from '../utils/groupRule'
import ConstraintEditor from '../components/ConstraintEditor.vue'

const route = useRoute()
const router = useRouter()

const title = ref('')
const description = ref('')
const groupParam = ref(2)
const groupStrategy = ref('fixed_group_size')
const constraints = ref([])
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
    groupParam.value = data.group_param ?? 2
    groupStrategy.value = data.group_strategy ?? 'fixed_group_size'
    if (data.constraints && data.constraints.length > 0) {
      constraints.value = data.constraints.map(c => ({
        attribute_name: c.attribute_name || '',
        allowed_values_raw: (c.allowed_values || []).join('，'),
        constraint_type: c.constraint_type || 'min_diversity',
        constraint_value: c.constraint_value || 1,
      }))
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
})

function buildConstraints() {
  if (constraints.value.length === 0) return null
  return constraints.value.map(c => ({
    attribute_name: c.attribute_name,
    allowed_values: c.allowed_values_raw.split(/[,，]/).map(s => s.trim()).filter(s => s),
    constraint_type: c.constraint_type,
    constraint_value: c.constraint_value,
  }))
}

async function handleSave() {
  saving.value = true
  saveError.value = ''
  try {
    await updateActivity(route.params.slug, {
      title: title.value,
      description: description.value || null,
      group_strategy: groupStrategy.value,
      group_param: groupParam.value,
      constraints: buildConstraints(),
    })
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
        <div class="form-group">
          <label>分组规则</label>
          <div class="group-rule-row">
            <select v-model="groupStrategy" class="rule-select">
              <option v-for="opt in groupStrategyOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <span class="rule-label">{{ groupStrategy === 'fixed_group_count' ? '，共' : '，每组' }}</span>
            <input v-model.number="groupParam" type="number" min="2" class="rule-input" />
            <span class="rule-label">{{ groupStrategy === 'fixed_group_count' ? '组' : '人' }}</span>
          </div>
        </div>
        <ConstraintEditor v-model="constraints" />
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

.group-rule-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-extra {
  margin-top: 8px;
}

.rule-label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}

.rule-input {
  width: 80px !important;
  text-align: center;
  padding: 0 8px !important;
}

.rule-select {
  min-width: 120px;
  max-width: 200px;
}

.rule-hint {
  margin: 6px 0 0 0;
  font-size: 12px;
  color: #aaa;
}
</style>
