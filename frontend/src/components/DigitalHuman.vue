<script setup lang="ts">
defineProps<{ speaking?: boolean }>()
</script>

<template>
  <div class="digital-human-container">
    <div class="placeholder">
      <div class="avatar-circle" :class="{ speaking: speaking }">
        <span>AI</span>
      </div>
      <p class="name">小导</p>
      <p class="status">{{ speaking ? '正在语音讲解...' : '待接入数字人引擎' }}</p>
    </div>
  </div>
</template>

<style scoped>
.digital-human-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder {
  text-align: center;
}
.avatar-circle {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a73e8, #34a853);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}
.avatar-circle.speaking {
  animation: pulse 1s ease-in-out infinite;
  box-shadow: 0 0 0 0 rgba(26, 115, 232, 0.5);
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(26, 115, 232, 0.5); transform: scale(1); }
  50% { box-shadow: 0 0 0 16px rgba(26, 115, 232, 0); transform: scale(1.05); }
  100% { box-shadow: 0 0 0 0 rgba(26, 115, 232, 0); transform: scale(1); }
}
.avatar-circle span {
  color: white;
  font-size: 48px;
  font-weight: bold;
}
.name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px;
}
.status {
  font-size: 13px;
  color: #999;
  margin: 0;
}
</style>
