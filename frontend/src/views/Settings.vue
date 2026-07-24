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