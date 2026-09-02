<template>
  <h1>Settings & Cameras</h1>
  
  <div class="card" style="margin-bottom: 20px;">
      <h2>Camera Management</h2>
      <table class="data-table">
          <tr><th>ID</th><th>Name</th><th>Source (USB/RTSP)</th><th>Actions</th></tr>
          <tr v-for="cam in cameras" :key="cam.id">
              <td>{{ cam.id }}</td>
              <td>{{ cam.name }}</td>
              <td>{{ cam.source }}</td>
              <td>
                  <button @click="deleteCamera(cam.id)" class="btn-danger">Delete</button>
              </td>
          </tr>
      </table>
      
      <form @submit.prevent="addCamera" style="margin-top: 20px; display: flex; gap: 10px;">
          <input type="text" v-model="newCam.name" placeholder="Camera Name (e.g. North Gate)" required />
          <input type="text" v-model="newCam.source" placeholder="Source (e.g. 0 for USB, rtsp://...)" required />
          <button type="submit">Add Camera</button>
      </form>
  </div>

  <div class="card">
      <h2>System Preferences</h2>
      <p>Threshold: {{ settings.threshold }}</p>
      <p>Cooldown: {{ settings.cooldown }}</p>
      <p><em>(Other settings are managed via config.py)</em></p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const settings = ref({})
const cameras = ref([])
const newCam = ref({ name: '', source: '' })

const loadData = async () => {
    const res = await axios.get('http://127.0.0.1:5000/api/settings')
    settings.value = res.data
    
    const resCam = await axios.get('http://127.0.0.1:5000/api/cameras')
    cameras.value = resCam.data
}

const addCamera = async () => {
    const fd = new FormData()
    fd.append('action', 'add')
    fd.append('name', newCam.value.name)
    fd.append('source', newCam.value.source)
    await axios.post('http://127.0.0.1:5000/api/cameras', fd)
    newCam.value.name = ''
    newCam.value.source = ''
    loadData()
}

const deleteCamera = async (id) => {
    const fd = new FormData()
    fd.append('action', 'delete')
    fd.append('camera_id', id)
    await axios.post('http://127.0.0.1:5000/api/cameras', fd)
    loadData()
}

onMounted(loadData)
</script>

<style scoped>
input {
    padding: 8px;
    border: 1px solid var(--border);
    border-radius: 4px;
    flex: 1;
    background: var(--bg);
    color: var(--text);
}
</style>