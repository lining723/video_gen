<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getTimeline } from '@/api/projects'
import { formatProjectLabel } from '@/utils/project'
import type { Project } from '@/types'

const props = defineProps<{
  projectId: string
  currentView: string
  eyebrow: string
  title: string
}>()

const router = useRouter()
const route = useRoute()

const collapsed = ref(false)
const project = ref<Project | null>(null)
const projectName = ref('')
const projectStatus = ref('')
const projectStage = ref('')

const sidebarWidth = computed(() => (collapsed.value ? '64px' : '280px'))

const stageItems = [
  { key: 'project-dashboard', label: '项目总览', icon: '📊', to: (id: string) => `/projects/${id}` },
  { key: 'scene-review', label: '场景审核', icon: '🎬', to: (id: string) => `/projects/${id}/scene` },
  { key: 'storyboard-edit', label: '分镜编辑', icon: '📝', to: (id: string) => `/projects/${id}/storyboard` },
  { key: 'render-progress', label: '渲染控制', icon: '⚙️', to: (id: string) => `/projects/${id}/renders` },
  { key: 'final-video', label: '最终成片', icon: '🎞️', to: (id: string) => `/projects/${id}/final-video` },
]

watch(
  () => props.projectId,
  async (id) => {
    if (!id) return
    try {
      const data = await getTimeline(id)
      const p = data.item.project
      project.value = p
      projectName.value = p.name
      projectStatus.value = p.status
      projectStage.value = p.current_stage
    } catch {
      // ignore
    }
  },
  { immediate: true }
)

function toggleSidebar() {
  collapsed.value = !collapsed.value
}
</script>

<template>
  <div class="app-shell">
    <!-- Ambient orbs -->
    <div class="ambient-orb one"></div>
    <div class="ambient-orb two"></div>

    <!-- Sidebar -->
    <aside
      v-if="projectId"
      class="sidebar"
      :class="{ collapsed }"
      :style="{ width: sidebarWidth }"
    >
      <div class="sidebar-project-meta" v-if="!collapsed">
        <h3>当前项目</h3>
        <strong>{{ projectName || '未命名项目' }}</strong>
        <div class="sidebar-pills">
          <el-tag v-if="projectStatus" size="small">{{ formatProjectLabel(projectStatus) }}</el-tag>
          <el-tag v-if="projectStage" size="small" type="info">{{ formatProjectLabel(projectStage) }}</el-tag>
        </div>
      </div>

      <div class="sidebar-nav" v-if="!collapsed">
        <h3>制作流程</h3>
      </div>
      <div class="sidebar-nav-items">
        <router-link
          v-for="item in stageItems"
          :key="item.key"
          :to="item.to(projectId)"
          class="nav-link"
          :class="{ active: currentView === item.key }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </div>

      <button class="sidebar-toggle" @click="toggleSidebar">
        {{ collapsed ? '▶' : '◀' }}
      </button>
    </aside>

    <!-- Topbar -->
    <header class="topbar" :style="{ marginLeft: projectId ? sidebarWidth : '0' }">
      <router-link to="/projects" class="brand">
        <span class="brand-dot"></span>
        <div>
          <strong>Frame Flow</strong>
          <span>AI video direction console</span>
        </div>
      </router-link>
      <router-link to="/projects" class="topbar-link">项目首页</router-link>
    </header>

    <!-- Main content -->
    <main class="page-shell" :style="{ marginLeft: projectId ? sidebarWidth : '0' }">
      <!-- Hero panel -->
      <section class="hero-panel">
        <div class="hero-grid">
          <div>
            <span class="eyebrow">{{ eyebrow }}</span>
            <h1 class="hero-title">{{ title }}</h1>
          </div>
        </div>
      </section>

      <!-- Page content -->
      <section class="content-area">
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  position: relative;
  min-height: 100vh;
}

.ambient-orb {
  position: fixed;
  border-radius: 999px;
  filter: blur(18px);
  opacity: 0.55;
  pointer-events: none;
  z-index: 0;
}
.ambient-orb.one {
  width: 28rem;
  height: 28rem;
  top: -10rem;
  right: -8rem;
  background: rgba(184, 92, 56, 0.14);
}
.ambient-orb.two {
  width: 20rem;
  height: 20rem;
  left: -4rem;
  bottom: 12rem;
  background: rgba(53, 89, 72, 0.12);
}

/* Sidebar */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg);
  transition: width 0.3s ease;
  overflow-y: auto;
}
.sidebar-project-meta {
  padding: 16px;
  background: var(--surface-bg);
  border-radius: 16px;
  border: 1px solid rgba(29, 26, 23, 0.08);
}
.sidebar-project-meta h3 {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.sidebar-project-meta strong {
  display: block;
  font-size: 0.95rem;
  margin-bottom: 10px;
}
.sidebar-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.sidebar-nav h3 {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 8px 0 6px;
  padding: 0 8px;
}
.sidebar-nav-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  color: var(--text-muted);
  transition: all 0.18s ease;
}
.nav-link:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.5);
}
.nav-link.active {
  color: var(--text);
  background: rgba(184, 92, 56, 0.12);
}
.nav-icon {
  font-size: 1.1rem;
}
.nav-label {
  flex: 1;
  font-size: 0.9rem;
}
.sidebar-toggle {
  margin-top: auto;
  padding: 10px;
  background: var(--surface-bg);
  border: 1px solid rgba(29, 26, 23, 0.08);
  border-radius: 12px;
  cursor: pointer;
  color: var(--text-muted);
  transition: background 0.2s;
}
.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.8);
}

/* Topbar */
.topbar {
  position: relative;
  z-index: 1;
  max-width: 1180px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: margin-left 0.3s ease;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-dot {
  width: 12px;
  height: 12px;
  border-radius: 99px;
  background: linear-gradient(135deg, var(--accent), #e8ab82);
  box-shadow: 0 0 0 10px rgba(184, 92, 56, 0.09);
}
.brand strong {
  display: block;
  font-size: 0.9rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.brand span {
  display: block;
  color: var(--text-muted);
  font-size: 0.78rem;
}
.topbar-link {
  color: var(--text-muted);
  font-size: 0.9rem;
  transition: color 0.18s;
}
.topbar-link:hover {
  color: var(--text);
}

/* Main content */
.page-shell {
  position: relative;
  z-index: 1;
  max-width: 1180px;
  padding: 0 24px 40px;
  transition: margin-left 0.3s ease;
}

/* Hero panel */
.hero-panel {
  position: relative;
  overflow: hidden;
  padding: 28px 32px;
  border: 1px solid rgba(29, 26, 23, 0.08);
  border-radius: 28px;
  background: linear-gradient(
    140deg,
    rgba(255, 252, 247, 0.96) 0%,
    rgba(246, 236, 224, 0.92) 44%,
    rgba(239, 232, 222, 0.9) 100%
  );
  box-shadow: 0 24px 80px rgba(72, 49, 30, 0.12);
  margin-bottom: 20px;
}
.hero-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 28px;
  align-items: end;
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text-muted);
  font-size: 0.78rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.eyebrow::before {
  content: '';
  width: 2.6rem;
  height: 1px;
  background: rgba(29, 26, 23, 0.18);
}
.hero-title {
  margin-top: 14px;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Songti SC', serif;
  font-size: clamp(2.2rem, 4vw, 3.8rem);
  line-height: 1.05;
  letter-spacing: -0.04em;
}

/* Content */
.content-area {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
</style>
