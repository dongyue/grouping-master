import api from './index'

export function createActivity(data) {
  return api.post('/activities', data)
}

export function listActivities(type) {
  return api.get('/activities', { params: { type } })
}

export function getActivity(id) {
  return api.get(`/activities/${id}`)
}

export function joinActivity(id) {
  return api.post(`/activities/${id}/join`)
}

export function leaveActivity(id) {
  return api.post(`/activities/${id}/leave`)
}

export function deleteActivity(id) {
  return api.delete(`/activities/${id}`)
}
