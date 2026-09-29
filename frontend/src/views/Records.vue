<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture, VideoCamera, View, Delete, Refresh } from '@element-plus/icons-vue'
import { api } from '../api/index.js'

const route = useRoute()
const router = useRouter()
const records = ref([])
const total = ref(0)
const page = ref(1)
const type = ref('')
const loading = ref(false)
const error = ref('')
const detail = ref(null)
const detailOpen = ref(false)

async function load() {
  loading.value = true; error.value = ''
  try { const data = await api.records({ page: page.value, page_size: 10, type: type.value }); records.value = data.items; total.value = data.total }
  catch (exc) { error.value = exc.message }
  finally { loading.value = false }
}
async function show(id) {
  try { detail.value = await api.record(id); detailOpen.value = true }
  catch (exc) { ElMessage.error(exc.message) }
}
async function remove(id) {
  try {
    await ElMessageBox.confirm('删除这条记录及其原始文件、结果文件？', '确认删除', { type: 'warning' })
    await api.deleteRecord(id)
    ElMessage.success('记录已删除')
    if (detail.value?.id === id) detailOpen.value = false
    await load()
  } catch (exc) { if (exc !== 'cancel' && exc !== 'close') ElMessage.error(exc.message || '删除失败') }
}
function filter(value) { type.value = value; page.value = 1; load() }
onMounted(load)
watch(() => route.query.id, id => { if (id) show(id) }, { immediate: true })
function closeDetail() { router.replace({ path: '/records' }) }
</script>

<template>
  <div>
    <div class="page-heading"><div><div class="eyebrow">HELMET / RECORDS</div><h1>安全帽检测记录</h1><p>回看当前模型的佩戴与未佩戴检测结果。</p></div><el-button class="secondary-action" @click="load"><el-icon><Refresh /></el-icon> 刷新列表</el-button></div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <section class="panel records-panel">
      <div class="records-toolbar"><h2 class="section-title">全部记录 <span>{{ total }}</span></h2><el-radio-group :model-value="type" size="small" @change="filter"><el-radio-button value="">全部</el-radio-button><el-radio-button value="image">图片</el-radio-button><el-radio-button value="video">视频</el-radio-button></el-radio-group></div>
      <div class="table-wrap"><el-table v-loading="loading" :data="records" empty-text="暂无记录，先去完成一次检测吧">
        <el-table-column label="检测任务" min-width="170"><template #default="scope"><div class="record-type"><span class="record-icon"><el-icon><component :is="scope.row.detect_type === 'image' ? Picture : VideoCamera" /></el-icon></span><div><strong>{{ scope.row.detect_type === 'image' ? '图片检测' : '视频检测' }}</strong><small>#{{ scope.row.id }}</small></div></div></template></el-table-column>
        <el-table-column label="已佩戴框" min-width="90" prop="helmet_count" />
        <el-table-column label="未佩戴框" min-width="95"><template #default="scope"><strong :class="{ 'warn-text': scope.row.no_helmet_count }">{{ scope.row.no_helmet_count }}</strong></template></el-table-column>
        <el-table-column label="结果" min-width="115"><template #default="scope">{{ scope.row.status === 'violation' ? '发现未佩戴' : scope.row.status === 'compliant' ? '仅检出已佩戴' : '未检出目标' }}</template></el-table-column>
        <el-table-column label="置信度" min-width="105"><template #default="scope">{{ Math.round(scope.row.confidence * 100) }}%</template></el-table-column>
        <el-table-column prop="created_at" label="检测时间" min-width="175" />
        <el-table-column label="操作" width="130" fixed="right"><template #default="scope"><el-button text type="primary" size="small" @click="show(scope.row.id)"><el-icon><View /></el-icon> 详情</el-button><el-button text type="danger" size="small" @click="remove(scope.row.id)"><el-icon><Delete /></el-icon></el-button></template></el-table-column>
      </el-table></div>
      <div v-if="total > 10" class="pagination-row"><el-pagination v-model:current-page="page" background layout="prev, pager, next" :page-size="10" :total="total" @current-change="load" /></div>
    </section>
    <el-dialog v-model="detailOpen" title="检测详情" width="min(760px, 94vw)" destroy-on-close @closed="closeDetail">
      <div v-if="detail">
        <div class="detail-meta"><span class="tag-soft">{{ detail.detect_type === 'image' ? '图片检测' : '视频检测' }}</span><span>#{{ detail.id }}</span><span>{{ detail.created_at }}</span><span>已佩戴 {{ detail.helmet_count }} · 未佩戴 {{ detail.no_helmet_count }}</span><span v-if="detail.detect_type === 'video'">未佩戴帧数 {{ detail.violation_frames }}</span></div>
        <div class="detail-media-grid"><div><strong>原始{{ detail.detect_type === 'image' ? '图片' : '视频' }} · <a :href="detail.original_url" download style="color:#2ca87d">下载</a></strong><img v-if="detail.detect_type === 'image'" :src="detail.original_url" alt="原始图片" /><video v-else :src="detail.original_url" controls></video></div><div><strong>结果{{ detail.detect_type === 'image' ? '图片' : '视频' }} · <a :href="detail.result_url" download style="color:#2ca87d">下载</a></strong><img v-if="detail.detect_type === 'image'" :src="detail.result_url" alt="结果图片" /><video v-else :src="detail.result_url" controls></video></div></div>
        <div v-if="detail.detect_type === 'image'" class="table-wrap"><el-table :data="detail.objects" max-height="220" empty-text="未检测到安全帽相关目标"><el-table-column label="佩戴状态"><template #default="scope">{{ scope.row.wearing_status === 'violation' ? '未佩戴' : '已佩戴' }}</template></el-table-column><el-table-column label="置信度"><template #default="scope">{{ (scope.row.confidence * 100).toFixed(1) }}%</template></el-table-column><el-table-column label="位置"><template #default="scope">{{ [scope.row.x1, scope.row.y1, scope.row.x2, scope.row.y2].map(Math.round).join(', ') }}</template></el-table-column></el-table></div>
        <div v-else class="class-chips"><span v-for="item in detail.classes" :key="item.class_name" class="class-chip">{{ item.wearing_status === 'violation' ? '未佩戴' : '已佩戴' }} · {{ item.count }}</span></div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>.records-panel{overflow:hidden}.records-toolbar{display:flex;align-items:center;justify-content:space-between;padding:20px 23px;gap:12px}.records-toolbar h2 span{color:#79ad97;font-size:11px;margin-left:5px}.record-type{display:flex;align-items:center;gap:10px}.record-icon{width:31px;height:31px;border-radius:8px;background:#e9f8ee;color:#37ac80;display:grid;place-items:center}.record-type strong,.record-type small{display:block}.record-type small{font-size:10px;color:#9ba9aa;margin-top:2px}.detail-meta{display:flex;align-items:center;gap:13px;color:#9ba8aa;font-size:11px;margin-bottom:18px;flex-wrap:wrap}.detail-media-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:18px}.detail-media-grid strong{display:block;font-size:12px;margin-bottom:8px;color:#57696b}.detail-media-grid img,.detail-media-grid video{display:block;width:100%;height:220px;object-fit:contain;background:#f2f5f4;border-radius:7px}@media(max-width:600px){.records-toolbar{display:block}.records-toolbar h2{margin-bottom:14px}.detail-media-grid{grid-template-columns:1fr}}
.warn-text{color:#d86654}
</style>
