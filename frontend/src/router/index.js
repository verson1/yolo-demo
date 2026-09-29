import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ImageDetect from '../views/ImageDetect.vue'
import VideoDetect from '../views/VideoDetect.vue'
import Records from '../views/Records.vue'
import ModelInfo from '../views/ModelInfo.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { title: '数据概览' } },
    { path: '/image', component: ImageDetect, meta: { title: '图片检测' } },
    { path: '/video', component: VideoDetect, meta: { title: '视频检测' } },
    { path: '/records', component: Records, meta: { title: '检测记录' } },
    { path: '/model', component: ModelInfo, meta: { title: '模型信息' } },
  ],
})
