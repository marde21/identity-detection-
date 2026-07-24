import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())

def main():
    base = "frontend/src"
    
    write_file(f"{base}/main.js", """
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/style.css'

createApp(App).use(router).mount('#app')
""")

    write_file(f"{base}/router/index.js", """
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
""")

    write_file(f"{base}/App.vue", """
<template>
  <div v-if="$route.path === '/'" class="landing-layout">
    <router-view />
  </div>
  <div v-else class="app-shell">
    <div class="sidebar">
      <div class="brand">🔎 Watchlist System</div>
      <nav>
        <router-link to="/dashboard" active-class="active">🏠 Dashboard</router-link>
        <router-link to="/camera" active-class="active">📷 Live Camera</router-link>
        <router-link to="/watchlist" active-class="active">📋 Manage Watchlist</router-link>
        <router-link to="/search" active-class="active">🔍 Search Photo</router-link>
        <router-link to="/alerts" active-class="active">🚨 Alert History</router-link>
        <router-link to="/settings" active-class="active">⚙️ Settings</router-link>
      </nav>
    </div>
    <div class="main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
</script>
""")

    write_file(f"{base}/views/Landing.vue", """
<template>
    <div class="scan-line"></div>
    <div class="ambient-glow"></div>

    <nav>
        <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--primary);">
                <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
                <path d="M12 12 2.1 12"></path>
                <path d="M12 12 21.9 12"></path>
                <path d="M12 12 12 21.9"></path>
                <circle cx="12" cy="12" r="4"></circle>
            </svg>
            Crime Detection System
        </div>
        <router-link to="/dashboard" class="btn-enter">Enter System</router-link>
    </nav>

    <main class="hero">
        <Transition name="fade-up" appear>
            <div v-show="mounted" style="transition-delay: 100ms;">
                <div class="badge">Advanced AI Face Watchlist</div>
            </div>
        </Transition>

        <Transition name="fade-up" appear>
            <h1 v-show="mounted" style="transition-delay: 200ms;">
                Next-Generation <br>
                <span class="highlight">Threat Detection</span>
            </h1>
        </Transition>

        <Transition name="fade-up" appear>
            <p class="subtitle" v-show="mounted" style="transition-delay: 300ms;">
                Instantly identify suspects, secure your village, and monitor live feeds with state-of-the-art AI facial recognition technology.
            </p>
        </Transition>

        <Transition name="fade-up" appear>
            <div v-show="mounted" style="transition-delay: 400ms;">
                <router-link to="/dashboard" class="cta-button">Launch Dashboard</router-link>
            </div>
        </Transition>
    </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const mounted = ref(false)
onMounted(() => {
    setTimeout(() => { mounted.value = true }, 100)
})
</script>

<style scoped>
:root {
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --bg: #0f172a;
    --text-light: #f8fafc;
    --text-muted: #94a3b8;
}

body {
    margin: 0; padding: 0; font-family: 'Inter', sans-serif;
    background-color: var(--bg); color: var(--text-light);
    overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column;
}

.ambient-glow {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    width: 800px; height: 800px; background: radial-gradient(circle, rgba(37,99,235,0.15) 0%, rgba(15,23,42,0) 70%);
    z-index: -1; pointer-events: none;
}
nav { padding: 24px 48px; display: flex; justify-content: space-between; align-items: center; z-index: 10; }
.logo { font-weight: 800; font-size: 1.5rem; letter-spacing: -0.5px; display: flex; align-items: center; gap: 12px; }
.logo span { color: var(--primary); }
.btn-enter {
    background: rgba(37, 99, 235, 0.1); color: var(--primary); border: 1px solid rgba(37, 99, 235, 0.3);
    padding: 10px 24px; border-radius: 99px; text-decoration: none; font-weight: 600;
    transition: all 0.3s ease; backdrop-filter: blur(10px);
}
.btn-enter:hover { background: var(--primary); color: white; box-shadow: 0 0 20px rgba(37, 99, 235, 0.4); transform: translateY(-2px); }
.hero { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 0 24px; z-index: 10; margin-top: 100px; }
.badge { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 99px; font-size: 0.9rem; color: var(--text-muted); margin-bottom: 24px; backdrop-filter: blur(10px); }
h1 { font-size: 4.5rem; font-weight: 800; line-height: 1.1; margin: 0 0 24px 0; letter-spacing: -2px; max-width: 800px; }
h1 .highlight { background: linear-gradient(135deg, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { font-size: 1.25rem; color: var(--text-muted); max-width: 600px; line-height: 1.6; margin-bottom: 48px; font-weight: 300; }
.cta-button { display: inline-block; background: var(--primary); color: white; text-decoration: none; padding: 16px 48px; border-radius: 99px; font-size: 1.1rem; font-weight: 600; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; }
.cta-button:hover { transform: translateY(-2px) scale(1.02); box-shadow: 0 10px 30px rgba(37, 99, 235, 0.4); background: var(--primary-dark); }
.fade-up-enter-active, .fade-up-leave-active { transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-up-enter-from, .fade-up-leave-to { opacity: 0; transform: translateY(30px); }
.scan-line { position: fixed; top: 0; left: 0; width: 100%; height: 2px; background: rgba(37, 99, 235, 0.3); box-shadow: 0 0 20px rgba(37, 99, 235, 0.5); animation: scan 8s infinite linear; z-index: -1; opacity: 0.5; }
@keyframes scan { 0% { top: 0; } 50% { top: 100%; } 100% { top: 0; } }
</style>
""")

    write_file(f"{base}/views/Dashboard.vue", """
<template>
  <h1>Dashboard</h1>
  <div class="grid">
    <div class="card stat-card">
      <div class="stat-value">{{ data.watchlist_count }}</div>
      <div class="stat-label">Enrolled in Watchlist</div>
    </div>
    <div class="card stat-card">
      <div class="stat-value">{{ data.total_alerts }}</div>
      <div class="stat-label">Total Alerts Logged</div>
    </div>
    <div class="card stat-card danger">
      <div class="stat-value">{{ data.high_danger_count }}</div>
      <div class="stat-label">HIGH Danger Alerts</div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const data = ref({ watchlist_count: 0, total_alerts: 0, high_danger_count: 0 })
onMounted(async () => {
    const res = await axios.get('http://127.0.0.1:5000/api/dashboard')
    data.value = res.data
})
</script>
""")

    write_file(f"{base}/views/Camera.vue", """
<template>
  <h1>Live Camera</h1>
  <div class="card">
    <div class="chip">
        <span class="dot" :class="isRunning ? 'on' : 'off'"></span>
        <span>{{ isRunning ? 'Camera running' : 'Camera stopped' }}</span>
    </div>
    <div style="display: flex; gap: 20px; margin-top: 14px;">
        <div style="flex: 2;">
            <div v-if="!isRunning" class="camera-placeholder">📷 Camera is not running</div>
            <img v-else :src="'http://127.0.0.1:5000/video_feed?t=' + timestamp" style="max-width: 100%; border-radius: 8px;">
        </div>
        <div style="flex: 1;" v-if="alert">
            <div style="padding: 20px; background: #fff; border-radius: 12px; border: 2px solid #ef4444;">
                <h3 style="color: #ef4444;">MATCH DETECTED</h3>
                <img :src="'http://127.0.0.1:5000' + alert.photo_url" style="width: 140px; height: 140px; border-radius: 50%;" v-if="alert.photo_url">
                <h4>{{ alert.name }}</h4>
                <p>Confidence: {{ (alert.similarity * 100).toFixed(1) }}%</p>
                <p>Case: {{ alert.case_number }}</p>
                <p>Crime: {{ alert.crime }}</p>
                <p>Danger: {{ alert.danger_level }}</p>
            </div>
        </div>
    </div>
    <button @click="isRunning ? stopCamera() : startCamera()" style="margin-top:20px;">
        {{ isRunning ? 'Stop Monitoring' : 'Start Monitoring' }}
    </button>
  </div>
</template>
<script setup>
import { ref, onUnmounted } from 'vue'
import axios from 'axios'

const isRunning = ref(false)
const alert = ref(null)
const timestamp = ref(Date.now())
let pollInterval = null

const pollAlert = async () => {
    if (!isRunning.value) return
    try {
        const res = await axios.get('http://127.0.0.1:5000/api/latest_alert')
        alert.value = res.data.alert || null
    } catch(e) {}
}

const startCamera = async () => {
    await axios.post('http://127.0.0.1:5000/api/start_camera')
    timestamp.value = Date.now()
    isRunning.value = true
    pollInterval = setInterval(pollAlert, 1000)
}
const stopCamera = async () => {
    await axios.post('http://127.0.0.1:5000/api/stop_camera')
    isRunning.value = false
    alert.value = null
    clearInterval(pollInterval)
}
onUnmounted(() => clearInterval(pollInterval))
</script>
<style scoped>
.camera-placeholder { background: #f1f5f9; padding: 100px; text-align: center; border-radius: 8px; border: 2px dashed #cbd5e1;}
.dot.on { background-color: #22c55e; }
.dot.off { background-color: #ef4444; }
.chip { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 20px;}
.dot { width: 10px; height: 10px; border-radius: 50%; }
</style>
""")

    write_file(f"{base}/views/Watchlist.vue", """
<template>
  <h1>Manage Watchlist</h1>
  <div class="card">
    <table class="data-table">
        <tr><th>Photo</th><th>Name</th><th>Case #</th><th>Crime</th><th>Danger</th><th>Actions</th></tr>
        <tr v-for="r in records" :key="r.name">
            <td><img v-if="r.photo_url" :src="'http://127.0.0.1:5000' + r.photo_url" style="width: 50px; height: 50px; border-radius: 50%;"></td>
            <td>{{ r.name }}</td>
            <td>{{ r.case_number }}</td>
            <td>{{ r.crime }}</td>
            <td>{{ r.danger_level }}</td>
            <td>
                <button @click="deleteRecord(r.name)">Delete</button>
            </td>
        </tr>
    </table>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const records = ref([])
const load = async () => {
    const res = await axios.get('http://127.0.0.1:5000/api/watchlist')
    records.value = res.data.records
}
const deleteRecord = async (name) => {
    const fd = new FormData()
    fd.append('action', 'delete')
    fd.append('original_name', name)
    await axios.post('http://127.0.0.1:5000/api/watchlist', fd)
    load()
}
onMounted(load)
</script>
""")

    write_file(f"{base}/views/Search.vue", """
<template>
  <h1>Search Photo</h1>
  <div class="card">
    <form @submit.prevent="search">
        <input type="file" ref="fileInput" required>
        <select v-model="searchType">
            <option value="watchlist">Search Watchlist</option>
            <option value="village">Search Village Database</option>
        </select>
        <button type="submit">Search</button>
    </form>
    <div v-if="results">
        <h3>Matches</h3>
        <ul>
            <li v-for="m in results.matches || results.ranked" :key="m.name">
                {{ m.name }} - {{(m.similarity*100).toFixed(1)}}%
            </li>
        </ul>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import axios from 'axios'
const fileInput = ref(null)
const searchType = ref('watchlist')
const results = ref(null)

const search = async () => {
    const fd = new FormData()
    fd.append('photo', fileInput.value.files[0])
    fd.append('search_type', searchType.value)
    const res = await axios.post('http://127.0.0.1:5000/api/search', fd)
    results.value = res.data
}
</script>
""")

    write_file(f"{base}/views/Alerts.vue", """
<template>
  <h1>Alert History</h1>
  <div class="card">
      <div v-for="p in people" :key="p.name">
          <h3>{{ p.name }}</h3>
          <ul>
              <li v-for="row in p.rows" :key="row.timestamp">{{ row.timestamp }} - {{ row.danger_level }}</li>
          </ul>
      </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const people = ref([])
onMounted(async () => {
    const res = await axios.get('http://127.0.0.1:5000/api/alerts')
    people.value = res.data.people
})
</script>
""")

    write_file(f"{base}/views/Settings.vue", """
<template>
  <h1>Settings</h1>
  <div class="card">
      <p>Threshold: {{ settings.threshold }}</p>
      <p>Cooldown: {{ settings.cooldown }}</p>
      <p>Camera Index: {{ settings.camera_index }}</p>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const settings = ref({})
onMounted(async () => {
    const res = await axios.get('http://127.0.0.1:5000/api/settings')
    settings.value = res.data
})
</script>
""")

if __name__ == "__main__":
    main()
