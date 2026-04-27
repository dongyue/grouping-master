<script setup>
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="page-card">
    <h1 class="page-title">欢迎使用分组大师</h1>
    <p style="color: #666; text-align: center; margin-bottom: 20px;">
      你好，{{ auth.user?.nickname }}！
    </p>
    <p style="color: #999; text-align: center; font-size: 14px;">
      更多功能即将上线，敬请期待。
    </p>
  </div>
</template>
