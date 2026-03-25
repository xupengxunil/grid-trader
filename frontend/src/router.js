import { createRouter, createWebHistory } from 'vue-router'
import PlanList from './components/PlanList.vue'
import PlanDetail from './components/PlanDetail.vue'
import Statistics from './components/Statistics.vue'

const routes = [
  { path: '/', redirect: '/plans' },
  { path: '/plans', component: PlanList },
  { path: '/plans/:id', component: PlanDetail, props: true },
  { path: '/statistics', component: Statistics },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
