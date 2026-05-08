<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  members: { type: Array, default: () => [] },
  max: { type: Number, default: 1 },
  actionLabel: { type: String, default: '尽量安排与' },
  showPrivacy: { type: Boolean, default: true },
  privacyNote: { type: String, default: '此名单系统不会透露给任何人' },
  uploadsUrl: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const personLabel = computed(() => props.max === 1 ? '他/她' : '他/她们')

const heading = computed(() => `${props.actionLabel}${personLabel.value}同组`)

const selectedLabel = computed(() => {
  if (!props.modelValue.length) return '当前未指定'
  const names = props.modelValue.map(id => {
    const m = props.members.find(mb => mb.user_id === id)
    return m ? m.nickname : ''
  }).filter(Boolean)
  return `已指定 ${props.modelValue.length}（最多 ${props.max}）：${names.join('、')}`
})

const sortedMembers = computed(() => {
  return [...props.members].sort((a, b) => (a.nickname || '').localeCompare(b.nickname || '', 'zh-CN'))
})

function toggle(userId) {
  const arr = [...props.modelValue]
  const idx = arr.indexOf(userId)
  if (idx >= 0) {
    arr.splice(idx, 1)
  } else if (arr.length < props.max) {
    arr.push(userId)
  }
  emit('update:modelValue', arr)
}
</script>

<template>
  <div class="member-selector">
    <p class="ms-heading">{{ heading }}</p>
    <p v-if="showPrivacy" class="ms-subtitle">{{ privacyNote }}</p>
    <div class="ms-list">
      <p v-if="!sortedMembers.length" class="ms-empty">活动尚无人加入</p>
      <label
        v-for="m in sortedMembers"
        :key="m.user_id"
        class="ms-item"
        :class="{
          'ms-selected': modelValue.includes(m.user_id),
          'ms-disabled': !modelValue.includes(m.user_id) && modelValue.length >= max,
        }"
      >
        <input
          type="checkbox"
          :checked="modelValue.includes(m.user_id)"
          :disabled="!modelValue.includes(m.user_id) && modelValue.length >= max"
          @change="toggle(m.user_id)"
        />
        <span class="ms-avatar">
          <img v-if="m.avatar_path" :src="`${uploadsUrl}/${m.avatar_path}`" />
          <span v-else class="ms-avatar-placeholder">{{ (m.nickname || '?')[0] }}</span>
        </span>
        <span class="ms-name">{{ m.nickname }}<template v-if="m.attributes && Object.keys(m.attributes).length">（{{ Object.values(m.attributes).join('，') }}）</template></span>
      </label>
    </div>
    <p class="ms-summary">{{ selectedLabel }}</p>
  </div>
</template>

<style scoped>
.member-selector {
  margin-bottom: 12px;
}

.ms-heading {
  font-size: 13px;
  color: #555;
  margin: 0 0 4px 0;
  font-weight: 500;
}

.ms-subtitle {
  font-size: 12px;
  color: #aaa;
  margin: 0 0 8px 0;
}

.ms-list {
  max-height: 160px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 4px;
}

.ms-empty {
  padding: 8px;
  text-align: center;
  font-size: 12px;
  color: #aaa;
  margin: 0;
}

.ms-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #555;
  transition: background 0.15s;
}

.ms-item:hover {
  background: #f5f3ff;
}

.ms-item.ms-selected {
  background: #ede9fe;
}

.ms-item.ms-disabled {
  opacity: 0.4;
  cursor: default;
}

.ms-item input[type="checkbox"] {
  width: 15px;
  height: 15px;
  margin: 0;
  accent-color: #4f46e5;
  flex-shrink: 0;
}

.ms-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: #e0e0e0;
}

.ms-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ms-avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 11px;
  color: #888;
  font-weight: 600;
}

.ms-name {
  flex: 1;
}

.ms-summary {
  font-size: 11px;
  color: #666;
  margin: 4px 0 0 0;
}
</style>
