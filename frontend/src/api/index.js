import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
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
    } else if (error.code === 'ERR_NETWORK') {
      error.response = {
        data: { detail: '无法连接到服务器，请确认后端已启动' },
      }
    }
    return Promise.reject(error)
  },
)

export default api
