import api from './index'

export function createActivity(data) {
  return api.post('/activities', data)
}

export function listActivities() {
  return api.get('/activities')
}

export function getActivity(id) {
  return api.get(`/activities/${id}`)
}
