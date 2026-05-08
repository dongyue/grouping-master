<script setup>
import { ref, computed } from 'vue'
import MemberSelector from './MemberSelector.vue'

const props = defineProps({
  constraints: { type: Array, default: () => [] },
  submitting: { type: Boolean, default: false },
  initialNickname: { type: String, default: '' },
  initialValues: { type: Object, default: () => ({}) },
  userAttributes: { type: Object, default: () => ({}) },
  confirmLabel: { type: String, default: '确认加入' },
  activityMembers: { type: Array, default: () => [] },
  allowWantPreferences: { type: Boolean, default: false },
  maxWantCount: { type: Number, default: 1 },
  allowAvoidPreferences: { type: Boolean, default: false },
  maxAvoidCount: { type: Number, default: 1 },
  initialPreferences: { type: Object, default: () => ({ want: [], avoid: [] }) },
  currentUserId: { type: Number, default: null },
  uploadsUrl: { type: String, default: '' },
})

const emit = defineEmits(['confirm', 'cancel'])

const nickname = ref(props.initialNickname)

const initValues = {}
for (const c of props.constraints) {
  let val = props.initialValues[c.attribute_name]
  if (!val || !c.allowed_values.includes(val)) {
    val = props.userAttributes[c.attribute_name]
  }
  if (val && c.allowed_values.includes(val)) {
    initValues[c.attribute_name] = val
  }
}
const values = ref(initValues)
const error = ref('')

const wantSelected = ref([...props.initialPreferences.want])
const avoidSelected = ref([...props.initialPreferences.avoid])

const otherMembers = computed(() => {
  return props.activityMembers.filter(m => m.user_id !== props.currentUserId)
})

const attributes = computed(() => {
  return props.constraints.map(c => ({
    name: c.attribute_name,
    allowed: c.allowed_values,
  }))
})

function handleSubmit() {
  error.value = ''
  if (!nickname.value.trim()) {
    error.value = '请输入昵称'
    return
  }
  const result = {}
  for (const attr of attributes.value) {
    const v = values.value[attr.name]
    if (!v) {
      error.value = `请为「${attr.name}」选择一个值`
      return
    }
    result[attr.name] = v
  }
  const preferences = {}
  if (props.allowWantPreferences || props.allowAvoidPreferences) {
    if (props.allowWantPreferences) preferences.want = wantSelected.value
    if (props.allowAvoidPreferences) preferences.avoid = avoidSelected.value
  }
  emit('confirm', {
    nickname: nickname.value.trim(),
    attributeValues: result,
    preferences: Object.keys(preferences).length ? preferences : null,
  })
}
</script>

<template>
  <div class="overlay" @click.self="emit('cancel')">
    <div class="modal">
      <h3 class="modal-title">我在本活动中的个人信息</h3>
      <p class="pref-footer">请在本页填写您在本次活动中的个人信息，加入活动后可在编辑页中继续修改完善</p>
      <div class="fields">
        <div class="field">
          <label>昵称</label>
          <input v-model="nickname" type="text" placeholder="你的显示昵称" />
          <span class="field-hint">此处有时宜填写真实姓名</span>
        </div>
        <div v-for="attr in attributes" :key="attr.name" class="field">
          <label>{{ attr.name }}</label>
          <select v-model="values[attr.name]">
            <option value="" disabled>请选择</option>
            <option v-for="v in attr.allowed" :key="v" :value="v">{{ v }}</option>
          </select>
        </div>
        <div v-if="allowWantPreferences" class="field">
          <MemberSelector
            v-model="wantSelected"
            :members="otherMembers"
            :max="maxWantCount"
            action-label="尽量安排与"
            :privacy-note="allowAvoidPreferences ? '请在活动已有成员中指定；此名单系统不会透露给任何人（下同）' : '请在活动已有成员中指定；此名单系统不会透露给任何人'"
            :uploads-url="uploadsUrl"
          />
        </div>
        <div v-if="allowAvoidPreferences" class="field">
          <MemberSelector
            v-model="avoidSelected"
            :members="otherMembers"
            :max="maxAvoidCount"
            action-label="尽量避免与"
            :show-privacy="!allowWantPreferences"
            :uploads-url="uploadsUrl"
          />
        </div>
      </div>
      <div v-if="error" class="error-msg">{{ error }}</div>
      <div class="actions">
        <button class="btn btn-primary" :disabled="submitting" @click="handleSubmit">
          {{ submitting ? '提交中...' : confirmLabel }}
        </button>
        <button class="btn btn-secondary" :disabled="submitting" @click="emit('cancel')">
          取消
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  background: #fff;
  border-radius: 12px;
  padding: 28px 32px;
  width: 440px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}
.modal-title {
  font-size: 17px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px 0;
  text-align: center;
}
.fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 12px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}
.field-hint {
  font-size: 11px;
  color: #aaa;
  margin-top: 2px;
}
.field input,
.field select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: #fff;
  transition: border-color 0.2s;
}
.field input:focus,
.field select:focus {
  border-color: #4f46e5;
}
.error-msg {
  color: #e74c3c;
  font-size: 13px;
  margin-bottom: 12px;
}
.actions {
  display: flex;
  gap: 12px;
}
.actions .btn {
  flex: 1;
}
.pref-footer {
  font-size: 12px;
  color: #aaa;
  margin: 0 0 8px 0;
}
</style>
