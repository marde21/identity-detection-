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