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