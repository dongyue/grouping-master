<script setup>
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div id="app-container">
    <header v-if="auth.isLoggedIn" class="header">
      <div class="header-inner">
        <a href="/" @click.prevent="router.push('/')" class="logo">分组大师</a>
        <nav>
          <a href="/settings" @click.prevent="router.push('/settings')">设置</a>
          <a href="#" @click.prevent="handleLogout">退出</a>
        </nav>
      </div>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
  color: #333;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 24px;
}

.header-inner {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
}

.logo {
  font-size: 18px;
  font-weight: 700;
  color: #4f46e5;
  text-decoration: none;
}

nav a {
  color: #666;
  text-decoration: none;
  margin-left: 24px;
  font-size: 14px;
}

nav a:hover {
  color: #4f46e5;
}

main {
  max-width: 480px;
  margin: 40px auto;
  padding: 0 16px;
}

.page-card {
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 24px;
  text-align: center;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}

.form-group input {
  width: 100%;
  height: 42px;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: #4f46e5;
}

.form-group select {
  width: 100%;
  height: 42px;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  background: #fff;
  cursor: pointer;
}

.form-group select:focus {
  border-color: #4f46e5;
}

.btn {
  display: block;
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary {
  background: #4f46e5;
  color: #fff;
}

.btn-primary:hover {
  background: #4338ca;
}

.btn-secondary {
  background: #f3f4f6;
  color: #555;
  border: 1px solid #d0d0d0;
}

.btn-secondary:hover {
  background: #f5f5f5;
  border-color: #bbb;
}

.btn-warning {
  color: #e6a23c;
}

.btn-warning:hover {
  background: #fef5e7;
}

.btn-danger {
  background: #dc2626;
  color: #fff;
}

.btn-danger:hover {
  background: #b91c1c;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-msg {
  background: #fef2f2;
  color: #dc2626;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
}

.success-msg {
  background: #f0fdf4;
  color: #16a34a;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #999;
}

.form-footer a {
  color: #4f46e5;
  text-decoration: none;
}

.optional {
  font-size: 11px;
  color: #aaa;
  font-weight: 400;
}

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

.section-heading {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 20px 0 10px 0;
}

.group-rule-row {
  display: flex;
  align-items: center;
  gap: 8px;
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

.rule-extra {
  margin-top: 8px;
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
