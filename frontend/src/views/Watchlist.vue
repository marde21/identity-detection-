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