import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)

app.config.errorHandler = (err, instance, info) => {
  console.error('Vue 全局错误:', err, info)
}

app.use(createPinia())
app.use(router)
app.mount('#app')
