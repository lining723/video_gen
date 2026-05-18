<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listProjects, createProject } from '@/api/projects'
import { formatProjectLabel } from '@/utils/project'
import type { Project } from '@/types'

const router = useRouter()

const projects = ref<Project[]>([])
const name = ref('新品发布视频')
const prompt = ref('为一款智能耳机生成 30 秒宣传视频，突出降噪、通勤、轻量感。')
const sceneCount = ref(3)
const creating = ref(false)

const activeCount = computed(() => projects.value.filter((p) => p.status !== 'completed').length)
const completedCount = computed(() => projects.value.filter((p) => p.status === 'completed').length)

import { computed } from 'vue'

async function load() {
  const data = await listProjects()
  projects.value = data.items || []
}

async function handleCreate() {
  if (!name.value.trim()) return
  creating.value = true
  try {
    const result = await createProject({
      name: name.value,
      prompt: prompt.value,
      scene_count: sceneCount.value,
    })
    router.push(`/projects/${result.item.id}/scene`)
  } finally {
    creating.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="project-landing">
    <!-- Create form -->
    <el-card class="create-card" shadow="hover">
      <template #header>
        <h2 class="card-title">新建视频项目</h2>
        <p class="card-subtitle">先定义片名与创意指令，系统会从场景设计开始逐步推进后续流程。</p>
      </template>
      <el-form label-position="top" @submit.prevent="handleCreate">
        <el-form-item label="项目名称">
          <el-input v-model="name" placeholder="例如：新品发布视频" />
          <div class="field-help">名称会出现在总览、阶段导航和成片页中。</div>
        </el-form-item>
        <el-form-item label="创意需求">
          <el-input v-model="prompt" type="textarea" :rows="5" placeholder="输入创意需求" />
          <div class="field-help">建议直接写清楚产品、氛围、卖点和时长，这样前面的场景与后面的分镜更稳定。</div>
        </el-form-item>
        <el-form-item label="场景数量">
          <el-input-number v-model="sceneCount" :min="1" :max="12" />
          <div class="field-help">用于控制场景设计输出的段落数量，后续在场景页也可以继续调整。</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" @click="handleCreate" :loading="creating" style="width: 100%">
            创建并进入场景审核
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Project list -->
    <div>
      <el-card shadow="hover">
        <template #header>
          <div class="section-header">
            <div>
              <h2 class="card-title">最近项目</h2>
              <p class="card-subtitle">所有项目统一展示名称、当前阶段和创意说明。</p>
            </div>
            <div class="stat-cards">
              <div class="stat-card">
                <span class="stat-value">{{ projects.length }}</span>
                <span class="stat-label">项目总数</span>
              </div>
              <div class="stat-card">
                <span class="stat-value">{{ activeCount }}</span>
                <span class="stat-label">进行中</span>
              </div>
              <div class="stat-card">
                <span class="stat-value">{{ completedCount }}</span>
                <span class="stat-label">已完成</span>
              </div>
            </div>
          </div>
        </template>

        <div v-if="projects.length === 0" class="empty-state">
          <h3>还没有项目</h3>
          <p>先从左侧创建一个视频需求，后面的场景设计、分镜和渲染都会按同一条流程展开。</p>
        </div>

        <div v-else class="project-list">
          <div v-for="item in projects" :key="item.id" class="project-item">
            <div class="project-item-main">
              <h3>{{ item.name || '未命名项目' }}</h3>
              <p>{{ item.prompt || '暂无项目描述' }}</p>
              <div class="project-tags">
                <el-tag
                  :type="item.status === 'completed' ? 'success' : item.status === 'failed' ? 'danger' : ''"
                  size="small"
                >
                  {{ formatProjectLabel(item.status) }}
                </el-tag>
                <el-tag size="small" type="info">{{ formatProjectLabel(item.current_stage) }}</el-tag>
              </div>
            </div>
            <el-button @click="router.push(`/projects/${item.id}`)">查看项目流转</el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.project-landing {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(300px, 0.9fr);
  gap: 18px;
}
.card-title {
  margin: 0;
  font-size: 1.3rem;
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
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.stat-cards {
  display: flex;
  gap: 10px;
}
.stat-card {
  min-width: 80px;
  text-align: center;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.56);
  border: 1px solid rgba(29, 26, 23, 0.08);
}
.stat-value {
  display: block;
  font-size: 1.3rem;
  font-weight: 600;
}
.stat-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
}
.empty-state {
  text-align: center;
  padding: 40px 20px;
}
.empty-state h3 {
  margin-bottom: 8px;
}
.empty-state p {
  color: var(--text-muted);
}
.project-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.project-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 0;
  border-top: 1px solid rgba(29, 26, 23, 0.08);
}
.project-item:first-child {
  border-top: 0;
  padding-top: 0;
}
.project-item-main {
  flex: 1;
}
.project-item-main h3 {
  margin: 0 0 6px;
  font-size: 1rem;
}
.project-item-main p {
  margin: 0 0 10px;
  color: var(--text-muted);
  font-size: 0.88rem;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.project-tags {
  display: flex;
  gap: 6px;
}

@media (max-width: 980px) {
  .project-landing {
    grid-template-columns: 1fr;
  }
}
</style>
