<script setup lang="ts">
const emit = defineEmits<{
  result: [text: string]
}>()

function startRecording() {
  // 待接入 Web Audio API + ASR 服务
  emit('result', '[待接入语音输入]')
}
</script>

<template>
  <button class="voice-btn" title="语音输入" @click="startRecording">
    🎤
  </button>
</template>

<style scoped>
.voice-btn {
  padding: 10px 14px;
  background: #34a853;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
}
.voice-btn:hover {
  background: #2d8f47;
}
</style>
