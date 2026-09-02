<template>
    <div class="ambient-glow"></div>

    <main class="hero">
        <Transition name="fade-up" appear>
            <div v-show="mounted" style="transition-delay: 100ms;">
                <div class="badge">Advanced AI Face Watchlist</div>
            </div>
        </Transition>

        <Transition name="fade-up" appear>
            <h1 v-show="mounted" style="transition-delay: 200ms;">
                Next-Generation <br>
                <span class="highlight">Threat Detection</span>
            </h1>
        </Transition>

        <Transition name="fade-up" appear>
            <div v-show="mounted" class="dashboard-grid" style="transition-delay: 300ms;">
                <div class="card stat-card">
                  <div class="stat-value">{{ data.watchlist_count }}</div>
                  <div class="stat-label">Enrolled in Watchlist</div>
                </div>
                <div class="card stat-card">
                  <div class="stat-value">{{ data.total_alerts }}</div>
                  <div class="stat-label">Total Alerts Logged</div>
                </div>
                <div class="card stat-card danger">
                  <div class="stat-value" style="color: #ef4444;">{{ data.high_danger_count }}</div>
                  <div class="stat-label">HIGH Danger Alerts</div>
                </div>
            </div>
        </Transition>
    </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const mounted = ref(false)
const data = ref({ watchlist_count: 0, total_alerts: 0, high_danger_count: 0 })

onMounted(async () => {
    setTimeout(() => { mounted.value = true }, 100)
    try {
        const res = await axios.get('http://127.0.0.1:5000/api/dashboard')
        data.value = res.data
    } catch (e) {
        console.error(e)
    }
})
</script>

<style scoped>
.ambient-glow {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    width: 800px; height: 800px; background: radial-gradient(circle, rgba(37,99,235,0.15) 0%, rgba(15,23,42,0) 70%);
    z-index: -1; pointer-events: none;
}
.hero { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 0 24px; z-index: 10; margin-top: 50px; }
.badge { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 99px; font-size: 0.9rem; color: var(--text-muted); margin-bottom: 24px; backdrop-filter: blur(10px); }
h1 { font-size: 4.5rem; font-weight: 800; line-height: 1.1; margin: 0 0 40px 0; letter-spacing: -2px; max-width: 800px; }
h1 .highlight { background: linear-gradient(135deg, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 30px;
    width: 100%;
    max-width: 900px;
    margin-top: 20px;
}
.stat-card {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 40px 20px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    transition: transform 0.3s ease;
}
.stat-card:hover {
    transform: translateY(-5px);
    border-color: rgba(37, 99, 235, 0.4);
}
.stat-value {
    font-size: 4rem;
    font-weight: 800;
    color: white;
    margin-bottom: 10px;
}
.stat-label {
    font-size: 1.1rem;
    color: var(--text-muted);
    font-weight: 600;
}
.stat-card.danger {
    border-color: rgba(239, 68, 68, 0.3);
}
.stat-card.danger:hover {
    border-color: rgba(239, 68, 68, 0.6);
}

.fade-up-enter-active, .fade-up-leave-active { transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-up-enter-from, .fade-up-leave-to { opacity: 0; transform: translateY(30px); }
</style>