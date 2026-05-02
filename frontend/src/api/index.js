import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const detail = error.response.data?.detail
      // FastAPI 422 校验错误：detail 是数组 [{loc, msg, type}]
      if (Array.isArray(detail)) {
        const messages = detail.map((e) => {
          const field = e.loc?.slice(-1)[0] || ''
          return `${field}: ${e.msg}`
        })
        error.response.data.detail = messages.join('; ')
      }
      if (!error.response.data?.detail) {
        const statusMessages = {
          400: '请求参数有误',
          401: '请先登录',
          403: '无权限执行此操作',
          404: '请求的资源不存在',
          409: '数据冲突，请刷新后重试',
          429: '请求过于频繁，请稍后再试',
          500: '服务器内部错误',
        }
        error.response.data = {
          ...error.response.data,
          detail: statusMessages[error.response.status] || `请求失败 (${error.response.status})`,
        }
      }
    } else if (error.code === 'ERR_NETWORK') {
      error.response = {
        data: { detail: '无法连接到服务器，请确认后端已启动' },
      }
    }
    return Promise.reject(error)
  },
)

export default api
