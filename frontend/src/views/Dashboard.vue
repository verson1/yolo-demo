<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ArrowRight, Picture, VideoCamera, Aim, Calendar } from '@element-plus/icons-vue'
import { api } from '../api/index.js'

const loading = ref(true)
const error = ref('')
const description = ref('查看安全帽佩戴情况与未佩戴记录。')
const summary = ref({ total_records: 0, today_records: 0, helmet_count: 0, no_helmet_count: 0, violation_records: 0, recent: [] })
const distribution = ref([])
const trend = ref([])
const trendEl = ref(null)
const classEl = ref(null)
let trendChart
let classChart

function draw() {
  if (!trendEl.value || !classEl.value) return
  trendChart ||= echarts.init(trendEl.value)
  classChart ||= echarts.init(classEl.value)
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - 6 + i)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  })
  const counts = Object.fromEntries(trend.value.map(item => [item.day, item.records]))
  const violations = Object.fromEntries(trend.value.map(item => [item.day, item.violations]))
  trendChart.setOption({
    animationDuration: 500,
    tooltip: { trigger: 'axis' },
    grid: { left: 35, right: 15, top: 24, bottom: 28 },
    xAxis: { type: 'category', data: days.map(day => day.slice(5)), axisTick: { show: false }, axisLine: { lineStyle: { color: '#e9efed' } }, axisLabel: { color: '#9aabaa', fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#eef3f0' } }, axisLabel: { color: '#9aabaa', fontSize: 10 } },
    series: [{ name: '检测次数', type: 'line', smooth: true, symbolSize: 7, data: days.map(day => counts[day] || 0), itemStyle: { color: '#38b589' }, lineStyle: { width: 3 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#52c89a55' }, { offset: 1, color: '#52c89a00' }]) } }, { name: '含未佩戴目标的任务', type: 'line', smooth: true, symbolSize: 7, data: days.map(day => violations[day] || 0), itemStyle: { color: '#ec806d' }, lineStyle: { width: 2 } }],
  })
  classChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle', itemWidth: 7, itemHeight: 7, textStyle: { color: '#829496', fontSize: 10 } },
    color: ['#35b889', '#6bd0aa', '#96d9bf', '#248d76', '#aedfcd', '#acc8c0'],
    series: [{ type: 'pie', radius: ['50%', '71%'], center: ['50%', '43%'], avoidLabelOverlap: true, label: { show: false }, data: distribution.value.length ? distribution.value : [{ name: '暂无数据', value: 1, itemStyle: { color: '#e8efeb' } }] }],
  })
}

function resize() { trendChart?.resize(); classChart?.resize() }

onMounted(async () => {
  try {
    const [summaryData, classData, trendData, modelData] = await Promise.all([api.summary(), api.classes(), api.trend(), api.model()])
    summary.value = summaryData; distribution.value = classData.map(item => ({ ...item, name: item.wearing_status === 'violation' ? '未佩戴' : '已佩戴' })); trend.value = trendData
    description.value = modelData.description || description.value
    await nextTick()
    draw()
    window.addEventListener('resize', resize)
  } catch (exc) { error.value = exc.message }
  finally { loading.value = false }
})
onBeforeUnmount(() => { window.removeEventListener('resize', resize); trendChart?.dispose(); classChart?.dispose() })

const cards = [
  { key: 'total_records', label: '累计检测任务', icon: Aim, className: 'teal', suffix: '次' },
  { key: 'helmet_count', label: '已佩戴检测框', icon: Picture, className: 'blue', suffix: '次' },
  { key: 'no_helmet_count', label: '未佩戴检测框', icon: Calendar, className: 'orange', suffix: '次' },
  { key: 'violation_records', label: '含未佩戴目标的任务', icon: VideoCamera, className: 'purple', suffix: '次' },
]
</script>

<template>
  <div>
    <div class="page-heading">
      <div><div class="eyebrow">OVERVIEW / 数据看板</div><h1>数据概览</h1><p>{{ description }}</p></div>
      <RouterLink to="/image"><el-button type="primary" class="primary-action">开始图片检测 <el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button></RouterLink>
    </div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <div class="metric-grid" v-loading="loading">
      <div v-for="card in cards" :key="card.key" class="metric-card panel">
        <div class="metric-icon" :class="card.className"><el-icon><component :is="card.icon" /></el-icon></div>
        <span>{{ card.label }}</span>
        <div><strong>{{ summary[card.key] }}</strong><small>{{ card.suffix }}</small></div>
        <div class="metric-foot">实时统计 <span>↗</span></div>
      </div>
    </div>
    <div class="chart-grid">
      <section class="panel"><div class="panel-header"><div><h2 class="section-title">近 7 天检测趋势</h2><p class="panel-subtitle">检测任务与含未佩戴目标的任务</p></div><span class="chart-badge">最近 7 天</span></div><div ref="trendEl" class="chart"></div></section>
      <section class="panel"><div class="panel-header"><div><h2 class="section-title">佩戴状态分布</h2><p class="panel-subtitle">当前模型的历史检测框统计</p></div></div><div ref="classEl" class="chart"></div></section>
    </div>
    <section class="panel recent-panel">
      <div class="panel-header"><div><h2 class="section-title">最近检测</h2><p class="panel-subtitle">最新的 5 条检测记录</p></div><RouterLink to="/records" class="view-all">查看全部 <el-icon><ArrowRight /></el-icon></RouterLink></div>
      <div v-if="!summary.recent.length" class="empty-state"><strong>还没有检测记录</strong>上传一张图片，开始你的第一次识别。</div>
      <div v-else class="recent-list"><RouterLink v-for="record in summary.recent" :key="record.id" :to="`/records?id=${record.id}`" class="recent-item"><div class="recent-icon"><el-icon><component :is="record.detect_type === 'image' ? Picture : VideoCamera" /></el-icon></div><div><strong>{{ record.detect_type === 'image' ? '图片检测' : '视频检测' }} #{{ record.id }}</strong><span>{{ record.created_at }}</span></div><div class="recent-count">{{ record.no_helmet_count ? `未佩戴 ${record.no_helmet_count} 次` : record.helmet_count ? '仅检出已佩戴' : '未检出目标' }}</div><el-icon class="recent-arrow"><ArrowRight /></el-icon></RouterLink></div>
    </section>
  </div>
</template>

<style scoped>
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.metric-card{min-height:156px;padding:19px 22px}.metric-icon{width:34px;height:34px;border-radius:9px;display:grid;place-items:center;font-size:18px;margin-bottom:12px}.metric-icon.teal{background:#e4f8ee;color:#2ead80}.metric-icon.blue{background:#e8f3fc;color:#54a1d2}.metric-icon.orange{background:#fff2e5;color:#e3a15d}.metric-icon.purple{background:#f0ecfc;color:#9c87d7}.metric-card>span{font-size:11px;color:#95a5a6}.metric-card>div:nth-of-type(2){display:flex;align-items:baseline;gap:6px;margin:4px 0 9px}.metric-card strong{font-size:28px;color:#21363a;letter-spacing:-1px}.metric-card small{font-size:10px;color:#99a6a8}.metric-foot{border-top:1px solid #f0f3f2;padding-top:9px;color:#a3b0b1;font-size:10px;display:flex;justify-content:space-between}.metric-foot span{color:#49bb8f;font-size:13px}.chart-grid{display:grid;grid-template-columns:1.55fr 1fr;gap:18px;margin-top:19px}.chart{height:280px;margin:4px 15px 10px}.chart-badge{font-size:10px;color:#5baf88;background:#ecf8f1;padding:7px 9px;border-radius:6px}.recent-panel{margin-top:19px}.view-all{display:flex;align-items:center;gap:4px;color:#2ca87d;font-size:11px}.recent-list{padding:5px 24px 14px}.recent-item{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #f0f3f2;color:inherit}.recent-item:last-child{border:0}.recent-icon{width:35px;height:35px;border-radius:8px;display:grid;place-items:center;background:#eaf7ef;color:#3caf80}.recent-item strong,.recent-item span{display:block}.recent-item strong{font-size:12px}.recent-item span{font-size:10px;color:#a1acae;margin-top:3px}.recent-count{margin-left:auto;color:#697f80;font-size:11px}.recent-arrow{color:#adbcbd}@media(max-width:1050px){.metric-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:700px){.metric-grid,.chart-grid{grid-template-columns:1fr}.page-heading{align-items:flex-start;flex-direction:column}.chart{height:240px}}
</style>
