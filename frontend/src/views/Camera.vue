<template>
  <div class="camera-page">
    <!-- LEFT PANEL: Recent Detections -->
    <div class="left-panel card">
      <h2 style="margin-top: 0; border-bottom: 1px solid var(--border); padding-bottom: 10px;">Recent Detections</h2>
      <div v-if="recentDetections.length === 0" class="empty-state">No detections yet.</div>
      
      <div class="detections-list">
        <div v-for="det in recentDetections" :key="det.timestamp + det.name" class="detection-card" :class="det.danger_level.toLowerCase()">
          <img v-if="det.photo_url" :src="'http://127.0.0.1:5000' + det.photo_url" class="det-img" />
          <div class="det-info">
             <div class="det-name">{{ det.name }}</div>
             <div class="badge" :class="det.danger_level.toLowerCase()">{{ det.danger_level }} DANGER</div>
             <div class="det-detail">Confidence: {{(det.similarity * 100).toFixed(1)}}%</div>
             <div class="det-detail">Crime: {{ det.crime }}</div>
             <div class="det-time">{{ det.timestamp }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- RIGHT PANEL: Live Cameras -->
    <div class="main-camera-area">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">Live Cameras</h1>
        <div>
            <button v-if="!isMonitoring" @click="toggleMonitoring" class="btn-start">▶ Start Monitoring</button>
            <button v-else @click="toggleMonitoring" class="btn-stop">⏹ Stop Monitoring</button>
        </div>
      </div>
      
      <div class="camera-grid">
        <div v-for="cam in cameras" :key="cam.id" class="card camera-card">
          <div class="chip">
            <span class="dot" :class="{ on: isMonitoring, off: !isMonitoring }"></span>
            <span>{{ cam.name }} ({{ cam.source }})</span>
          </div>
          <div class="video-container">
            <img v-if="isMonitoring" :src="'http://127.0.0.1:5000/video_feed/' + cam.id + '?t=' + timestamp" class="video-feed" @error="handleImageError" />
            <div v-else class="stopped-state">Monitoring Stopped</div>
          </div>
        </div>
      </div>
      <div v-if="cameras.length === 0" class="card">
        <p>No cameras configured. Add cameras in the Settings menu.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'

const cameras = ref([])
const timestamp = ref(Date.now())
const isMonitoring = ref(true)
const recentDetections = ref([])
let socket = null

const toggleMonitoring = async () => {
    isMonitoring.value = !isMonitoring.value
    if (isMonitoring.value) {
        timestamp.value = Date.now() // Force reload stream
    } else {
        try {
            await axios.post('http://127.0.0.1:5000/api/monitoring/stop')
        } catch(e) {
            console.error("Failed to force stop camera")
        }
    }
}

onMounted(async () => {
    try {
        const res = await axios.get('http://127.0.0.1:5000/api/cameras')
        cameras.value = res.data
    } catch (e) {
        console.error("Failed to load cameras")
    }
    
    socket = io('http://127.0.0.1:5000')
    socket.on('new_alert', (alert) => {
        // Prevent duplicate alerts within a few seconds for the same person
        const lastDet = recentDetections.value[0]
        if (lastDet && lastDet.name === alert.name) {
            const timeDiff = new Date() - new Date(lastDet.timestamp)
            if (timeDiff < 5000) return // Skip if same person detected in last 5 seconds
        }
        
        recentDetections.value.unshift(alert)
        if (recentDetections.value.length > 10) {
            recentDetections.value.pop()
        }
    })
})

onUnmounted(() => {
    if (socket) {
        socket.disconnect()
    }
})

const handleImageError = (e) => {
    e.target.style.display = 'none'
    e.target.parentElement.innerHTML = '<div class="error-state">Camera Offline or Loading...</div>'
}
</script>

<style scoped>
.camera-page {
    display: flex;
    gap: 30px;
    height: 100%;
}
.left-panel {
    flex: 0 0 350px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    height: calc(100vh - 120px); /* Fill available height minus header */
    overflow: hidden;
}
.main-camera-area {
    flex: 1;
}

/* Detections styling */
.detections-list {
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 15px;
    padding-right: 5px;
}
.empty-state {
    color: var(--text-muted);
    font-style: italic;
    text-align: center;
    margin-top: 20px;
}
.detection-card {
    display: flex;
    gap: 15px;
    background: rgba(0,0,0,0.2);
    border-radius: 8px;
    padding: 12px;
    border-left: 4px solid #666;
    animation: slideIn 0.3s ease-out;
}
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
.detection-card.high { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.1); }
.detection-card.medium { border-left-color: #eab308; background: rgba(234, 179, 8, 0.1); }
.detection-card.low { border-left-color: #22c55e; background: rgba(34, 197, 94, 0.1); }

.det-img {
    width: 70px;
    height: 70px;
    border-radius: 8px;
    object-fit: cover;
}
.det-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
}
.det-name {
    font-weight: 700;
    font-size: 1.1rem;
    color: white;
}
.det-detail {
    font-size: 0.85rem;
    color: #cbd5e1;
}
.det-time {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 4px;
    text-align: right;
}
.badge {
    align-self: flex-start;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: bold;
    color: white;
}
.badge.high { background: #ef4444; }
.badge.medium { background: #eab308; }
.badge.low { background: #22c55e; }

/* Existing Camera styling */
.camera-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
}
.camera-card {
    display: flex;
    flex-direction: column;
    gap: 15px;
}
.video-container {
    background: #000;
    border-radius: 8px;
    overflow: hidden;
    aspect-ratio: 16/9;
    display: flex;
    align-items: center;
    justify-content: center;
}
.video-feed {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.error-state {
    color: #ef4444;
    font-weight: 600;
}
.stopped-state {
    color: #94a3b8;
    font-weight: 600;
    font-size: 1.2rem;
}
.dot.on { background-color: var(--success); box-shadow: 0 0 5px var(--success); }
.dot.off { background-color: #666; }
.chip { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; background: var(--card-bg-2); border: 1px solid var(--border); border-radius: 20px; font-weight: 600; font-size: 0.9rem; color: var(--text-muted); }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.btn-start { background-color: #22c55e; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 1rem; }
.btn-stop { background-color: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 1rem; }
</style>