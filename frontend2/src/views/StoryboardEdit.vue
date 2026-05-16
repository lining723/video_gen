<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTimeline } from '@/api/projects'
import { generateStoryboard, reviewStoryboard, updateShot, regenerateShot, updateStoryboardSettings } from '@/api/storyboard'
import type { Timeline, Shot } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const projectId = route.params.projectId as string

const data = ref<Timeline | null>(null)
const styleInput = ref('')
const generating = ref(false)
const shotModalVisible = ref(false)
const editingShot = ref<Shot | null>(null)
const STYLE_PRESETS = ['电影感写实', '高级广告片', '温暖生活方式', '未来科技感', '纪录片纪实', '国潮质感']

async function load() {
  const result = await getTimeline(projectId)
  data.value = result.item
  styleInput.value = result.item.project.storyboard_style || ''
}

async function handleGenerate() {
  generating.value = true
  try {
    await generateStoryboard(projectId)
    await load()
    ElMessage.success('分镜已生成')
  } finally {
    generating.value = false
  }
}

async function handleReview(action: string) {
  try {
    await reviewStoryboard(projectId, { action, comment: action === 'reject' ? '请调整分镜' : '' })
    if (action === 'approve') {
      router.push(`/projects/${projectId}/renders`)
    } else {
      await load()
      ElMessage.warning('分镜已驳回，请继续调整')
    }
  } catch { /* ignore */ }
}

async function handleSaveStyle() {
  await updateStoryboardSettings(projectId, { storyboard_style: styleInput.value })
  await load()
  ElMessage.success(styleInput.value ? `统一风格已保存为"${styleInput.value}"` : '统一风格已清空')
}

async function setStylePreset(style: string) {
  styleInput.value = style
  await handleSaveStyle()
}

async function openShotModal(shot: Shot) {
  editingShot.value = { ...shot }
  shotModalVisible.value = true
}

async function saveShot() {
  if (!editingShot.value) return
  await updateShot(projectId, editingShot.value.id, {
    sequence: editingShot.value.sequence,
    duration: editingShot.value.duration,
    shot_type: editingShot.value.shot_type,
    camera_movement: editingShot.value.camera_movement,
    scene_time: editingShot.value.scene_time,
    background: editingShot.value.background,
    sound_effects: editingShot.value.sound_effects,
    action_direction: editingShot.value.action_direction,
    description: editingShot.value.description,
    subtitle_text: editingShot.value.subtitle_text,
    dubbing_text: editingShot.value.dubbing_text,
    voiceover_text: editingShot.value.voiceover_text,
    voiceover_tone: editingShot.value.voiceover_tone,
  })
  shotModalVisible.value = false
  await load()
  ElMessage.success('分镜已保存')
}

async function handleRegenerateShot(shotId: string) {
  await regenerateShot(projectId, shotId)
  await load()
  ElMessage.success('镜头已重新生成')
}

async function moveShot(shotId: string, direction: 'up' | 'down') {
  const shots = data.value?.storyboard || []
  const index = shots.findIndex((s) => s.id === shotId)
  if (index === -1) return
  const targetIndex = direction === 'up' ? index - 1 : index + 1
  if (targetIndex < 0 || targetIndex >= shots.length) return

  // Swap sequences
  const tmp = shots[index].sequence
  await updateShot(projectId, shots[index].id, { sequence: shots[targetIndex].sequence })
  await updateShot(projectId, shots[targetIndex].id, { sequence: tmp })
  await load()
}

onMounted(load)
</script>

<template>
  <div v-if="data">
    <!-- Style panel -->
    <el-card shadow="hover">
      <template #header>
        <div class="section-head">
          <div>
            <h3>统一镜头风格</h3>
            <p class="muted">先确定整支片子的风格，再生成分镜。后续渲染也会沿用。</p>
          </div>
          <el-tag>当前：{{ styleInput || '未设置' }}</el-tag>
        </div>
      </template>
      <el-form-item label="分镜统一风格">
        <el-input v-model="styleInput" placeholder="如：电影感写实、高级广告片、未来科技感" />
      </el-form-item>
      <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px">
        <el-button
          v-for="style in STYLE_PRESETS"
          :key="style"
          size="small"
          @click="setStylePreset(style)"
        >
          {{ style }}
        </el-button>
        <el-button size="small" type="primary" @click="handleSaveStyle">一键设置风格</el-button>
      </div>
      <p class="muted">设置完成后，所有镜头会按同一风格输出。</p>
    </el-card>

    <!-- Empty state -->
    <el-card v-if="!data.storyboard || data.storyboard.length === 0" shadow="hover">
      <div class="empty-state">
        <h3>还没有分镜</h3>
        <p>场景审核通过后，再生成镜头级内容。</p>
        <el-button type="primary" @click="handleGenerate" :loading="generating">生成分镜</el-button>
      </div>
    </el-card>

    <!-- Shot list -->
    <template v-else>
      <el-card shadow="hover">
        <template #header>
          <div class="section-head">
            <div>
              <h3>分镜审核</h3>
              <p class="muted">列表模式更适合审核和排序，点击查看详情进行编辑。</p>
            </div>
            <div style="display: flex; gap: 8px">
              <el-button type="primary" @click="handleReview('approve')">通过分镜并开始渲染</el-button>
              <el-button type="danger" @click="handleReview('reject')">驳回分镜</el-button>
            </div>
          </div>
        </template>

        <!-- Shot list items -->
        <div class="shot-list">
          <div v-for="(shot, index) in data.storyboard" :key="shot.id" class="shot-item">
            <div class="shot-order">
              <el-button size="small" :disabled="index === 0" @click="moveShot(shot.id, 'up')">↑</el-button>
              <span class="order-num">{{ shot.sequence }}</span>
              <el-button size="small" :disabled="index === data.storyboard.length - 1" @click="moveShot(shot.id, 'down')">↓</el-button>
            </div>
            <div class="shot-info">
              <div class="shot-info-head">
                <h4>镜头 {{ shot.sequence }}</h4>
                <div class="shot-tags">
                  <el-tag size="small">{{ shot.shot_type || '未填写' }}</el-tag>
                  <el-tag size="small" type="info">{{ shot.camera_movement || '未填写' }}</el-tag>
                  <el-tag size="small" type="warning">{{ shot.duration }}s</el-tag>
                </div>
              </div>
              <el-row :gutter="12" style="margin-top: 10px">
                <el-col :span="8">
                  <div class="shot-meta-card">
                    <strong>场景</strong>
                    <p>{{ (shot.background || shot.description || '暂无').slice(0, 60) }}</p>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="shot-meta-card">
                    <strong>字幕</strong>
                    <p>{{ (shot.subtitle_text || '暂无').slice(0, 60) }}</p>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="shot-meta-card">
                    <strong>配音</strong>
                    <p>{{ (shot.dubbing_text || '暂无').slice(0, 60) }}</p>
                  </div>
                </el-col>
              </el-row>
            </div>
            <div class="shot-actions">
              <el-button @click="openShotModal(shot)">查看详情</el-button>
              <el-button @click="handleRegenerateShot(shot.id)">重新生成</el-button>
            </div>
          </div>
        </div>
      </el-card>
    </template>

    <div class="action-row">
      <el-button @click="router.push(`/projects/${projectId}/scene`)">回看场景设计</el-button>
    </div>

    <!-- Shot detail dialog -->
    <el-dialog v-model="shotModalVisible" title="分镜详情" width="800px" destroy-on-close>
      <template v-if="editingShot">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="顺序">
              <el-input-number v-model="editingShot.sequence" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="时长(s)">
              <el-input-number v-model="editingShot.duration" :min="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="镜头类型">
              <el-input v-model="editingShot.shot_type" placeholder="全景/中景/特写" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="运镜方式">
              <el-input v-model="editingShot.camera_movement" placeholder="推进/摇镜/跟拍" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="场景时间">
              <el-input v-model="editingShot.scene_time" placeholder="清晨/黄昏/深夜" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="配音音色">
          <el-input v-model="editingShot.voiceover_tone" placeholder="温暖女声/沉稳男声" />
        </el-form-item>
        <el-form-item label="背景">
          <el-input v-model="editingShot.background" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="动作指导">
          <el-input v-model="editingShot.action_direction" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="镜头描述">
          <el-input v-model="editingShot.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="字幕">
          <el-input v-model="editingShot.subtitle_text" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="配音">
          <el-input v-model="editingShot.dubbing_text" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="旁白">
          <el-input v-model="editingShot.voiceover_text" type="textarea" :rows="2" />
        </el-form-item>
      </template>
      <template #footer>
        <el-button @click="shotModalVisible = false">关闭</el-button>
        <el-button @click="handleRegenerateShot(editingShot!.id)">重新生成</el-button>
        <el-button type="primary" @click="saveShot">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.section-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.section-head h3 { margin: 0; }
.muted { color: var(--text-muted); line-height: 1.6; }
.empty-state { text-align: center; padding: 40px 20px; }
.empty-state h3 { margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); margin-bottom: 16px; }

.shot-item {
  display: flex;
  gap: 16px;
  padding: 16px 0;
  border-top: 1px solid rgba(29, 26, 23, 0.08);
}
.shot-item:first-child { border-top: 0; padding-top: 0; }
.shot-order {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.order-num {
  font-weight: 600;
  color: var(--accent);
  min-width: 24px;
  text-align: center;
}
.shot-info { flex: 1; }
.shot-info-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.shot-info-head h4 { margin: 0; font-size: 1rem; }
.shot-tags { display: flex; gap: 6px; }
.shot-meta-card {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(29, 26, 23, 0.08);
}
.shot-meta-card strong { display: block; font-size: 0.82rem; margin-bottom: 4px; }
.shot-meta-card p { margin: 0; color: var(--text-muted); font-size: 0.84rem; line-height: 1.5; word-break: break-all; }
.shot-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 100px;
}
.action-row { margin-top: 8px; }
</style>
