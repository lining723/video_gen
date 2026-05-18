<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTimeline, updateProjectSettings } from '@/api/projects'
import { listTextModels, listImageModels, listVideoModels } from '@/api/models'
import { formatProjectLabel } from '@/utils/project'
import type { Timeline, TextModel, ImageModel, VideoProvider } from '@/types'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const projectId = route.params.projectId as string

const data = ref<Timeline | null>(null)
const textModels = ref<TextModel[]>([])
const imageModels = ref<ImageModel[]>([])
const videoProviders = ref<VideoProvider[]>([])
const selectedTextModel = ref('')
const selectedImageModel = ref('')
const selectedVideoModel = ref('')
const saving = ref(false)

const quickLinks = [
  { label: '场景审核', desc: '确认画面结构、段落安排与整体叙事气质。', to: `/projects/${projectId}/scene` },
  { label: '分镜编辑', desc: '逐条细化镜头描述、字幕和配音文案。', to: `/projects/${projectId}/storyboard` },
  { label: '渲染控制', desc: '查看主体资产、发起渲染并处理缓存重试。', to: `/projects/${projectId}/renders` },
  { label: '最终成片', desc: '查看最终视频版本与下载入口。', to: `/projects/${projectId}/final-video` },
]

async function load() {
  const result = await getTimeline(projectId)
  data.value = result.item
  selectedTextModel.value = result.item.project.text_model || ''
  selectedImageModel.value = result.item.project.image_model || ''
  selectedVideoModel.value = result.item.project.video_model || ''

  const [text, image, video] = await Promise.all([
    listTextModels(),
    listImageModels(),
    listVideoModels(),
  ])
  textModels.value = text.models || []
  imageModels.value = image.models || []
  videoProviders.value = video.providers || []
}

async function saveModelSettings() {
  saving.value = true
  try {
    await updateProjectSettings(projectId, {
      text_model: selectedTextModel.value,
      image_model: selectedImageModel.value,
      video_model: selectedVideoModel.value,
    })
    ElMessage.success('项目模型设置已保存')
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-if="data">
    <!-- Overview -->
    <el-card shadow="hover">
      <template #header>
        <div class="overview-header">
          <div>
            <h2 class="card-title">{{ data.project.name }}</h2>
            <p class="card-subtitle">{{ data.project.prompt || '暂无项目描述' }}</p>
          </div>
          <div class="overview-tags">
            <el-tag>{{ formatProjectLabel(data.project.status) }}</el-tag>
            <el-tag type="info">{{ formatProjectLabel(data.project.current_stage) }}</el-tag>
          </div>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="6" v-for="stat in [
          { label: '场景版本', value: data.scene ? `V${data.scene.version}` : '--' },
          { label: '已生成镜头', value: (data.storyboard || []).length },
          { label: '主体资产', value: (data.subjects || []).length },
          { label: '渲染任务记录', value: (data.render_tasks || []).length },
        ]" :key="stat.label">
          <div class="stat-block">
            <strong>{{ stat.value }}</strong>
            <span>{{ stat.label }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- Model settings -->
    <el-card shadow="hover">
      <template #header>
        <h3>模型设置</h3>
        <p class="card-subtitle">项目级分别配置文本、图片、视频模型。后续场景、分镜、主体图和渲染都会按这里的配置执行。</p>
      </template>
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="文本模型">
            <el-select v-model="selectedTextModel" clearable placeholder="使用默认模型" style="width: 100%">
              <el-option
                v-for="m in textModels"
                :key="m.id"
                :label="`${m.name} (${m.provider_name})`"
                :value="m.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="图片模型">
            <el-select v-model="selectedImageModel" clearable placeholder="使用默认模型" style="width: 100%">
              <el-option
                v-for="m in imageModels"
                :key="m.id"
                :label="`${m.name} (${m.provider_name})`"
                :value="m.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="视频模型">
            <el-select v-model="selectedVideoModel" clearable placeholder="使用默认模型" style="width: 100%">
              <el-option-group
                v-for="provider in videoProviders"
                :key="provider.id"
                :label="provider.name"
              >
                <el-option
                  v-for="m in provider.models"
                  :key="m.id"
                  :label="m.name"
                  :value="m.id"
                />
              </el-option-group>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-button type="primary" @click="saveModelSettings" :loading="saving" style="margin-top: 16px">
        保存模型设置
      </el-button>
    </el-card>

    <!-- Quick links -->
    <el-card shadow="hover">
      <template #header>
        <h3>流程入口</h3>
        <p class="card-subtitle">把四个关键阶段放到一层，减少跳转认知成本。</p>
      </template>
      <el-row :gutter="16">
        <el-col :span="6" v-for="link in quickLinks" :key="link.label">
          <router-link :to="link.to" class="quick-link-card">
            <h3>{{ link.label }}</h3>
            <p>{{ link.desc }}</p>
          </router-link>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.card-title {
  margin: 0;
  font-size: 1.3rem;
}
.card-subtitle {
  color: var(--text-muted);
  line-height: 1.6;
  margin-top: 6px;
}
.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.overview-tags {
  display: flex;
  gap: 6px;
}
.stat-block {
  padding: 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(29, 26, 23, 0.08);
}
.stat-block strong {
  display: block;
  font-size: 1.5rem;
}
.stat-block span {
  display: block;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 0.84rem;
}
.quick-link-card {
  display: block;
  padding: 20px;
  border-radius: 16px;
  background: var(--surface-bg);
  border: 1px solid rgba(29, 26, 23, 0.08);
  transition: transform 0.18s, box-shadow 0.18s;
}
.quick-link-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(78, 56, 38, 0.1);
}
.quick-link-card h3 {
  margin: 0;
  font-size: 1rem;
}
.quick-link-card p {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: 0.86rem;
  line-height: 1.6;
}
</style>
