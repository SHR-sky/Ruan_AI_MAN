<script setup lang="ts">
</script>

<template>
  <div class="admin-container">
    <aside class="sidebar">
      <div class="logo">
        <h2>景区导览后台</h2>
      </div>
      <nav class="nav">
        <router-link to="/" class="nav-item">数据大屏</router-link>
        <router-link to="/knowledge" class="nav-item">知识库管理</router-link>
        <router-link to="/digital-human" class="nav-item">数字人配置</router-link>
      </nav>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.admin-container {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 220px;
  background: #1e293b;
  color: white;
  display: flex;
  flex-direction: column;
}
.logo {
  padding: 20px;
  border-bottom: 1px solid #334155;
}
.logo h2 {
  margin: 0;
  font-size: 16px;
  text-align: center;
}
.nav {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-item {
  display: block;
  padding: 10px 14px;
  color: #94a3b8;
  text-decoration: none;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s;
}
.nav-item:hover {
  background: #334155;
  color: white;
}
.nav-item.router-link-active {
  background: #1a73e8;
  color: white;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f1f5f9;
  padding: 24px;
}
</style>
