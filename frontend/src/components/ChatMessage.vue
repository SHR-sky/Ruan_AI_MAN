<script setup lang="ts">
defineProps<{
  role: string
  content: string
}>()

const emit = defineEmits<{
  play: []
}>()
</script>

<template>
  <div :class="['message', role]">
    <div class="bubble">
      {{ content }}
      <button v-if="role === 'assistant'" class="play-msg-btn" title="播放语音" @click="emit('play')">▶</button>
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  margin-bottom: 12px;
}
.message.user {
  justify-content: flex-end;
}
.message.assistant {
  justify-content: flex-start;
}
.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-line;
  position: relative;
}
.user .bubble {
  background: #1a73e8;
  color: white;
  border-bottom-right-radius: 4px;
}
.assistant .bubble {
  background: white;
  color: #333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 4px;
  padding-right: 40px;
}
.play-msg-btn {
  position: absolute;
  bottom: 6px;
  right: 6px;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: #5f7f4e;
  color: white;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.7;
  transition: opacity 0.15s;
}
.play-msg-btn:hover {
  opacity: 1;
}
</style>
