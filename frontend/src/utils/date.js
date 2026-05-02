export function formatDate(isoString) {
  if (!isoString) return ''
  return isoString.slice(0, 10)
}

export function formatDateTime(isoString) {
  if (!isoString) return ''
  return isoString.slice(0, 19).replace('T', ' ')
}
