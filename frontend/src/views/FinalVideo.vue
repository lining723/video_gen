<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTimeline } from '@/api/projects'
import { getFinalVideo } from '@/api/render'
import { mediaUrl } from '@/api/http'
import { formatProjectLabel } from '@/utils/project'
import type { FinalVideo, Timeline } from '@/types'

const route = useRoute()
const router = useRouter()
const projectId = route.params.projectId as string

const data = ref<Timeline | null>(null)
const finalVideo = ref<FinalVideo | null>(null)
const pending = ref(false)
const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)

function featureLabel(key: string): string {
  return { subtitles: '字幕烧录', background_music: '背景音乐', voiceover_mix: '旁白音轨', fade_transition: '简单转场' }[key] || key
}

function bgmSourceLabel(source: string): string {
  return { custom: '自定义 BGM', generated: '系统内置 BGM', disabled: '未启用 BGM' }[source || ''] || '未知来源'
}

async function load() {
  const timelineResult = await getTimeline(projectId)
  data.value = timelineResult.item
  try {
    const result = await getFinalVideo(projectId)
    finalVideo.value = result.item
    pending.value = false
  } catch (e: any) {
    if (e.status === 404) {
      finalVideo.value = null
      pending.value = timelineResult.item.project.current_stage === 'video_rendering'
    } else {
      throw e
    }
  }
}

onMounted(async () => {
  await load()
  if (!finalVideo.value && pending.value) {
    pollTimer.value = setInterval(load, 1500)
  }
})

onUnmounted(() => {
  if (pollTimer.value) clearInterval(pollTimer.value)
})
</script>

<template>
  <div v-if="data">
    <!-- Pending -->
    <el-card v-if="!finalVideo && pending" shadow="hover">
      <div class="empty-state">
        <h3>正在合成最终成片</h3>
        <p>成片页会自动刷新，当前会依次完成字幕烧录、旁白混入、背景音乐混音和简单转场，再输出最终视频。</p>
      </div>
    </el-card>

    <!-- Not generated -->
    <el-card v-else-if="!finalVideo" shadow="hover">
      <div class="empty-state">
        <h3>成片还没有生成</h3>
        <p>先在渲染控制页完成镜头渲染，再触发成片合成，这里会直接展示最终版本。</p>
      </div>
    </el-card>

    <!-- Final video display -->
    <template v-else>
      <el-card shadow="hover" class="video-stage">
        <template #header>
          <div class="section-head">
            <div>
              <h2 class="card-title">最终成片 V{{ finalVideo.version }}</h2>
            </div>
            <div style="display: flex; gap: 6px">
              <el-tag>{{ finalVideo.duration }}s</el-tag>
              <el-tag type="info">{{ finalVideo.resolution || 'unknown' }}</el-tag>
              <el-tag type="warning">BGM: {{ bgmSourceLabel(finalVideo.bgm_source) }}</el-tag>
            </div>
          </div>
        </template>

        <div style="margin-bottom: 14px">
          <strong>本次启用</strong>
          <div style="display: flex; gap: 6px; margin-top: 8px">
            <el-tag v-for="feat in finalVideo.features" :key="feat" size="small">{{ featureLabel(feat) }}</el-tag>
            <el-tag v-if="!finalVideo.features?.length" size="small" type="info">未启用额外处理</el-tag>
          </div>
        </div>

        <el-button type="primary" tag="a" :href="mediaUrl(finalVideo.storage_path)" target="_blank" style="margin-bottom: 14px">
          下载 / 查看成片
        </el-button>

        <div class="media-preview">
          <video :src="mediaUrl(finalVideo.storage_path)" controls preload="metadata"></video>
        </div>
      </el-card>
    </template>

    <div class="action-row">
      <el-button @click="router.push(`/projects/${projectId}/renders`)">回到渲染控制</el-button>
    </div>
  </div>
</template>

<style scoped>
.section-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.card-title { font-size: 1.3rem; margin: 0; }
.empty-state { text-align: center; padding: 40px 20px; }
.empty-state h3 { margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); }
.action-row { margin-top: 8px; }
.video-stage :deep(.el-card__body) {  }
.media-preview video {
  width: 100%;
  max-height: 520px;
  border-radius: 16px;
  background: rgba(18, 15, 12, 0.94);
}
</style>
