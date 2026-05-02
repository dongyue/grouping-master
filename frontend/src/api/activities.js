import api from './index'

export function createActivity(data) {
  return api.post('/activities', data)
}

export function listActivities(type) {
  return api.get('/activities', { params: { type } })
}

export function getActivity(slug) {
  return api.get(`/activities/${slug}`)
}

export function joinActivity(slug, attributeValues = null) {
  return api.post(`/activities/${slug}/join`, { attribute_values: attributeValues })
}

export function leaveActivity(slug) {
  return api.post(`/activities/${slug}/leave`)
}

export function deleteActivity(slug) {
  return api.delete(`/activities/${slug}`)
}

export function kickMember(slug, userId) {
  return api.delete(`/activities/${slug}/members/${userId}`)
}

export function updateActivity(slug, data) {
  return api.put(`/activities/${slug}`, data)
}

export function createGroups(slug) {
  return api.post(`/activities/${slug}/groups`)
}

export function deleteGroups(slug) {
  return api.delete(`/activities/${slug}/groups`)
}

export function getActivityLogs(slug) {
  return api.get(`/activities/${slug}/logs`)
}

