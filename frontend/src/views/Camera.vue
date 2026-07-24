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