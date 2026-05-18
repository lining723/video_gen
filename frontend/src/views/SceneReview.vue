<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTimeline } from '@/api/projects'
import { generateScene, reviewScene, updateSceneSettings } from '@/api/sceneDesign'
import type { Timeline } from '@/types'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const projectId = route.params.projectId as string

const data = ref<Timeline | null>(null)
const sceneCount = ref(3)
const comment = ref('')
const generating = ref(false)
const reviewing = ref(false)

async function load() {
  const result = await getTimeline(projectId)
  data.value = result.item
  sceneCount.value = result.item.project.scene_count || (result.item.scene?.scene_list?.length || 3)
}

async function handleGenerate() {
  generating.value = true
  try {
    await generateScene(projectId, { scene_count: sceneCount.value })
    await load()
    ElMessage.success('场景设计已生成')
  } finally {
    generating.value = false
  }
}

async function handleReview(action: string) {
  reviewing.value = true
  try {
    await reviewScene(projectId, { action, comment: comment.value })
    if (action === 'approve') {
      router.push(`/projects/${projectId}/storyboard`)
    } else {
      await load()
      ElMessage.info(action === 'reject' ? '场景已驳回' : '正在重新生成')
    }
  } finally {
    reviewing.value = false
  }
}

async function saveSceneCount() {
  await updateSceneSettings(projectId, { scene_count: sceneCount.value })
  ElMessage.success(`场景数量已更新为 ${sceneCount.value}`)
}

onMounted(load)
</script>

<template>
  <div v-if="data">
    <!-- Scene count settings -->
    <el-card shadow="hover">
      <template #header>
        <div class="section-head">
          <div>
            <h3>场景数量</h3>
            <p class="muted">先确定这一版要拆成几段场景，重新生成时也会沿用这个数量。</p>
          </div>
          <el-tag>当前配置：{{ sceneCount }}</el-tag>
        </div>
      </template>
      <el-row :gutter="16" align="middle">
        <el-col :span="12">
          <el-form-item label="场景数量">
            <el-input-number v-model="sceneCount" :min="1" :max="12" />
            <div class="field-help">建议控制在 3-8 段，便于后续分镜与渲染节奏保持稳定。</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-button @click="saveSceneCount">保存数量</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Scene content -->
    <el-card v-if="data.scene" shadow="hover">
      <template #header>
        <div class="section-head">
          <div>
            <h2 class="card-title">场景设计 V{{ data.scene.version }}</h2>
            <p class="card-subtitle">{{ data.scene.scene_summary || '暂无场景摘要' }}</p>
          </div>
          <el-tag>场景数：{{ (data.scene.scene_list || []).length }}</el-tag>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="8" v-for="(item, index) in data.scene.scene_list" :key="index">
          <div class="scene-card">
            <h4>{{ item.title || `场景 ${index + 1}` }}</h4>
            <p>{{ item.description || '暂无描述' }}</p>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-else shadow="hover">
      <div class="empty-state">
        <h3>还没有场景设计</h3>
        <p>先生成一版整体场景，页面会在这里按段落列出每个场景的标题、说明。</p>
        <el-button type="primary" @click="handleGenerate" :loading="generating">生成场景设计</el-button>
      </div>
    </el-card>

    <!-- Review panel -->
    <el-card v-if="data.scene" shadow="hover">
      <template #header>
        <div class="section-head">
          <div>
            <h3>审核意见</h3>
            <p class="muted">只保留一个输入区和三个关键动作，让审核流更干净。</p>
          </div>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="16">
          <el-input
            v-model="comment"
            type="textarea"
            :rows="4"
            placeholder="例如：第二段场景节奏偏慢，通勤场景需要更明确。"
          />
          <div style="margin-top: 14px; display: flex; gap: 10px">
            <el-button type="primary" @click="handleReview('approve')" :loading="reviewing">通过并进入分镜</el-button>
            <el-button type="danger" @click="handleReview('reject')" :loading="reviewing">驳回</el-button>
            <el-button @click="handleReview('regenerate')" :loading="reviewing">重新生成</el-button>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="review-principles">
            <h4>审核原则</h4>
            <ul>
              <li>确认每一段场景都对创意需求有回应。</li>
              <li>检查场景顺序是否有明显断裂或重复。</li>
              <li>通过后会直接进入分镜页。</li>
            </ul>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <div class="action-row">
      <el-button @click="router.push(`/projects/${projectId}`)">回到项目总览</el-button>
    </div>
  </div>
</template>

<style scoped>
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.section-head h3, .section-head h2 {
  margin: 0;
}
.card-title {
  font-size: 1.3rem;
  margin: 0;
}
.card-subtitle {
  margin: 6px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}
.field-help {
  color: var(--text-muted);
  font-size: 0.82rem;
  margin-top: 4px;
}
.scene-card {
  padding: 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(29, 26, 23, 0.08);
  margin-bottom: 12px;
}
.scene-card h4 {
  margin: 0 0 8px;
}
.scene-card p {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.88rem;
  line-height: 1.7;
}
.empty-state {
  text-align: center;
  padding: 40px 20px;
}
.empty-state h3 { margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); margin-bottom: 16px; }
.review-principles {
  padding: 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(29, 26, 23, 0.08);
}
.review-principles h4 { margin: 0 0 10px; }
.review-principles ul { margin: 0; padding-left: 18px; color: var(--text-muted); line-height: 1.8; }
.action-row { margin-top: 8px; }
.muted { color: var(--text-muted); line-height: 1.6; }
</style>
