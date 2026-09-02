<template>
  <div class="search-container">
    <h1>Search Suspect Photo</h1>
    <p class="subtitle">Upload a photo of an unknown suspect to identify them against the database.</p>
    
    <div class="card search-card">
        <form @submit.prevent="search" class="search-form">
            <div class="form-group">
                <label>Select Photo:</label>
                <input type="file" ref="fileInput" required accept="image/*" class="file-input">
            </div>
            
            <div class="form-group">
                <label>Search Against:</label>
                <select v-model="searchType" class="select-input">
                    <option value="village">Entire Population (100k+ Database)</option>
                    <option value="watchlist">Known Criminal Watchlist</option>
                </select>
            </div>
            
            <button type="submit" class="btn-primary" :disabled="isSearching">
                {{ isSearching ? 'Searching...' : 'Scan Photo' }}
            </button>
        </form>
    </div>

    <div v-if="results" class="results-section">
        <h2>Results</h2>
        
        <div v-if="results.best_match || (results.matches && results.matches.length > 0)" class="best-match card success">
            <h3 v-if="results.best_match">🎯 BEST MATCH IDENTIFIED</h3>
            <h3 v-else>🎯 MATCHES FOUND ON WATCHLIST</h3>
            
            <div class="match-info" v-if="results.best_match">
                <img v-if="results.best_match.photo_url" :src="'http://127.0.0.1:5000' + results.best_match.photo_url" class="profile-img" />
                <div class="details">
                    <div class="name">{{ results.best_match.name }}</div>
                    <div class="confidence">Confidence: {{(results.best_match.score*100 || results.best_match.similarity*100).toFixed(1)}}%</div>
                </div>
            </div>
            
            <div class="match-info" v-else>
                <div class="details" style="display:flex; flex-direction: column; gap:10px;">
                    <div v-for="match in results.matches" :key="match.name" style="display:flex; align-items:center; gap:15px;">
                        <img v-if="match.photo_url" :src="'http://127.0.0.1:5000' + match.photo_url" class="profile-img" style="width:70px; height:70px;" />
                        <div>
                            <div class="name" style="font-size: 1.3rem;">{{ match.name }}</div>
                            <div class="confidence">Confidence: {{(match.similarity*100).toFixed(1)}}%</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div v-else class="best-match card danger">
            <h3>⚠️ NO CONFIDENT MATCH FOUND</h3>
            <p>The AI could not find a match above the confidence threshold. See closest candidates below.</p>
        </div>

        <div v-if="results.result_image" class="result-image-container card">
            <h3>Annotated Suspect Photo</h3>
            <img :src="'http://127.0.0.1:5000' + results.result_image" class="annotated-img" />
        </div>

        <h3 style="margin-top: 30px;">Top Candidates</h3>
        <div class="candidates-grid">
            <div v-for="m in (results.ranked || results.matches)" :key="m.name" class="card candidate-card">
                <img v-if="m.photo_url" :src="'http://127.0.0.1:5000' + m.photo_url" class="candidate-img" />
                <div class="candidate-details">
                    <div class="name">{{ m.name }}</div>
                    <div class="score">{{(m.score*100 || m.similarity*100).toFixed(1)}}% match</div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const fileInput = ref(null)
const searchType = ref('village')
const results = ref(null)
const isSearching = ref(false)

const search = async () => {
    isSearching.value = true
    results.value = null
    const fd = new FormData()
    fd.append('photo', fileInput.value.files[0])
    fd.append('search_type', searchType.value)
    
    try {
        const res = await axios.post('http://127.0.0.1:5000/api/search', fd)
        results.value = res.data
    } catch (e) {
        console.error("Search failed")
    }
    isSearching.value = false
}
</script>

<style scoped>
.search-container { max-width: 900px; margin: 0 auto; }
.subtitle { color: var(--text-muted); margin-bottom: 30px; }
.search-card { padding: 30px; margin-bottom: 40px; }
.search-form { display: flex; flex-direction: column; gap: 20px; }
.form-group { display: flex; flex-direction: column; gap: 8px; }
.form-group label { font-weight: 600; color: var(--text-muted); }
.file-input, .select-input { padding: 12px; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(0,0,0,0.2); color: white; font-size: 1rem; }
.results-section h2 { border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 20px; }
.best-match { margin-bottom: 30px; border-width: 2px; }
.best-match.success { border-color: #22c55e; background: rgba(34, 197, 94, 0.05); }
.best-match.danger { border-color: #ef4444; background: rgba(239, 68, 68, 0.05); }
.best-match h3 { margin-top: 0; color: inherit; }
.match-info { display: flex; align-items: center; gap: 20px; }
.profile-img { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #22c55e; }
.details .name { font-size: 1.5rem; font-weight: 800; color: white; }
.details .confidence { font-size: 1.1rem; color: #22c55e; font-weight: 600; }
.annotated-img { max-width: 100%; border-radius: 8px; }
.result-image-container { text-align: center; margin-bottom: 30px; }
.candidates-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
.candidate-card { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 15px; }
.candidate-img { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-bottom: 10px; }
.candidate-details .name { font-weight: 600; color: white; margin-bottom: 5px; }
.candidate-details .score { color: var(--text-muted); font-size: 0.9rem; }
</style>