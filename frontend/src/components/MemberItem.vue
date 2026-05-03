<script setup>
const props = defineProps({
  member: { type: Object, required: true },
  currentUserId: { type: Number, required: true },
  isCreator: { type: Boolean, default: false },
  showKick: { type: Boolean, default: false },
  kickingUserId: { type: Number, default: null },
  uploadsUrl: { type: String, required: true },
  groupLabel: { type: String, default: '' },
})

const emit = defineEmits(['edit', 'kick'])
</script>

<template>
  <div class="member-item" :class="{ 'is-me': member.user_id === currentUserId }">
    <div class="member-avatar">
      <img v-if="member.avatar_path" :src="`${uploadsUrl}/${member.avatar_path}`" />
      <span v-else class="avatar-placeholder">{{ member.nickname[0] }}</span>
    </div>
    <span v-if="groupLabel" class="group-label" :class="{ 'ungrouped-label': groupLabel === '落单' }">{{ groupLabel }}</span>
    <span class="member-nickname">{{ member.nickname }}</span>
    <span v-if="member.attributes && Object.keys(member.attributes).length" class="member-attrs">
      <span v-for="(val, key) in member.attributes" :key="key" class="attr-tag">{{ val }}</span>
    </span>
    <span v-if="member.attribute_warnings?.length" class="warn-icon" :title="member.attribute_warnings.join('\n')">&#9888;</span>
    <span v-if="member.user_id === currentUserId" class="edit-icon" @click="$emit('edit')" title="编辑个人信息">&#x270E;</span>
    <button
      v-if="isCreator && member.user_id !== currentUserId && showKick"
      class="btn-kick"
      :disabled="kickingUserId === member.user_id"
      @click="$emit('kick', member.user_id, member.nickname)"
    >
      {{ kickingUserId === member.user_id ? '踢出中...' : '踢出' }}
    </button>
  </div>
</template>

<style scoped>
.member-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.member-item.is-me {
  background: #ede9fe;
  outline: 2px solid #a78bfa;
}

.member-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: #e0e0e0;
}

.member-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 12px;
  color: #888;
  font-weight: 600;
  text-transform: uppercase;
}

.member-nickname {
  font-size: 13px;
  color: #333;
}

.member-attrs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-left: auto;
}

.attr-tag {
  font-size: 11px;
  padding: 1px 6px;
  background: #f0f0f0;
  color: #888;
  border-radius: 3px;
}

.group-label {
  font-size: 11px;
  padding: 1px 6px;
  background: #ede9fe;
  color: #6d28d9;
  border-radius: 3px;
  white-space: nowrap;
  flex-shrink: 0;
}

.group-label.ungrouped-label {
  background: #fef3c7;
  color: #b45309;
}

.warn-icon {
  font-size: 14px;
  color: #e63946;
  cursor: help;
  flex-shrink: 0;
}

.edit-icon {
  font-size: 14px;
  color: #4f46e5;
  cursor: pointer;
  flex-shrink: 0;
}

.edit-icon:hover {
  color: #3730a3;
}

.btn-kick {
  font-size: 11px;
  padding: 2px 10px;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  background: transparent;
  color: #e74c3c;
  cursor: pointer;
  margin-left: auto;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.btn-kick:hover:not(:disabled) {
  background: #e74c3c;
  color: #fff;
}

.btn-kick:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
