<template>
  <h1>Manage Watchlist</h1>
  
  <div class="card" style="margin-bottom: 20px;">
    <h2>Enroll New Person</h2>
    <form @submit.prevent="enrollPerson" class="enroll-form">
        <input v-model="newPerson.name" placeholder="Full Name" required />
        <input v-model="newPerson.caseNumber" placeholder="Case Number" />
        <input v-model="newPerson.crime" placeholder="Crime" />
        <select v-model="newPerson.dangerLevel">
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
        </select>
        <input type="file" ref="photoInput" required accept="image/*" />
        <button type="submit">Enroll</button>
    </form>
    <div v-if="enrollError" class="error-msg">{{ enrollError }}</div>
  </div>

  <div class="card">
    <table class="data-table">
        <tr><th>Photo</th><th>Name</th><th>Case #</th><th>Crime</th><th>Danger</th><th>Actions</th></tr>
        <tr v-for="r in records" :key="r.name">
            <td><img v-if="r.photo_url" :src="'http://127.0.0.1:5000' + r.photo_url" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;"></td>
            <td>{{ r.name }}</td>
            <td>{{ r.case_number }}</td>
            <td>{{ r.crime }}</td>
            <td>{{ r.danger_level }}</td>
            <td>
                <button @click="deleteRecord(r.name)" class="btn-danger">Delete</button>
            </td>
        </tr>
    </table>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const records = ref([])

const newPerson = ref({
    name: '',
    caseNumber: '',
    crime: '',
    dangerLevel: 'LOW'
})
const photoInput = ref(null)
const enrollError = ref('')

const load = async () => {
    const res = await axios.get('http://127.0.0.1:5000/api/watchlist')
    records.value = res.data.records
}

const enrollPerson = async () => {
    enrollError.value = ''
    const fd = new FormData()
    fd.append('action', 'add')
    fd.append('name', newPerson.value.name)
    fd.append('case_number', newPerson.value.caseNumber)
    fd.append('crime', newPerson.value.crime)
    fd.append('danger_level', newPerson.value.dangerLevel)
    
    if (photoInput.value.files[0]) {
        fd.append('photos', photoInput.value.files[0])
    }
    
    try {
        await axios.post('http://127.0.0.1:5000/api/watchlist', fd)
        newPerson.value = { name: '', caseNumber: '', crime: '', dangerLevel: 'LOW' }
        photoInput.value.value = ''
        load()
    } catch (e) {
        enrollError.value = e.response?.data?.error || "Failed to enroll"
    }
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

<style scoped>
.enroll-form {
    display: flex;
    gap: 10px;
    margin-top: 15px;
    flex-wrap: wrap;
}
.enroll-form input, .enroll-form select {
    padding: 8px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--bg);
    color: var(--text);
}
.error-msg {
    color: var(--danger);
    margin-top: 10px;
}
</style>