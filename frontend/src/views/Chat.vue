<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import DigitalHuman from '../components/DigitalHuman.vue'
import ChatMessage from '../components/ChatMessage.vue'
import VoiceInput from '../components/VoiceInput.vue'
import api from '../api'

type Message = { role: string; content: string }

const messages = ref<Message[]>([])
const inputText = ref('')
const introText = ref('')
const introName = ref('')
const introType = ref('')
const audioUrl = ref('')
const isPlaying = ref(false)
const loading = ref(true)
const audioLoading = ref(false)
const autoplayBlocked = ref(false)
const audioError = ref('')
const audioRef = ref<HTMLAudioElement | null>(null)
const ttsDevice = ref('')
let speechRunId = 0
const dhRef = ref<any>(null)

onMounted(async () => {
  await loadIntro()
})

onBeforeUnmount(() => {
  stopAudio()
})

async function loadIntro() {
  loading.value = true
  try {
    const res = await api.get('/demo/intro')
    introName.value = res.data.name
    introType.value = res.data.type
    introText.value = res.data.intro_text || res.data.full_text || ''
    audioUrl.value = res.data.audio_url || '/api/v1/demo/intro/audio?voice_type=female'
    ttsDevice.value = res.data.tts_status?.gpu_name || res.data.tts_status?.runtime_device || ''
    messages.value.push({
      role: 'assistant',
      content: `${introText.value}`,
    })
    await nextTick()
    await playIntro(true)
  } catch {
    messages.value.push({ role: 'assistant', content: '您好！我是AI导游，后端服务暂不可用。' })
  } finally {
    loading.value = false
  }
}

function stopAudio() {
  speechRunId += 1
  if (audioRef.value) {
    audioRef.value.pause()
    audioRef.value.currentTime = 0
  }
  dhRef.value?.stopVoice()
  isPlaying.value = false
}

async function playAudioSource(source: string, fromAutoplay = false) {
  if (!source) return
  if (isPlaying.value) {
    stopAudio()
  }

  audioLoading.value = true
  audioError.value = ''
  autoplayBlocked.value = false

  try {
    const audio = audioRef.value ?? new Audio()
    audioRef.value = audio
    audio.preload = 'auto'
    audio.src = source
    audio.onplaying = () => {
      isPlaying.value = true
      audioLoading.value = false
    }
    audio.onended = () => {
      isPlaying.value = false
      audioLoading.value = false
    }
    audio.onerror = () => {
      isPlaying.value = false
      audioLoading.value = false
      audioError.value = '导览音频加载失败，请确认后端 TTS 服务已启动。'
    }

    await audio.play()
  } catch (error) {
    isPlaying.value = false
    audioLoading.value = false
    if (fromAutoplay) {
      autoplayBlocked.value = true
      audioError.value = '浏览器阻止了自动有声播放，请点击“播放导览”。'
      return
    }
    audioError.value = '播放失败，请稍后重试。'
  }
}

async function playIntro(fromAutoplay = false) {
  if (!audioUrl.value) return
  const source = `${audioUrl.value}${audioUrl.value.includes('?') ? '&' : '?'}t=${Date.now()}`
  await playAudioSource(source, fromAutoplay)
}

async function playAssistantAnswer(text: string) {
  const speechText = normalizeSpeechText(text)
  if (!speechText) return

  const runId = ++speechRunId
  try {
    audioError.value = ''
    if (isPlaying.value) {
      stopAudio()
    }
    audioLoading.value = true
    const res = await api.post(
      '/tts/synthesize-file',
      { text: speechText, voice_type: 'female' },
      { responseType: 'blob' },
    )
    if (runId !== speechRunId) return
    audioLoading.value = false
    isPlaying.value = true
    await dhRef.value?.playVoice(res.data, runId)
  } catch {
    audioError.value = '回答语音生成失败，请确认后端 TTS 服务可用。'
  } finally {
    if (runId === speechRunId) {
      isPlaying.value = false
      audioLoading.value = false
    }
  }
}

function normalizeSpeechText(text: string) {
  return text.replace(/\s+/g, ' ').trim()
}

async function sendText() {
  if (!inputText.value.trim()) return
  const query = inputText.value
  messages.value.push({ role: 'user', content: query })
  inputText.value = ''
  try {
    const res = await api.post('/chat/text', null, { params: { query, session_id: 'demo' } })
    const answer = res.data.answer || ''
    messages.value.push({ role: 'assistant', content: answer })
    dhRef.value?.triggerExpression?.('smile')
    await playAssistantAnswer(answer)
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
      <div>
        <p class="eyebrow">Scenic Guide AI</p>
        <h1>景区智能导览语音 Demo</h1>
      </div>
      <div class="header-actions" v-if="introText">
        <span v-if="ttsDevice" class="device-badge" :class="{ cuda: ttsDevice.includes('NVIDIA') || ttsDevice.includes('VRAM') }">{{ ttsDevice }}</span>
        <button class="play-btn" :class="{ playing: isPlaying }" :disabled="audioLoading" @click="isPlaying ? stopAudio() : playIntro(false)">
          {{ audioLoading ? '生成语音中...' : isPlaying ? '停止播放' : '播放导览' }}
        </button>
      </div>
    </header>

    <main class="chat-main">
      <section class="digital-human-area">
        <DigitalHuman ref="dhRef" :speaking="isPlaying" />
        <div class="guide-card">
          <span class="tag">{{ introType || '知识库导览' }}</span>
          <h2>{{ introName || '正在加载景点' }}</h2>
          <p>{{ introText || '正在从本地知识库生成导览词。' }}</p>
          <div v-if="autoplayBlocked || audioError" class="audio-alert">
            {{ audioError }}
          </div>
        </div>
      </section>

      <section class="chat-area">
        <div class="messages">
          <div v-if="loading" class="welcome">正在加载导览服务...</div>
          <ChatMessage v-for="(msg, idx) in messages" :key="idx" :role="msg.role" :content="msg.content" @play="playAssistantAnswer(msg.content)" />
        </div>
        <div class="input-area">
          <input v-model="inputText" type="text" placeholder="输入您的问题，如：推荐一条亲子游路线" @keyup.enter="sendText" />
          <button @click="sendText">发送</button>
          <VoiceInput @result="handleVoiceResult" />
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 18%, rgba(255, 205, 120, 0.55), transparent 28%),
    radial-gradient(circle at 92% 10%, rgba(70, 155, 130, 0.28), transparent 32%),
    linear-gradient(135deg, #f7efe0 0%, #eef4e8 45%, #dfe9dd 100%);
  color: #20342b;
}

.chat-header {
  padding: 18px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(58, 80, 64, 0.14);
  backdrop-filter: blur(14px);
}

.eyebrow {
  margin: 0 0 4px;
  color: #6f7d57;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.chat-header h1 {
  margin: 0;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 26px;
  letter-spacing: 0.02em;
}

.play-btn {
  min-width: 132px;
  padding: 10px 18px;
  border: 0;
  border-radius: 999px;
  background: #20342b;
  color: #fff8ec;
  cursor: pointer;
  font-weight: 700;
  box-shadow: 0 12px 28px rgba(32, 52, 43, 0.22);
}

.play-btn:disabled {
  cursor: wait;
  opacity: 0.76;
}

.play-btn.playing {
  background: #b64632;
}

.device-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: #e8e8e8;
  color: #555;
  margin-right: 10px;
  white-space: nowrap;
}
.device-badge.cuda {
  background: #76b900;
  color: #fff;
}

.chat-main {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(360px, 0.92fr) minmax(420px, 1.08fr);
  grid-template-rows: 1fr;
  gap: 22px;
  padding: 22px;
  overflow: hidden;
}

.digital-human-area,
.chat-area {
  min-height: 0;
  border: 1px solid rgba(58, 80, 64, 0.14);
  border-radius: 28px;
  background: rgba(255, 252, 244, 0.72);
  box-shadow: 0 22px 70px rgba(55, 74, 54, 0.14);
}

.digital-human-area {
  display: grid;
  grid-template-rows: 1fr auto;
  overflow: hidden;
}

.guide-card {
  margin: 0 22px 22px;
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(58, 80, 64, 0.12);
}

.tag {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: #dbe8ce;
  color: #50623b;
  font-size: 12px;
  font-weight: 700;
}

.guide-card h2 {
  margin: 12px 0 8px;
  font-size: 24px;
}

.guide-card p {
  margin: 0;
  color: #526257;
  line-height: 1.7;
}

.audio-alert {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff0d6;
  color: #8a4b12;
  font-size: 13px;
}

.chat-area {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
}

.welcome {
  padding: 16px;
  color: #6b765f;
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 16px;
  border-top: 1px solid rgba(58, 80, 64, 0.12);
  background: rgba(255, 255, 255, 0.62);
}

.input-area input {
  flex: 1;
  padding: 12px 14px;
  border: 1px solid rgba(58, 80, 64, 0.2);
  border-radius: 14px;
  background: #fffdf8;
  font-size: 14px;
  outline: none;
}

.input-area input:focus {
  border-color: #5f7f4e;
  box-shadow: 0 0 0 3px rgba(95, 127, 78, 0.12);
}

.input-area button {
  padding: 12px 18px;
  background: #5f7f4e;
  color: white;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font-weight: 700;
}

@media (max-width: 860px) {
  .chat-main {
    grid-template-columns: 1fr;
    overflow: auto;
  }

  .digital-human-area {
    min-height: 520px;
  }
}
</style>
