<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { UploadFilled, MagicStick, Refresh } from '@element-plus/icons-vue'
import { api } from '../api/index.js'

const file = ref(null)
const preview = ref('')
const confidence = ref(0.25)
const result = ref(null)
const busy = ref(false)
const error = ref('')

function choose(uploadFile) {
  if (preview.value) URL.revokeObjectURL(preview.value)
  file.value = uploadFile.raw
  preview.value = URL.createObjectURL(uploadFile.raw)
  result.value = null
  error.value = ''
}
function clear() {
  if (preview.value) URL.revokeObjectURL(preview.value)
  file.value = null; preview.value = ''; result.value = null; error.value = ''
}
async function detect() {
  if (!file.value) return
  busy.value = true; error.value = ''; result.value = null
  try { result.value = await api.detect('image', file.value, confidence.value) }
  catch (exc) { error.value = exc.message }
  finally { busy.value = false }
}
onBeforeUnmount(clear)
</script>

<template>
  <div>
    <div class="page-heading"><div><div class="eyebrow">HELMET / IMAGE</div><h1>安全帽图片检测</h1><p>识别已佩戴与未佩戴安全帽的目标位置。</p></div><span class="pill">支持 JPG / PNG / WEBP</span></div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <section class="panel upload-panel">
      <el-upload class="upload-drop" drag action="#" accept=".jpg,.jpeg,.png,.webp" :auto-upload="false" :show-file-list="false" :on-change="choose">
        <div class="upload-icon"><el-icon><UploadFilled /></el-icon></div><div class="upload-title">拖拽图片到这里，或点击选择文件</div><div class="upload-hint">选择后可调整置信度，再开始识别</div>
      </el-upload>
      <div v-if="file" class="selected-file"><span>已选择：{{ file.name }}</span><el-button text size="small" @click="clear">移除</el-button></div>
      <div class="control-row"><div class="confidence-control"><label>置信度阈值</label><el-slider v-model="confidence" :min="0.05" :max="1" :step="0.05" /><span class="confidence-value">{{ Math.round(confidence * 100) }}%</span></div><div><el-button v-if="result" class="secondary-action" @click="clear"><el-icon><Refresh /></el-icon> 重新选择</el-button><el-button type="primary" class="primary-action" :loading="busy" :disabled="!file" @click="detect"><el-icon v-if="!busy"><MagicStick /></el-icon> {{ busy ? '正在识别...' : '开始检测' }}</el-button></div></div>
    </section>
    <div v-if="preview || result" class="result-grid"><section class="panel result-card"><h3>原始图片 <span>ORIGINAL</span></h3><img v-if="preview" :src="preview" class="preview-media" alt="上传的原始图片" /></section><section class="panel result-card"><h3>检测结果 <span>DETECTION RESULT</span></h3><img v-if="result" :src="result.result_url" class="preview-media" alt="标注检测框的结果图片" /><div v-else class="preview-media preview-placeholder">等待检测结果</div></section></div>
    <section v-if="result" class="panel object-list"><h2 class="section-title">检测结果</h2><div v-if="result.status === 'violation'" class="error-banner">检测到未佩戴安全帽的目标，请复核图片。</div><div v-else-if="result.status === 'unknown'" class="notice">未检出安全帽相关目标，不能据此判断现场全部人员已佩戴。</div><div class="summary-strip"><div><strong>{{ result.helmet_count }}</strong>已佩戴目标</div><div><strong>{{ result.no_helmet_count }}</strong>未佩戴目标</div><div><strong>{{ result.elapsed_ms }} ms</strong>处理耗时</div></div><div class="table-wrap" style="margin-top:20px"><el-table :data="result.objects" empty-text="未发现安全帽相关目标"><el-table-column label="佩戴状态" min-width="120"><template #default="scope"><span class="tag-soft">{{ scope.row.wearing_status === 'violation' ? '未佩戴' : '已佩戴' }}</span></template></el-table-column><el-table-column label="置信度" min-width="100"><template #default="scope">{{ (scope.row.confidence * 100).toFixed(1) }}%</template></el-table-column><el-table-column label="位置 (x1, y1, x2, y2)" min-width="210"><template #default="scope">{{ [scope.row.x1, scope.row.y1, scope.row.x2, scope.row.y2].map(Math.round).join(', ') }}</template></el-table-column></el-table></div><p class="helper-text">统计的是检测框，不代表去重后的工人人数。检测结果请结合原图复核。</p></section>
  </div>
</template>

<style scoped>.selected-file{display:flex;align-items:center;justify-content:space-between;margin-top:12px;padding:9px 12px;background:#f3faf6;border-radius:7px;color:#478b70;font-size:11px;word-break:break-all}.preview-placeholder{display:grid;place-items:center;color:#b1bcbd;font-size:12px}</style>
