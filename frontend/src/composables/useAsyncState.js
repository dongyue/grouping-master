import { ref } from 'vue'

export function useAsyncState(asyncFn, { onSuccess, onError } = {}) {
  const loading = ref(false)
  const error = ref('')
  const data = ref(null)

  async function execute(...args) {
    loading.value = true
    error.value = ''
    try {
      const result = await asyncFn(...args)
      data.value = result
      if (onSuccess) onSuccess(result)
      return result
    } catch (err) {
      const msg = err.response?.data?.detail || '操作失败'
      error.value = msg
      if (onError) onError(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return { loading, error, data, execute }
}
