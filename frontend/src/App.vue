<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { DataAnalysis, Picture, VideoCamera, Tickets, Cpu, ArrowRight, Menu } from '@element-plus/icons-vue'
import { api } from './api/index.js'

const route = useRoute()
const systemName = ref('安全帽佩戴检测系统')
const modelName = ref('best.pt')
const modelReady = ref(false)
const mobileMenu = ref(false)
const currentTitle = computed(() => route.meta.title || '数据概览')
const nav = [
  { path: '/', label: '数据概览', icon: DataAnalysis, index: '01' },
  { path: '/image', label: '图片检测', icon: Picture, index: '02' },
  { path: '/video', label: '视频检测', icon: VideoCamera, index: '03' },
  { path: '/records', label: '检测记录', icon: Tickets, index: '04' },
  { path: '/model', label: '模型信息', icon: Cpu, index: '05' },
]

onMounted(async () => {
  try {
    const info = await api.model()
    systemName.value = info.system_name
    modelName.value = info.name
    modelReady.value = info.ready
    document.title = info.system_name
  } catch { /* The page itself shows API errors where relevant. */ }
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ 'sidebar-open': mobileMenu }">
      <div class="brand">
        <div class="brand-mark"><span class="brand-core"></span></div>
        <div>
          <strong>HELMET<span>VISION</span></strong>
          <small>工地安全帽佩戴检测</small>
        </div>
      </div>

      <div class="sidebar-caption">工作空间 <span>WORKSPACE</span></div>
      <nav class="nav-list" aria-label="主导航">
        <RouterLink v-for="item in nav" :key="item.path" :to="item.path"
          class="nav-link" :class="{ active: route.path === item.path }" @click="mobileMenu = false">
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
          <small>{{ item.index }}</small>
        </RouterLink>
      </nav>

      <div class="sidebar-bottom">
        <div class="model-card">
          <span class="model-card-label">当前运行模型</span>
          <strong>{{ modelReady ? modelName : '等待接入模型' }}</strong>
          <span class="model-status"><i :class="{ muted: !modelReady }"></i>{{ modelReady ? '已就绪' : '未配置' }}</span>
          <RouterLink to="/model" @click="mobileMenu = false">查看模型信息 <el-icon><ArrowRight /></el-icon></RouterLink>
        </div>
        <div class="sidebar-footer">安全帽佩戴检测系统 <span>v1.0</span></div>
      </div>
    </aside>

    <div v-if="mobileMenu" class="mobile-shade" @click="mobileMenu = false"></div>
    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <button class="menu-toggle" aria-label="打开导航" @click="mobileMenu = !mobileMenu"><el-icon><Menu /></el-icon></button>
          <span class="breadcrumb-root">工作空间</span><span class="breadcrumb-sep">/</span><strong>{{ currentTitle }}</strong>
        </div>
        <div class="topbar-right"><span class="topbar-name">{{ systemName }}</span><span class="topbar-avatar">YO</span></div>
      </header>
      <main class="page-content"><RouterView /></main>
    </div>
  </div>
</template>
