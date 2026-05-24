<script setup lang="ts">
defineProps<{
  role: string
  content: string
}>()
</script>

<template>
  <div :class="['message', role]">
    <div class="bubble">
      {{ content }}
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
}
</style>
