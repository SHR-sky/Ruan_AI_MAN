<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

const props = defineProps<{ speaking?: boolean }>()

const isSpeaking = ref(false)

let currentRunId = 0

onUnmounted(() => {
  currentRunId++
  stopFallbackAudio()
})

async function playVoice(blob: Blob, runId: number) {
  currentRunId = runId
  isSpeaking.value = true
  await playAudioFallback(blob, runId)
}

function stopVoice() {
  currentRunId++
  stopFallbackAudio()
  isSpeaking.value = false
}

let fallbackAudio: HTMLAudioElement | null = null

async function playAudioFallback(blob: Blob, runId: number) {
  const url = URL.createObjectURL(blob)
  try {
    fallbackAudio = new Audio(url)
    await new Promise<void>((resolve, reject) => {
      if (!fallbackAudio) { resolve(); return }
      fallbackAudio.onended = () => resolve()
      fallbackAudio.onerror = () => reject()
      fallbackAudio.play().catch(reject)
    })
  } finally {
    if (runId === currentRunId) isSpeaking.value = false
    URL.revokeObjectURL(url)
  }
}

function stopFallbackAudio() {
  if (fallbackAudio) {
    fallbackAudio.pause()
    fallbackAudio.currentTime = 0
    fallbackAudio = null
  }
}

defineExpose({ playVoice, stopVoice, isSpeaking })
</script>

<template>
  <div class="digital-human-container">
    <div class="fallback-avatar">
      <div class="halo" :class="{ speaking: speaking || isSpeaking }"></div>
      <div class="avatar-card">
        <div class="avatar-circle" :class="{ speaking: speaking || isSpeaking }">
          <span>AI</span>
        </div>
        <p class="name">小导</p>
        <p class="status">{{ speaking || isSpeaking ? '正在语音导览' : '等待播放导览' }}</p>
        <div class="voice-bars" :class="{ active: speaking || isSpeaking }">
          <i></i><i></i><i></i><i></i><i></i>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.digital-human-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 330px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.fallback-avatar {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.halo {
  position: absolute;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: conic-gradient(from 120deg, #e2b45f, #6f9b72, #c6dfb4, #e2b45f);
  filter: blur(10px);
  opacity: 0.34;
}

.halo.speaking {
  animation: rotate 4s linear infinite;
}

.avatar-card {
  position: relative;
  width: 250px;
  padding: 28px 24px;
  border-radius: 32px;
  text-align: center;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(61, 82, 65, 0.14);
  box-shadow: 0 24px 60px rgba(49, 66, 50, 0.18);
}

.avatar-circle {
  width: 150px;
  height: 150px;
  border-radius: 44% 56% 48% 52%;
  background:
    radial-gradient(circle at 35% 25%, rgba(255,255,255,0.9), transparent 20%),
    linear-gradient(135deg, #294235, #6f9b72 52%, #d6ad61);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 18px;
}

.avatar-circle.speaking {
  animation: breathe 1.15s ease-in-out infinite;
}

.avatar-circle span {
  color: #fff8e8;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 52px;
  font-weight: 700;
}

.name {
  margin: 0;
  color: #20342b;
  font-size: 21px;
  font-weight: 800;
}

.status {
  margin: 6px 0 18px;
  color: #6c7968;
  font-size: 13px;
}

.voice-bars {
  display: flex;
  justify-content: center;
  gap: 5px;
  height: 26px;
}

.voice-bars i {
  width: 5px;
  height: 10px;
  border-radius: 999px;
  background: #9bad84;
  opacity: 0.45;
}

.voice-bars.active i {
  animation: bar 0.9s ease-in-out infinite;
}

.voice-bars.active i:nth-child(2) { animation-delay: 0.08s; }
.voice-bars.active i:nth-child(3) { animation-delay: 0.16s; }
.voice-bars.active i:nth-child(4) { animation-delay: 0.24s; }
.voice-bars.active i:nth-child(5) { animation-delay: 0.32s; }

@keyframes breathe {
  0%, 100% { transform: scale(1); border-radius: 44% 56% 48% 52%; }
  50% { transform: scale(1.05); border-radius: 52% 48% 56% 44%; }
}

@keyframes bar {
  0%, 100% { height: 9px; opacity: 0.35; }
  50% { height: 26px; opacity: 1; }
}

@keyframes rotate {
  to { transform: rotate(360deg); }
}
</style>
