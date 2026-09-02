<template>
  <div class="alerts-page">
    <h1>Alert Timeline</h1>
    <p class="subtitle">Historical tracking of all detected suspects across all cameras.</p>

    <div class="timeline">
      <div v-for="alert in history" :key="alert.id" class="timeline-item">
        <div class="timeline-time">
          {{ formatTime(alert.timestamp) }}
        </div>
        <div class="timeline-content card">
          <div class="alert-header">
            <span class="danger-badge" :class="alert.danger_level.toLowerCase()">
              {{ alert.danger_level }} DANGER
            </span>
            <span class="camera-badge">📷 {{ alert.camera_name || 'Unknown Camera' }}</span>
          </div>
          
          <div class="alert-body">
            <div class="photo-container">
              <img v-if="alert.photo_url" :src="'http://127.0.0.1:5000' + alert.photo_url" alt="Snapshot" />
              <div v-else class="no-photo">No Photo</div>
            </div>
            
            <div class="alert-details">
              <h2>{{ alert.person_name }}</h2>
              <p><strong>Confidence:</strong> {{ (alert.confidence * 100).toFixed(1) }}%</p>
              <p><strong>Crime:</strong> {{ alert.crime }}</p>
              <p><strong>Case #:</strong> {{ alert.case_number }}</p>
              <p><strong>Date:</strong> {{ formatDate(alert.timestamp) }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="history.length === 0" class="card" style="margin-left: 140px;">
          <p>No alerts recorded yet.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const history = ref([])

onMounted(async () => {
    try {
        const res = await axios.get('http://127.0.0.1:5000/api/alert_history')
        history.value = res.data.history || []
    } catch (e) {
        console.error("Failed to fetch history")
    }
})

const formatDate = (ts) => {
    if (!ts) return ''
    // Handle SQLite timestamp format 'YYYY-MM-DD HH:MM:SS' by replacing space with 'T' for safari compatibility
    const d = new Date(ts.replace(' ', 'T'))
    return d.toLocaleDateString()
}
const formatTime = (ts) => {
    if (!ts) return ''
    const d = new Date(ts.replace(' ', 'T'))
    return d.toLocaleTimeString()
}
</script>

<style scoped>
.subtitle {
    color: var(--text-muted);
    margin-bottom: 30px;
}
.timeline {
    position: relative;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px 0;
}
.timeline::before {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    left: 120px;
    width: 4px;
    background: var(--border);
    border-radius: 4px;
}
.timeline-item {
    display: flex;
    margin-bottom: 30px;
    position: relative;
}
.timeline-time {
    width: 100px;
    text-align: right;
    padding-right: 35px;
    font-weight: 600;
    color: var(--text-muted);
    padding-top: 20px;
}
.timeline-item::before {
    content: '';
    position: absolute;
    left: 114px;
    top: 24px;
    width: 16px;
    height: 16px;
    background: var(--danger);
    border: 4px solid var(--bg);
    border-radius: 50%;
    z-index: 1;
}
.timeline-content {
    flex: 1;
    margin-left: 20px;
    padding: 20px;
}
.alert-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
}
.danger-badge {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 800;
    color: white;
}
.danger-badge.high { background: var(--danger); }
.danger-badge.medium { background: #f59e0b; }
.danger-badge.low { background: #3b82f6; }

.camera-badge {
    background: var(--card-bg-2);
    color: var(--text-muted);
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}
.alert-body {
    display: flex;
    gap: 20px;
}
.photo-container {
    width: 140px;
    height: 140px;
    border-radius: 8px;
    overflow: hidden;
    background: var(--card-bg-2);
    border: 1px solid var(--border);
    flex-shrink: 0;
}
.photo-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.no-photo {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    font-weight: 600;
}
.alert-details h2 {
    margin: 0 0 10px 0;
    color: #fff;
    text-transform: capitalize;
}
.alert-details p {
    margin: 5px 0;
    color: var(--text-muted);
    font-size: 0.95rem;
}
</style>