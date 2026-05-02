<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createActivity } from '../api/activities'
import { groupStrategyOptions } from '../utils/groupRule'
import ConstraintEditor from '../components/ConstraintEditor.vue'

const router = useRouter()

const title = ref('')
const description = ref('')
const joinActivity = ref(true)
const groupParam = ref(2)
const groupStrategy = ref('fixed_group_size')
const constraints = ref([])
const error = ref('')
const creating = ref(false)

function buildConstraints() {
  if (constraints.value.length === 0) return null
  return constraints.value.map(c => ({
    attribute_name: c.attribute_name,
    allowed_values: c.allowed_values_raw.split(/[,，]/).map(s => s.trim()).filter(s => s),
    constraint_type: c.constraint_type,
    constraint_value: c.constraint_value,
  }))
}

async function handleCreate() {
  error.value = ''
  creating.value = true
  try {
    const res = await createActivity({
      title: title.value,
      description: description.value || null,
      group_strategy: groupStrategy.value,
      group_param: groupParam.value,
      constraints: buildConstraints(),
    })
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
  <div class="page-card">
    <h1 class="page-title">创建活动</h1>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <form @submit.prevent="handleCreate">
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
          <span>我作为创建者也要参加</span>
        </label>
      </div>
      <h3 class="section-heading">分组规则</h3>
      <div class="form-group">
        <label>分组方式</label>
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
      <p class="rule-hint">创建后可在编辑页中修改上述设置</p>
      <div class="actions">
        <button type="submit" class="btn btn-primary" :disabled="creating">
          {{ creating ? '创建中...' : '创建活动' }}
        </button>
        <button type="button" class="btn btn-secondary" :disabled="creating" @click="handleCancel">
          取消
        </button>
      </div>
    </form>
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

.group-rule-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-extra {
  margin-top: 8px;
}

.section-heading {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 20px 0 10px 0;
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
  margin: 6px 0 16px 0;
  font-size: 12px;
  color: #aaa;
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
