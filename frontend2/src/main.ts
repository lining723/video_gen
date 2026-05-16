import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/global.scss'

const app = createApp(App)
app.use(ElementPlus, { size: 'default' })
app.use(createPinia())
app.use(router)
app.mount('#app')
