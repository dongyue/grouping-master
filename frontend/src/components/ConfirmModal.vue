<script setup>
defineProps({
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '确定要执行此操作吗？' },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
})

const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <div class="modal-overlay" @click.self="emit('cancel')">
    <div class="modal-box">
      <h3 class="modal-title">{{ title }}</h3>
      <p class="modal-message">{{ message }}</p>
      <div class="modal-actions">
        <button class="btn btn-secondary" @click="emit('cancel')">{{ cancelText }}</button>
        <button class="btn btn-danger" @click="emit('confirm')">{{ confirmText }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  min-width: 320px;
  max-width: 400px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.16);
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.modal-message {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-actions .btn {
  width: auto;
  padding: 8px 24px;
  height: auto;
  font-size: 14px;
}
</style>
