import api from './index'

export function getAuthConfig() {
  return api.get('/auth/config')
}

export function register(data) {
  return api.post('/auth/register', data)
}

export function login(data) {
  return api.post('/auth/login', data)
}

export function logout() {
  return api.post('/auth/logout')
}

export function getCurrentUser() {
  return api.get('/auth/me')
}

export function changePassword(data) {
  return api.put('/auth/password', data)
}

export function forgotPassword(data) {
  return api.post('/auth/forgot-password', data)
}

export function resetPassword(data) {
  return api.post('/auth/reset-password', data)
}

export function updateProfile(data) {
  return api.put('/auth/profile', data)
}

export function uploadAvatar(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/auth/avatar', formData)
}

export function deleteAccount() {
  return api.delete('/auth/account')
}
