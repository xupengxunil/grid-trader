import { createRouter, createWebHistory } from 'vue-router'
import PlanList from './components/PlanList.vue'
import PlanDetail from './components/PlanDetail.vue'
import Statistics from './components/Statistics.vue'
import StockAnalysis from './components/StockAnalysis.vue'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import Profile from './views/Profile.vue'
import { isLoggedIn, isApproved } from './store/auth.js'

const routes = [
  { path: '/login', component: Login, meta: { public: true } },
  { path: '/register', component: Register, meta: { public: true } },
  { path: '/', redirect: '/plans' },
  { path: '/plans', component: PlanList },
  { path: '/plans/:id', component: PlanDetail, props: true },
  { path: '/statistics', component: Statistics },
  { path: '/analysis', component: StockAnalysis },
  { path: '/profile', component: Profile },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!isLoggedIn.value) return '/login'
  if (!isApproved.value) return '/login'
  return true
})

export default router
