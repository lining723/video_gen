<script setup lang="ts">
import { useRoute } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import { computed } from 'vue'

const route = useRoute()

const projectId = computed(() => (route.params.projectId as string) || '')

const pageMeta = computed(() => {
  const map: Record<string, { eyebrow: string; title: string }> = {
    projects: { eyebrow: 'AI Video Studio', title: '智能视频生成平台' },
    'project-dashboard': { eyebrow: 'Project Overview', title: '项目总览' },
    'scene-review': { eyebrow: 'Scene Review', title: '场景设计审核' },
    'storyboard-edit': { eyebrow: 'Storyboard', title: '分镜审核' },
    'render-progress': { eyebrow: 'Render Progress', title: '渲染控制' },
    'final-video': { eyebrow: 'Final Video', title: '最终成片' },
  }
  return map[route.name as string] || { eyebrow: '', title: '' }
})
</script>

<template>
  <AppLayout
    :project-id="projectId"
    :current-view="(route.name as string)"
    :eyebrow="pageMeta.eyebrow"
    :title="pageMeta.title"
  >
    <router-view />
  </AppLayout>
</template>
