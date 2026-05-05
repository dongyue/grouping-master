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

export function joinActivity(slug, data) {
  return api.post(`/activities/${slug}/join`, data)
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

export function getActivityLogs(slug, params) {
  return api.get(`/activities/${slug}/logs`, { params })
}

export function updateMemberInfo(slug, data) {
  return api.put(`/activities/${slug}/member-info`, data)
}

export function moveMember(slug, data) {
  return api.post(`/activities/${slug}/groups/move`, data)
}

export function createGroup(slug, data) {
  return api.post(`/activities/${slug}/groups/create`, data)
}

export function deleteGroup(slug, data) {
  return api.post(`/activities/${slug}/groups/delete`, data)
}

