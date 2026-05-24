import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import KnowledgeBase from '../views/KnowledgeBase.vue'
import DigitalHumanConfig from '../views/DigitalHumanConfig.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/knowledge', name: 'KnowledgeBase', component: KnowledgeBase },
  { path: '/digital-human', name: 'DigitalHumanConfig', component: DigitalHumanConfig },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
