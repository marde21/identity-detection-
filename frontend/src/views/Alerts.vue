<template>
  <h1>Alert History</h1>
  <div class="card">
      <div v-for="p in people" :key="p.name">
          <h3>{{ p.name }}</h3>
          <ul>
              <li v-for="row in p.rows" :key="row.timestamp">{{ row.timestamp }} - {{ row.danger_level }}</li>
          </ul>
      </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const people = ref([])
onMounted(async () => {
    const res = await axios.get('http://127.0.0.1:5000/api/alerts')
    people.value = res.data.people
})
</script>