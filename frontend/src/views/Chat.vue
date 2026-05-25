<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DigitalHuman from '../components/DigitalHuman.vue'
import ChatMessage from '../components/ChatMessage.vue'
import VoiceInput from '../components/VoiceInput.vue'
import api from '../api'

const messages = ref<Array<{ role: string; content: string }>>([])
const inputText = ref('')
const introText = ref('')
const introName = ref('')
const isPlaying = ref(false)
const audioRef = ref<HTMLAudioElement | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await api.get('/demo/intro')
    introName.value = res.data.name
    introText.value = res.data.full_text
    messages.value.push({
      role: 'assistant',
      content: `您好！我是AI导游小导，今天为您介绍「${res.data.name}」。\n\n${res.data.full_text}`,
    })
  } catch {
    messages.value.push({ role: 'assistant', content: '您好！我是您的AI导游，请问有什么可以帮您？' })
  } finally {
    loading.value = false
  }
})

async function playIntro() {
  if (isPlaying.value) {
    audioRef.value?.pause()
    isPlaying.value = false
    return
  }
  try {
    isPlaying.value = true
    const res = await api.get('/demo/intro/audio', {
      params: { voice_type: 'default' },
      responseType: 'blob',
    })
    const url = URL.createObjectURL(res.data)
    const audio = new Audio(url)
    audioRef.value = audio
    audio.onended = () => { isPlaying.value = false; URL.revokeObjectURL(url) }
    audio.play()
  } catch {
    isPlaying.value = false
  }
}

async function sendText() {
  if (!inputText.value.trim()) return
  const query = inputText.value
  messages.value.push({ role: 'user', content: query })
  inputText.value = ''
  try {
    const res = await api.post('/chat/text', null, { params: { query, session_id: 'demo' } })
    messages.value.push({ role: 'assistant', content: res.data.answer })
  } catch {
    messages.value.push({ role: 'assistant', content: '[AI服务暂不可用]' })
  }
}

function handleVoiceResult(text: string) {
  inputText.value = text
  sendText()
}
</script>

<template>
  <div class="chat-layout">
    <header class="chat-header">
      <h1>景区智能导览</h1>
      <div class="header-actions" v-if="introText">
        <button class="play-btn" :class="{ playing: isPlaying }" @click="playIntro">
          {{ isPlaying ? '⏹ 停止' : '▶ 语音介绍' }}
        </button>
      </div>
    </header>
    <main class="chat-main">
      <div class="digital-human-area">
        <DigitalHuman :speaking="isPlaying" />
      </div>
      <div class="chat-area">
        <div class="messages">
          <div v-if="loading" class="welcome">加载中...</div>
          <ChatMessage v-for="(msg, idx) in messages" :key="idx" :role="msg.role" :content="msg.content" />
          <div v-if="!loading && messages.length === 1 && introName" class="demo-hint">
            <p>📢 正在为您介绍「{{ introName }}」</p>
          </div>
        </div>
        <div class="input-area">
          <input v-model="inputText" type="text" placeholder="输入您的问题，如：介绍一下这个景点" @keyup.enter="sendText" />
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
  background: linear-gradient(135deg, #1a73e8, #0d47a1);
  color: white;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chat-header h1 {
  margin: 0;
  font-size: 20px;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.play-btn {
  padding: 6px 16px;
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 20px;
  background: rgba(255,255,255,0.15);
  color: white;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.play-btn:hover { background: rgba(255,255,255,0.3); }
.play-btn.playing { background: #ef5350; border-color: #ef5350; }
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
.welcome, .demo-hint {
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
.input-area input:focus { border-color: #1a73e8; }
.input-area button {
  padding: 10px 20px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.input-area button:hover { background: #1557b0; }
</style>
