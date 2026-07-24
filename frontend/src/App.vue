<template>
  <div v-if="$route.path === '/'" class="landing-layout">
    <router-view />
  </div>
  <div v-else class="app-shell">
    <div class="sidebar">
      <div class="brand">🔎 Watchlist System</div>
      <nav>
        <router-link to="/dashboard" active-class="active">🏠 Dashboard</router-link>
        <router-link to="/camera" active-class="active">📷 Live Camera</router-link>
        <router-link to="/watchlist" active-class="active">📋 Manage Watchlist</router-link>
        <router-link to="/search" active-class="active">🔍 Search Photo</router-link>
        <router-link to="/alerts" active-class="active">🚨 Alert History</router-link>
        <router-link to="/settings" active-class="active">⚙️ Settings</router-link>
      </nav>
    </div>
    <div class="main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
</script>