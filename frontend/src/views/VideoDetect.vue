<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { UploadFilled, VideoCamera } from '@element-plus/icons-vue'
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
  result.value = null; error.value = ''
}
function clear() {
  if (preview.value) URL.revokeObjectURL(preview.value)
  file.value = null; preview.value = ''; result.value = null; error.value = ''
}
async function detect() {
  if (!file.value) return
  busy.value = true; error.value = ''; result.value = null
  try { result.value = await api.detect('video', file.value, confidence.value) }
  catch (exc) { error.value = exc.message }
  finally { busy.value = false }
}
onBeforeUnmount(clear)
</script>

<template>
  <div>
    <div class="page-heading"><div><div class="eyebrow">HELMET / VIDEO</div><h1>安全帽视频检测</h1><p>逐帧标注佩戴状态，汇总未佩戴目标出现的帧数。</p></div><span class="pill">支持 MP4 / AVI / MOV / MKV</span></div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <section class="panel upload-panel"><el-upload class="upload-drop" drag action="#" accept=".mp4,.avi,.mov,.mkv" :auto-upload="false" :show-file-list="false" :on-change="choose"><div class="upload-icon"><el-icon><UploadFilled /></el-icon></div><div class="upload-title">拖拽视频到这里，或点击选择文件</div><div class="upload-hint">较长的视频会需要更多处理时间，请保持页面打开</div></el-upload><div v-if="file" class="selected-file"><span>已选择：{{ file.name }}</span><el-button text size="small" @click="clear">移除</el-button></div><div class="control-row"><div class="confidence-control"><label>置信度阈值</label><el-slider v-model="confidence" :min="0.05" :max="1" :step="0.05" /><span class="confidence-value">{{ Math.round(confidence * 100) }}%</span></div><el-button type="primary" class="primary-action" :loading="busy" :disabled="!file" @click="detect"><el-icon v-if="!busy"><VideoCamera /></el-icon> {{ busy ? '正在逐帧检测...' : '开始视频检测' }}</el-button></div></section>
    <div v-if="preview || result" class="result-grid"><section class="panel result-card"><h3>原始视频 <span>ORIGINAL</span></h3><video v-if="preview" :src="preview" class="video-preview" controls preload="metadata"></video></section><section class="panel result-card"><h3>结果视频 <span>DETECTION RESULT</span></h3><video v-if="result" :src="result.result_url" class="video-preview" controls preload="metadata"></video><div v-else class="video-placeholder">完成检测后在此播放结果</div></section></div>
    <section v-if="result" class="panel object-list"><h2 class="section-title">本次检测</h2><div v-if="result.status === 'violation'" class="error-banner">检测到未佩戴安全帽的目标，请查看结果视频确认。</div><div v-else-if="result.status === 'unknown'" class="notice">未检出安全帽相关目标，不能据此判断现场全部人员已佩戴。</div><div class="summary-strip"><div><strong>{{ result.frames }}</strong>处理帧数</div><div><strong>{{ result.helmet_count }}</strong>已佩戴框次数</div><div><strong>{{ result.no_helmet_count }}</strong>未佩戴框次数</div><div><strong>{{ result.violation_frames }}</strong>出现未佩戴的帧数</div></div><p class="helper-text">同一目标跨帧会重复计入检测框；“出现未佩戴的帧数”也不等于未佩戴人数。处理耗时 {{ (result.elapsed_ms / 1000).toFixed(1) }} 秒。<a :href="result.result_url" download>下载结果视频</a> · <a :href="result.original_url" download>下载原始视频</a></p></section>
  </div>
</template>

<style scoped>.selected-file{display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding:9px 12px;background:#f3faf6;border-radius:7px;color:#478b70;font-size:11px;word-break:break-all}.video-placeholder{height:240px;background:#f4f7f6;border-radius:8px;display:grid;place-items:center;color:#b0bcbb;font-size:12px}</style>
