import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      redirect: '/projects',
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('@/views/ProjectList.vue'),
    },
    {
      path: '/projects/:projectId',
      name: 'project-dashboard',
      component: () => import('@/views/ProjectDashboard.vue'),
    },
    {
      path: '/projects/:projectId/scene',
      name: 'scene-review',
      component: () => import('@/views/SceneReview.vue'),
    },
    {
      path: '/projects/:projectId/storyboard',
      name: 'storyboard-edit',
      component: () => import('@/views/StoryboardEdit.vue'),
    },
    {
      path: '/projects/:projectId/renders',
      name: 'render-progress',
      component: () => import('@/views/RenderProgress.vue'),
    },
    {
      path: '/projects/:projectId/final-video',
      name: 'final-video',
      component: () => import('@/views/FinalVideo.vue'),
    },
  ],
})

export default router
