<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  constraints: { type: Array, required: true },
  submitting: { type: Boolean, default: false },
  initialValues: { type: Object, default: () => ({}) },
  userAttributes: { type: Object, default: () => ({}) },
  confirmLabel: { type: String, default: '确认加入' },
})

const emit = defineEmits(['confirm', 'cancel'])

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

const attributes = computed(() => {
  return props.constraints.map(c => ({
    name: c.attribute_name,
    allowed: c.allowed_values,
  }))
})

function handleSubmit() {
  error.value = ''
  const result = {}
  for (const attr of attributes.value) {
    const v = values.value[attr.name]
    if (!v) {
      error.value = `请为「${attr.name}」选择一个值`
      return
    }
    result[attr.name] = v
  }
  emit('confirm', result)
}
</script>

<template>
  <div class="overlay" @click.self="emit('cancel')">
    <div class="modal">
      <h3 class="modal-title">我的信息</h3>
      <div class="fields">
        <div v-for="attr in attributes" :key="attr.name" class="field">
          <label>{{ attr.name }}</label>
          <select v-model="values[attr.name]">
            <option value="" disabled>请选择</option>
            <option v-for="v in attr.allowed" :key="v" :value="v">{{ v }}</option>
          </select>
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
  width: 400px;
  max-width: 90vw;
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
.field select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: #fff;
  transition: border-color 0.2s;
}
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
</style>
