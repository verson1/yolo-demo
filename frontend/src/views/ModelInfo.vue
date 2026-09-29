<script setup>
import { computed, onMounted, ref } from 'vue'
import { Cpu, Check, Warning } from '@element-plus/icons-vue'
import { api } from '../api/index.js'

const info = ref(null)
const error = ref('')
const helmetClasses = computed(() => info.value?.classes.filter(item => info.value.helmet_class_ids?.includes(item.id)) || [])
onMounted(async () => { try { info.value = await api.model() } catch (exc) { error.value = exc.message } })
</script>

<template>
  <div>
    <div class="page-heading"><div><div class="eyebrow">HELMET / MODEL</div><h1>安全帽模型信息</h1><p>系统只使用权重中的“已佩戴”和“未佩戴”两类检测结果。</p></div><span v-if="info" class="pill" :class="{ warn: !info.ready }">{{ info.ready ? '模型已就绪' : '模型未配置' }}</span></div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="info" class="info-grid"><section class="panel info-card"><div class="info-top"><div class="model-icon"><el-icon><Cpu /></el-icon></div><div><h2>{{ info.name }}</h2><p>Ultralytics YOLO · 安全帽检测</p></div></div><div class="info-row"><span>系统名称</span><strong>{{ info.system_name }}</strong></div><div class="info-row"><span>模型版本</span><strong>{{ info.model_id }}</strong></div><div class="info-row"><span>模型路径</span><strong>{{ info.path }}</strong></div><div class="info-row"><span>启用类别</span><strong>{{ helmetClasses.length }} / {{ info.classes.length }}</strong></div><div class="info-row"><span>默认置信度</span><strong>{{ Math.round(info.default_confidence * 100) }}%</strong></div><div class="info-row"><span>运行状态</span><strong :class="info.ready ? 'ready-text' : 'warn-text'"><el-icon><component :is="info.ready ? Check : Warning" /></el-icon> {{ info.ready ? '可用于检测' : '需要安全帽权重' }}</strong></div></section><section class="panel info-card"><h2 class="section-title">启用的检测类别</h2><p class="helper-text">类别编号来自模型权重，系统自动映射为佩戴状态。</p><div v-if="helmetClasses.length" class="class-chips"><span v-for="item in helmetClasses" :key="item.id" class="class-chip"><b>{{ String(item.id).padStart(2, '0') }}</b>{{ item.name }}</span></div><div v-else class="empty-state"><strong>模型未就绪</strong>请接入同时包含安全帽与未佩戴安全帽类别的权重。</div><div class="notice" style="margin-top:25px">{{ info.ready ? '未检出目标时结果为“未知”，不会自动判断全部人员合规。更换权重后重启后端。' : info.message }}</div></section></div>
  </div>
</template>

<style scoped>.info-top{display:flex;align-items:center;gap:14px;margin-bottom:18px}.model-icon{display:grid;place-items:center;width:50px;height:50px;border-radius:12px;background:#e8f8ee;color:#2ead7e;font-size:25px}.info-top h2{font-size:17px;color:#23383b;margin:0}.info-top p{font-size:11px;color:#9aa8aa;margin:5px 0 0}.ready-text{color:#2da879!important}.warn-text{color:#c88b3b!important}.info-row .el-icon{vertical-align:-2px}</style>
