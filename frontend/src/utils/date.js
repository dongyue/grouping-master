export function formatDate(isoString) {
  if (!isoString) return ''
  return isoString.slice(0, 10)
}
