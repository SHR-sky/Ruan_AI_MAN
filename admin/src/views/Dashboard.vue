<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref({
  today_visitors: 0,
  weekly_visitors: 0,
  total_visitors: 0,
  satisfaction_rate: 0,
  hot_questions: [] as string[],
})

onMounted(async () => {
  try {
    const res = await api.get('/admin/dashboard')
    stats.value = res.data
  } catch {
    // API 未就绪时使用占位数据
  }
})
</script>

<template>
  <div class="dashboard">
    <h2>运营数据大屏</h2>
    <div class="cards">
      <div class="card">
        <div class="card-label">今日服务人次</div>
        <div class="card-value">{{ stats.today_visitors }}</div>
      </div>
      <div class="card">
        <div class="card-label">本周服务人次</div>
        <div class="card-value">{{ stats.weekly_visitors }}</div>
      </div>
      <div class="card">
        <div class="card-label">累计服务</div>
        <div class="card-value">{{ stats.total_visitors }}</div>
      </div>
      <div class="card">
        <div class="card-label">满意度</div>
        <div class="card-value">{{ (stats.satisfaction_rate * 100).toFixed(1) }}%</div>
      </div>
    </div>
    <div class="section">
      <h3>热门问答</h3>
      <ul v-if="stats.hot_questions.length">
        <li v-for="(q, i) in stats.hot_questions" :key="i">{{ q }}</li>
      </ul>
      <p v-else class="empty">暂无数据</p>
    </div>
  </div>
</template>

<style scoped>
.dashboard h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: #1e293b;
}
.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.card {
  background: white;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.card-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}
.card-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a73e8;
}
.section {
  background: white;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.section h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #1e293b;
}
.section ul {
  list-style: none;
  padding: 0;
}
.section li {
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 14px;
  color: #334155;
}
.empty {
  color: #94a3b8;
  font-size: 14px;
}
</style>
