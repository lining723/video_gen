<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTimeline } from '@/api/projects'
import {
  generateSubjects, generateShotSubject, uploadShotSubject,
  startRenders, retryRender, getRenderStatus, composeVideo,
  updateFinalVideoSettings, uploadFinalVideoBgm, clearFinalVideoBgm,
  lockSubject, unlockSubject, updateSubjectFeature,
  regenerateSubject, getSubjectVersions, rollbackSubjectVersion,
} from '@/api/render'
import { getKeyframes, generateKeyframes, retryKeyframe, generateCompositeGrid, type KeyframeGrid, type CompositeGrid } from '@/api/keyframes'
import { mediaUrl } from '@/api/http'
import type { Timeline, RenderTask, Subject } from '@/types'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const projectId = route.params.projectId as string

const data = ref<Timeline | null>(null)
const composeError = ref('')
const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)
const keyframeGrids = reactive<Record<string, KeyframeGrid | null>>({})
const compositeGrids = reactive<Record<string, CompositeGrid | null>>({})

// Compose settings
const enableSubtitles = ref(true)
const enableBgm = ref(false)
const enableVoiceover = ref(false)
const enableTransitions = ref(false)

const latestTasks = computed(() => {
  const map = new Map<string, RenderTask>()
  for (const t of data.value?.render_tasks || []) {
    map.set(t.shot_id, t)
  }
  return Array.from(map.values())
})

const composeReady = computed(() => {
  const shots = data.value?.storyboard || []
  const blockers: string[] = []
  const tasks = latestTasks.value
  const taskMap = new Map(tasks.map((t) => [t.shot_id, t]))

  for (const shot of shots) {
    const task = taskMap.get(shot.id)
    if (!task) {
      blockers.push(`镜头 ${shot.sequence} 尚未创建渲染任务`)
    } else if (task.status !== 'succeeded') {
      blockers.push(`镜头 ${shot.sequence} 仍处于${task.status}`)
    } else if (!String(task.render_path || '').toLowerCase().endsWith('.mp4')) {
      blockers.push(`镜头 ${shot.sequence} 还没有可播放的视频产物`)
    }
  }
  return { ready: shots.length > 0 && blockers.length === 0, blockers }
})

const latestGlobalSubjects = computed(() => {
  const map = new Map<string, Subject>()
  for (const s of data.value?.subjects || []) {
    if (!s.shot_id) map.set(s.name, s)
  }
  return Array.from(map.values())
})

function renderStatusText(task: RenderTask): string {
  if (task.progress_message) return task.progress_message
  if (task.status === 'missing') return '未创建任务'
  if (task.status === 'running' && task.force_refresh) return '强制重生成中'
  if (task.status === 'running') return '渲染中'
  if (task.status === 'succeeded' && task.force_refresh) return '已替换旧产物'
  if (task.status === 'succeeded' && task.cache_hit) return '已完成（缓存命中）'
  if (task.status === 'succeeded') return '已完成'
  return task.status || '未知状态'
}

function getShotSubject(shotId: string): Subject | undefined {
  return (data.value?.subjects || []).find((s) => s.shot_id === shotId)
}

function getGridColumns(gridType: string): string {
  const cols = parseInt(gridType.split('x')[0], 10)
  return `repeat(${cols}, 1fr)`
}

async function load() {
  const result = await getTimeline(projectId)
  data.value = result.item
  enableSubtitles.value = !!result.item.project.compose_enable_subtitles
  enableBgm.value = !!result.item.project.compose_enable_bgm
  enableVoiceover.value = !!result.item.project.compose_enable_voiceover
  enableTransitions.value = !!result.item.project.compose_enable_transitions
  // 加载关键帧数据
  await loadKeyframes()
}

async function loadKeyframes() {
  for (const shot of data.value?.storyboard || []) {
    try {
      const grid = await getKeyframes(projectId, shot.id)
      keyframeGrids[shot.id] = grid
      // 自动加载 composite 网格图
      if (grid.composite_image_url) {
        compositeGrids[shot.id] = {
          grid_type: grid.composite_grid_type || grid.grid_type,
          frame_count: grid.frame_count,
          image_url: grid.composite_image_url,
        }
      }
    } catch {
      keyframeGrids[shot.id] = null
    }
  }
}

async function handleGenerateKeyframes(shotId: string) {
  try {
    const result = await generateKeyframes(projectId, shotId)
    keyframeGrids[shotId] = result.item
    ElMessage.success('关键帧生成成功')
  } catch (e: any) {
    ElMessage.error(e.message || '关键帧生成失败')
  }
}

async function handleGenerateCompositeGrid(shotId: string) {
  try {
    const result = await generateCompositeGrid(projectId, shotId)
    compositeGrids[shotId] = result
    ElMessage.success('网格图生成成功（1次API调用）')
  } catch (e: any) {
    ElMessage.error(e.message || '网格图生成失败')
  }
}

async function handleRetryKeyframe(shotId: string, position: number) {
  try {
    await retryKeyframe(projectId, shotId, position)
    ElMessage.success('正在重新生成关键帧...')
    setTimeout(() => loadKeyframes(), 2000)
  } catch {
    ElMessage.error('重试失败')
  }
}

async function handleGenerateSubjects() {
  await generateSubjects(projectId)
  await load()
  ElMessage.success('主体图及关键帧已生成')
}

async function handleStartRenders(force = false) {
  await startRenders(projectId, { force })
  startPolling()
}

async function handleComposeVideo() {
  try {
    await composeVideo(projectId)
    composeError.value = ''
    setTimeout(() => router.push(`/projects/${projectId}/final-video`), 400)
  } catch (e: any) {
    composeError.value = e.payload?.details?.blockers?.map((b: any) => `镜头 ${b.sequence} ${b.reason}`).join('；') || e.message
    ElMessage.error(composeError.value)
  }
}

async function handleRetryRender(shotId: string, force = false) {
  await retryRender(projectId, shotId, { force })
  startPolling()
}

async function handleQueryStatus(shotId: string) {
  await getRenderStatus(projectId, shotId)
  await load()
  ElMessage.success('已获取最新进度')
}

async function toggleComposeSetting(key: string, value: boolean) {
  await updateFinalVideoSettings(projectId, { [key]: value })
  await load()
}

async function handleUploadBgm(file: File) {
  const reader = new FileReader()
  reader.onload = async () => {
    const dataUrl = reader.result as string
    const parts = dataUrl.split(',', 2)
    await uploadFinalVideoBgm(projectId, {
      filename: file.name,
      content_type: file.type,
      data_base64: parts[1],
    })
    await load()
    ElMessage.success('BGM 已上传')
  }
  reader.readAsDataURL(file)
}

async function handleClearBgm() {
  await clearFinalVideoBgm(projectId)
  await load()
  ElMessage.success('BGM 已清除')
}

async function handleUploadShotSubject(shotId: string, file: File) {
  const reader = new FileReader()
  reader.onload = async () => {
    const dataUrl = reader.result as string
    const parts = dataUrl.split(',', 2)
    await uploadShotSubject(projectId, shotId, {
      filename: file.name,
      content_type: file.type,
      data_base64: parts[1],
    })
    await load()
    ElMessage.success('镜头主体图已上传')
  }
  reader.readAsDataURL(file)
}

function startPolling() {
  if (pollTimer.value) return
  pollTimer.value = setInterval(async () => {
    const hasRunning = latestTasks.value.some((t) => t.status === 'running')
    if (!hasRunning && data.value) {
      stopPolling()
      return
    }
    await load()
  }, 3000)
}

function stopPolling() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

onMounted(async () => {
  await load()
  if (latestTasks.value.some((t) => t.status === 'running')) {
    startPolling()
  }
})

onUnmounted(stopPolling)
</script>

<template>
  <div v-if="data">
    <!-- Control console -->
    <el-card shadow="hover">
      <template #header>
        <h3>渲染控制台</h3>
        <p class="muted">把高频动作放在一处，减少在资产列表和任务列表之间来回找按钮。</p>
      </template>

      <div v-if="composeError" class="notice warn" style="margin-bottom: 14px">{{ composeError }}</div>
      <div v-if="!composeReady.ready" class="notice info" style="margin-bottom: 14px">
        当前还不能合成成片：{{ composeReady.blockers.join('；') }}
      </div>

      <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 18px">
        <el-button @click="handleGenerateSubjects">生成主体图</el-button>
        <el-button type="primary" @click="handleStartRenders(false)">开始渲染</el-button>
        <el-button type="danger" @click="handleStartRenders(true)">全部跳过缓存重渲染</el-button>
        <el-button type="success" :disabled="!composeReady.ready" @click="handleComposeVideo">合成成片</el-button>
      </div>

      <!-- Compose settings -->
      <el-card shadow="never" style="background: rgba(255,255,255,0.42)">
        <template #header>
          <h4 style="margin:0">成片设置</h4>
        </template>
        <el-row :gutter="16">
          <el-col :span="6">
            <el-checkbox
              :model-value="enableSubtitles"
              @change="(v: boolean) => toggleComposeSetting('compose_enable_subtitles', v)"
              border
            >字幕烧录</el-checkbox>
          </el-col>
          <el-col :span="6">
            <el-checkbox
              :model-value="enableVoiceover"
              @change="(v: boolean) => toggleComposeSetting('compose_enable_voiceover', v)"
              border
            >旁白音轨</el-checkbox>
          </el-col>
          <el-col :span="6">
            <el-checkbox
              :model-value="enableBgm"
              @change="(v: boolean) => toggleComposeSetting('compose_enable_bgm', v)"
              border
            >背景音乐</el-checkbox>
          </el-col>
          <el-col :span="6">
            <el-checkbox
              :model-value="enableTransitions"
              @change="(v: boolean) => toggleComposeSetting('compose_enable_transitions', v)"
              border
            >简单转场</el-checkbox>
          </el-col>
        </el-row>
        <div style="margin-top: 14px; display: flex; align-items: center; justify-content: space-between">
          <div>
            <strong>自定义 BGM</strong>
            <p class="muted">{{ data.project.final_bgm_path || '当前未上传，默认使用系统内置音乐床' }}</p>
          </div>
          <div style="display: flex; gap: 8px">
            <label>
              <el-button size="small" tag="span">上传 BGM</el-button>
              <input type="file" accept="audio/*" hidden @change="(e: any) => { const f = e.target.files?.[0]; if (f) handleUploadBgm(f); e.target.value = '' }" />
            </label>
            <el-button size="small" :disabled="!data.project.final_bgm_path" @click="handleClearBgm">清除 BGM</el-button>
          </div>
        </div>
      </el-card>

      <!-- Stats -->
      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="4" v-for="stat in [
          { label: '全局主体资产', value: latestGlobalSubjects.length },
          { label: '最新渲染任务', value: latestTasks.length },
          { label: '渲染中', value: latestTasks.filter(t => t.status === 'running').length },
          { label: '已完成', value: latestTasks.filter(t => t.status === 'succeeded').length },
        ]" :key="stat.label">
          <div class="stat-block">
            <strong>{{ stat.value }}</strong>
            <span>{{ stat.label }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- Subject assets + Render tasks + Keyframes -->
    <el-row :gutter="18">
      <!-- Subjects -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <h3>主体资产</h3>
            <p class="muted">每个镜头都能上传自己的主体图；未上传时，渲染会继续沿用全局主体资产。</p>
          </template>

          <div v-for="shot in (data.storyboard || [])" :key="shot.id" class="subject-shot-card">
            <div class="subject-shot-head">
              <h4>镜头 {{ shot.sequence }}</h4>
              <el-tag size="small" type="info">{{ (shot.subject_refs || []).join('、') || '主角' }}</el-tag>
            </div>
            <div style="display: flex; gap: 6px; flex-wrap: wrap">
              <el-button size="small" @click="generateShotSubject(projectId, shot.id, { mode: 'generate' }).then(load)">
                直接生成
              </el-button>
              <label>
                <el-button size="small" tag="span">上传图片</el-button>
                <input type="file" accept="image/*" hidden @change="(e: any) => { const f = e.target.files?.[0]; if (f) handleUploadShotSubject(shot.id, f) }" />
              </label>
            </div>
            <div v-if="getShotSubject(shot.id)" class="notice info" style="margin-top: 8px">
              已上传镜头专属主体图
            </div>
            <div v-else class="notice info" style="margin-top: 8px">
              未上传专属图片，将使用全局主体图
            </div>
          </div>

          <!-- Global subjects -->
          <div style="margin-top: 18px; padding-top: 18px; border-top: 1px solid rgba(29,26,23,0.08)">
            <h4 style="margin: 0 0 12px">全局主体库</h4>
            <div v-for="subject in latestGlobalSubjects" :key="subject.id" class="subject-item">
              <div class="subject-item-head">
                <div>
                  <strong>{{ subject.name }}</strong>
                  <span class="version-badge">v{{ subject.image_version }}</span>
                </div>
                <div style="display: flex; gap: 6px">
                  <el-tag v-if="subject.is_locked" size="small" type="warning">已锁定</el-tag>
                  <el-tag v-if="subject.generation_warning" size="small" type="danger">生成告警</el-tag>
                </div>
              </div>
              <div v-if="subject.feature_description" style="margin: 8px 0">
                <el-input v-model="subject.feature_description" readonly size="small" />
              </div>
              <div style="display: flex; gap: 6px; margin-top: 8px">
                <el-button v-if="!subject.is_locked" size="small" type="warning" @click="lockSubject(projectId, subject.id).then(load)">锁定特征</el-button>
                <el-button v-else size="small" @click="unlockSubject(projectId, subject.id).then(load)">解锁</el-button>
                <el-button size="small" :disabled="!!subject.is_locked" @click="regenerateSubject(projectId, subject.id).then(load)">重新生成</el-button>
              </div>
              <div v-if="subject.image_path" class="media-preview" style="margin-top: 10px">
                <img :src="mediaUrl(subject.image_path)" :alt="subject.name" />
              </div>
            </div>
            <div v-if="latestGlobalSubjects.length === 0" class="muted">暂无全局主体图</div>
          </div>
        </el-card>
      </el-col>

      <!-- Render tasks + Keyframes -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <h3>渲染任务</h3>
            <p class="muted">每个镜头只保留最新状态，重试与预览直接贴近结果。</p>
          </template>

          <div v-for="shot in (data.storyboard || [])" :key="shot.id">
            <div class="task-item">
              <div class="task-item-head">
                <div>
                  <h4>镜头 {{ shot.sequence }}</h4>
                </div>
                <el-tag
                  :type="(
                    () => { const t = latestTasks.find(rt => rt.shot_id === shot.id);
                    return t?.status === 'succeeded' ? 'success' : t?.status === 'failed' ? 'danger' : 'info'; }
                  )()"
                  size="small"
                >
                  {{ renderStatusText(latestTasks.find(t => t.shot_id === shot.id) || { shot_id: shot.id, status: 'missing', render_path: '', force_refresh: false, error_message: '', progress_message: '', cache_hit: false } as RenderTask) }}
                </el-tag>
              </div>
              <div style="display: flex; gap: 6px; margin-top: 10px">
                <el-button size="small" @click="handleQueryStatus(shot.id)">查询进度</el-button>
                <el-button size="small" @click="handleRetryRender(shot.id)">重新生成</el-button>
                <el-button size="small" type="danger" @click="handleRetryRender(shot.id, true)">跳过缓存重渲染</el-button>
              </div>

              <!-- Keyframe grid -->
              <div style="margin-top: 14px; padding-top: 14px; border-top: 1px solid rgba(29,26,23,0.08)">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px">
                  <span class="muted" style="font-weight: 600">
                    关键帧
                    <template v-if="keyframeGrids[shot.id]">
                      {{ keyframeGrids[shot.id]!.grid_type }} · {{ keyframeGrids[shot.id]!.frame_count }}帧
                    </template>
                  </span>
                  <el-button size="small" @click="handleGenerateKeyframes(shot.id)">
                    {{ keyframeGrids[shot.id] ? '重新生成关键帧' : '生成关键帧' }}
                  </el-button>
                  <el-button size="small" type="success" @click="handleGenerateCompositeGrid(shot.id)">
                    网格图 (composite)
                  </el-button>
                </div>
                <div v-if="keyframeGrids[shot.id]" class="keyframe-grid" :style="{ gridTemplateColumns: getGridColumns(keyframeGrids[shot.id]!.grid_type) }">
                  <div
                    v-for="frame in keyframeGrids[shot.id]!.frames"
                    :key="frame.position"
                    class="keyframe-cell"
                    :class="{ 'frame-succeeded': frame.status === 'succeeded', 'frame-failed': frame.status === 'failed', 'frame-pending': frame.status !== 'succeeded' && frame.status !== 'failed' }"
                  >
                    <img v-if="frame.image_url && frame.status === 'succeeded'" :src="frame.image_url" :alt="`帧 ${frame.position + 1}`" />
                    <div v-else-if="frame.status === 'failed'" class="frame-error">
                      <span>失败</span>
                      <el-button size="small" type="danger" @click="handleRetryKeyframe(shot.id, frame.position)">重试</el-button>
                    </div>
                    <div v-else class="frame-loading">
                      <span>{{ frame.status === 'generating' ? '生成中...' : '等待中' }}</span>
                    </div>
                    <span class="frame-label">{{ Math.round(frame.time_ratio * 100) }}%</span>
                  </div>
                </div>
                <!-- Composite grid -->
                <div v-if="compositeGrids[shot.id]" style="margin-top: 14px; padding-top: 14px; border-top: 1px solid rgba(29,26,23,0.08)">
                  <span class="muted" style="font-weight: 600">网格图 {{ compositeGrids[shot.id]!.grid_type }} · {{ compositeGrids[shot.id]!.frame_count }}帧 (1次API)</span>
                  <div class="media-preview" style="margin-top: 8px">
                    <img :src="compositeGrids[shot.id]!.image_url" alt="Composite grid" style="width: 100%; border-radius: 8px" />
                  </div>
                </div>
                <div v-else-if="!keyframeGrids[shot.id]" class="muted">尚未生成关键帧</div>
              </div>
            </div>
          </div>
          <div v-if="!data.storyboard?.length" class="muted">暂无渲染任务</div>
        </el-card>
      </el-col>
    </el-row>

    <div class="action-row">
      <el-button @click="router.push(`/projects/${projectId}/storyboard`)">返回分镜编辑</el-button>
    </div>
  </div>
</template>

<style scoped>
.muted { color: var(--text-muted); line-height: 1.6; font-size: 0.88rem; margin-top: 4px; }
.stat-block {
  padding: 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(29, 26, 23, 0.08);
  text-align: center;
}
.stat-block strong { display: block; font-size: 1.4rem; }
.stat-block span { display: block; margin-top: 4px; color: var(--text-muted); font-size: 0.8rem; }
.action-row { margin-top: 8px; }

.subject-shot-card {
  padding: 14px 0;
  border-top: 1px solid rgba(29,26,23,0.08);
}
.subject-shot-card:first-child { border-top: 0; padding-top: 0; }
.subject-shot-head { display: flex; justify-content: space-between; align-items: center; }
.subject-shot-head h4 { margin: 0; }

.subject-item {
  padding: 12px 0;
  border-top: 1px solid rgba(29,26,23,0.08);
}
.subject-item:first-child { border-top: 0; padding-top: 0; }
.subject-item-head { display: flex; justify-content: space-between; align-items: center; }
.version-badge { font-size: 0.8rem; color: var(--text-muted); margin-left: 8px; }

.task-item {
  padding: 14px 0;
  border-top: 1px solid rgba(29,26,23,0.08);
}
.task-item:first-child { border-top: 0; padding-top: 0; }
.task-item-head { display: flex; justify-content: space-between; align-items: center; }
.task-item-head h4 { margin: 0; font-size: 0.95rem; }

/* Keyframe grid styles */
.keyframe-grid {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}
.keyframe-cell {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(29, 26, 23, 0.1);
}
.keyframe-cell img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.frame-label {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 0.7rem;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 1px 5px;
  border-radius: 4px;
}
.frame-succeeded { border-color: rgba(47, 107, 83, 0.3); }
.frame-failed { border-color: rgba(175, 90, 42, 0.3); }
.frame-pending { border-color: rgba(29, 26, 23, 0.08); }
.frame-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 100%;
  color: var(--warning);
  font-size: 0.8rem;
}
.frame-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: 0.78rem;
}
</style>
