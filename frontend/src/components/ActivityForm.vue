<script setup>
import { ref, watch } from 'vue'
import { groupStrategyOptions } from '../utils/groupRule'
import ConstraintEditor from './ConstraintEditor.vue'

const MAX_PREF_COUNT = 10  // 与后端 config.py MAX_PREFERENCE_COUNT 同步

const props = defineProps({
  initialData: { type: Object, default: null },
  submitting: { type: Boolean, default: false },
  submitError: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  pageTitle: { type: String, default: '' },
  hintText: { type: String, default: '' },
})

const emit = defineEmits(['submit'])

const title = ref('')
const description = ref('')
const groupParam = ref(2)
const groupStrategy = ref('fixed_group_size')
const constraints = ref([])
const allowWantPreferences = ref(false)
const maxWantCount = ref(1)
const allowAvoidPreferences = ref(false)
const maxAvoidCount = ref(1)

function applyInitialData(data) {
  if (!data) return
  title.value = data.title || ''
  description.value = data.description || ''
  groupParam.value = data.group_param ?? 2
  groupStrategy.value = data.group_strategy ?? 'fixed_group_size'
  allowWantPreferences.value = data.allow_want_preferences ?? false
  maxWantCount.value = data.max_want_count ?? 1
  allowAvoidPreferences.value = data.allow_avoid_preferences ?? false
  maxAvoidCount.value = data.max_avoid_count ?? 1
  constraints.value = data.constraints || []
}

watch(() => props.initialData, applyInitialData)

function buildConstraints() {
  if (constraints.value.length === 0) return null
  return constraints.value.map(c => ({
    attribute_name: c.attribute_name,
    allowed_values: c.allowed_values_raw.split(/[,，]/).map(s => s.trim()).filter(s => s),
    constraint_type: c.constraint_type,
    constraint_value: c.constraint_value,
  }))
}

function handleSubmit() {
  emit('submit', {
    title: title.value,
    description: description.value || null,
    group_strategy: groupStrategy.value,
    group_param: Number(groupParam.value) || 2,
    constraints: buildConstraints(),
    allow_want_preferences: allowWantPreferences.value,
    max_want_count: Number(maxWantCount.value) || 1,
    allow_avoid_preferences: allowAvoidPreferences.value,
    max_avoid_count: Number(maxAvoidCount.value) || 1,
  })
}
</script>

<template>
  <div class="page-card">
    <div v-if="loading" style="text-align: center; color: #999; padding: 40px;">加载中...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else>
      <h1 class="page-title">{{ pageTitle }}</h1>
      <div v-if="submitError" class="error-msg">{{ submitError }}</div>
      <form @submit.prevent="handleSubmit">
        <p v-if="hintText" class="rule-hint">{{ hintText }}</p>
        <div class="form-group">
          <label>活动标题 *</label>
          <input v-model="title" type="text" required placeholder="输入活动标题" />
        </div>
        <div class="form-group">
          <label>活动描述 <span class="optional">(可选)</span></label>
          <textarea v-model="description" rows="3" placeholder="输入活动描述" class="textarea"></textarea>
        </div>
        <slot name="extra-fields" />
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
        <div class="form-group">
          <label>成员偏好设置</label>
          <div class="pref-row">
            <label class="checkbox-label">
              <input v-model="allowWantPreferences" type="checkbox" />
              <span>允许成员设置「想和谁同组」<template v-if="allowWantPreferences">，最多</template></span>
              <template v-if="allowWantPreferences">
                <input v-model.number="maxWantCount" type="number" min="1" :max="MAX_PREF_COUNT" class="pref-count-input" />
                <span>人</span>
              </template>
            </label>
          </div>
          <div class="pref-row">
            <label class="checkbox-label">
              <input v-model="allowAvoidPreferences" type="checkbox" />
              <span>允许成员设置「不想和谁同组」<template v-if="allowAvoidPreferences">，最多</template></span>
              <template v-if="allowAvoidPreferences">
                <input v-model.number="maxAvoidCount" type="number" :min="MIN_PREF_COUNT" :max="MAX_PREF_COUNT" class="pref-count-input" />
                <span>人</span>
              </template>
            </label>
          </div>
        </div>
        <div class="actions">
          <slot name="actions" :submitting="submitting" />
        </div>
      </form>
    </template>
  </div>
</template>

<style scoped>
.pref-row {
  margin-bottom: 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #555;
}

.pref-row input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin: 0;
  accent-color: #4f46e5;
  cursor: pointer;
  flex-shrink: 0;
}

.pref-count-input {
  width: 52px;
  height: 32px;
  padding: 0 6px;
  border: 1px solid #ccc;
  border-radius: 8px;
  text-align: center;
  font-size: 14px;
}

.rule-input {
  width: 52px;
  height: 32px;
  text-align: center;
  padding: 0 8px;
}

.rule-select {
  width: auto;
  height: 32px;
  min-width: 0;
}
</style>
