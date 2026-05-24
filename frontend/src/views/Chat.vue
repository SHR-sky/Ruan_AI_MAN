<script setup lang="ts">
import { ref } from 'vue'
import DigitalHuman from '../components/DigitalHuman.vue'
import ChatMessage from '../components/ChatMessage.vue'
import VoiceInput from '../components/VoiceInput.vue'

const messages = ref<Array<{ role: string; content: string }>>([])
const inputText = ref('')

function sendText() {
  if (!inputText.value.trim()) return
  messages.value.push({ role: 'user', content: inputText.value })
  messages.value.push({ role: 'assistant', content: '[待接入AI响应]' })
  inputText.value = ''
}

function handleVoiceResult(text: string) {
  messages.value.push({ role: 'user', content: text })
  messages.value.push({ role: 'assistant', content: '[待接入AI响应]' })
}
</script>

<template>
  <div class="chat-layout">
    <header class="chat-header">
      <h1>景区智能导览</h1>
    </header>
    <main class="chat-main">
      <div class="digital-human-area">
        <DigitalHuman />
      </div>
      <div class="chat-area">
        <div class="messages">
          <ChatMessage
            v-for="(msg, idx) in messages"
            :key="idx"
            :role="msg.role"
            :content="msg.content"
          />
          <div v-if="messages.length === 0" class="welcome">
            <p>您好！我是您的AI导游，请问有什么可以帮您？</p>
          </div>
        </div>
        <div class="input-area">
          <input
            v-model="inputText"
            type="text"
            placeholder="输入您的问题..."
            @keyup.enter="sendText"
          />
          <button @click="sendText">发送</button>
          <VoiceInput @result="handleVoiceResult" />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}
.chat-header {
  background: #1a73e8;
  color: white;
  padding: 16px 24px;
  text-align: center;
}
.chat-header h1 {
  margin: 0;
  font-size: 20px;
}
.chat-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.digital-human-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e8edf3;
}
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #ddd;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.welcome {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 16px;
}
.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #ddd;
  background: white;
}
.input-area input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}
.input-area input:focus {
  border-color: #1a73e8;
}
.input-area button {
  padding: 10px 20px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.input-area button:hover {
  background: #1557b0;
}
</style>
