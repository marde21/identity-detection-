<template>
  <div class="app-shell">
    <header class="top-navbar">
      <div class="brand">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--primary);">
            <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
            <path d="M12 12 2.1 12"></path>
            <path d="M12 12 21.9 12"></path>
            <path d="M12 12 12 21.9"></path>
            <circle cx="12" cy="12" r="4"></circle>
        </svg>
        <span>Watchlist System</span>
      </div>
      <nav class="nav-links">
        <router-link to="/" active-class="active" exact>🏠 Dashboard</router-link>
        <router-link to="/camera" active-class="active">📷 Live Camera</router-link>
        <router-link to="/watchlist" active-class="active">📋 Watchlist</router-link>
        <router-link to="/search" active-class="active">🔍 Search</router-link>
        <router-link to="/alerts" active-class="active">🚨 Alerts</router-link>
        <router-link to="/settings" active-class="active">⚙️ Settings</router-link>
      </nav>
    </header>
    
    <div class="main-content">
      <router-view />
    </div>

    <!-- Global Alert Toast -->
    <div v-if="globalAlert" class="global-alert-toast">
        <div class="toast-header">🚨 SYSTEM ALERT - {{ globalAlert.danger_level }} DANGER</div>
        <div class="toast-body">
            <img v-if="globalAlert.photo_url" :src="'http://127.0.0.1:5000' + globalAlert.photo_url" class="toast-img" />
            <div class="toast-details">
                <strong>{{ globalAlert.name }}</strong> detected!
                <br>Confidence: {{ (globalAlert.similarity * 100).toFixed(1) }}%
            </div>
        </div>
        <button @click="globalAlert = null">Dismiss</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { io } from 'socket.io-client'

const globalAlert = ref(null)
let lastAlarmTime = 0

const playAlarm = () => {
    const now = Date.now()
    if (now - lastAlarmTime < 2000) return // Throttle alarm sound to once per 2s
    lastAlarmTime = now
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gainNode = ctx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.5);
        gainNode.gain.setValueAtTime(0.2, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
        osc.connect(gainNode);
        gainNode.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.5);
    } catch (e) {
        console.error("Audio playback failed", e)
    }
}

onMounted(() => {
    const socket = io('http://127.0.0.1:5000')
    socket.on('new_alert', (alert) => {
        globalAlert.value = alert
        playAlarm()
    })
})
</script>