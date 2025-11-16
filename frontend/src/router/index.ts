import { createRouter, createWebHistory } from 'vue-router'
import GeneratePage from '@/views/GeneratePage.vue'
import ThemePage from '@/views/ThemePage.vue'
import UserPage from '@/views/UserPage.vue'
import PublishPage from '@/views/PublishPage.vue'
import WorkflowPage from '@/views/WorkflowPage.vue'
import AgentPage from '@/views/AgentPage.vue'
import ImageManagement from '@/views/ImageManagement.vue'
import ParticipationProcessComponent from '@/components/ParticipationProcess.vue'
import PromptTemplates from '@/views/PromptTemplates.vue'
import LLMModels from '@/views/LLMModels.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/generate'
    },
    {
      path: '/generate',
      name: 'generate',
      component: GeneratePage
    },
    {
      path: '/theme',
      name: 'theme',
      component: ThemePage
    },
    {
      path: '/publish',
      name: 'publish',
      component: PublishPage
    },
    {
      path: '/workflow',
      name: 'workflow',
      component: WorkflowPage
    },
    {
      path: '/users',
      name: 'users',
      component: UserPage
    },
    {
      path: '/agent',
      name: 'agent',
      component: AgentPage
    },
    {
      path: '/images',
      name: 'images',
      component: ImageManagement
    },
    { path: '/images/participate/:id', name: 'image-participation', component: ParticipationProcessComponent, props: route => ({ initialRuleImageId: route.params.id }) },
    {
      path: '/templates',
      name: 'templates',
      component: PromptTemplates
    },
    {
      path: '/llm-models',
      name: 'llm-models',
      component: LLMModels
    }
  ]
})

export default router