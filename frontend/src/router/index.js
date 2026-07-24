import { createRouter, createWebHistory } from 'vue-router'
import Landing from '../views/Landing.vue'
import Dashboard from '../views/Dashboard.vue'
import Camera from '../views/Camera.vue'
import Watchlist from '../views/Watchlist.vue'
import Search from '../views/Search.vue'
import Alerts from '../views/Alerts.vue'
import Settings from '../views/Settings.vue'

const routes = [
  { path: '/', component: Landing },
  { path: '/dashboard', component: Dashboard },
  { path: '/camera', component: Camera },
  { path: '/watchlist', component: Watchlist },
  { path: '/search', component: Search },
  { path: '/alerts', component: Alerts },
  { path: '/settings', component: Settings }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router