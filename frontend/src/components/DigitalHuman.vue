<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Application, Ticker } from 'pixi.js'
import { Config, Live2DSprite, Priority, LogLevel } from 'easy-live2d'

const props = defineProps<{ speaking?: boolean }>()

const wrapperRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const loaded = ref(false)
const webglFailed = ref(false)
const isSpeaking = ref(false)

Config.MotionGroupIdle = 'Idle'
Config.MouseFollow = false
Config.CubismLoggingLevel = LogLevel.LogLevel_Error

let app: Application | null = null
let sprite: Live2DSprite | null = null
let currentRunId = 0
let fallbackAudio: HTMLAudioElement | null = null
let activeSource: AudioBufferSourceNode | null = null
let activeAudioCtx: AudioContext | null = null

onMounted(async () => {
  if (!canvasRef.value) return

  const timeout = setTimeout(() => {
    if (!loaded.value) {
      webglFailed.value = true
    }
  }, 10000)

  try {
    app = new Application()
    await app.init({
      canvas: canvasRef.value,
      backgroundAlpha: 0,
      autoDensity: true,
      resolution: Math.max(window.devicePixelRatio || 1, 1),
      resizeTo: wrapperRef.value!,
    })

    sprite = new Live2DSprite({
      modelPath: '/Resources/Hiyori/Hiyori.model3.json',
      ticker: Ticker.shared,
    })

    sprite.width = canvasRef.value.clientWidth
    app.stage.addChild(sprite)

    sprite.onLive2D('ready', () => {
      clearTimeout(timeout)
      loaded.value = true
      sprite?.startRandomMotion({ group: 'Idle', priority: Priority.Idle })
    })
  } catch (e) {
    clearTimeout(timeout)
    console.warn('[Live2D] init failed:', e)
    webglFailed.value = true
  }
})

onUnmounted(() => {
  currentRunId++
  stopFallbackAudio()
  sprite?.destroy()
  if (app) {
    app.destroy(true, { children: true })
    app = null
  }
})

async function playVoice(blob: Blob, runId: number) {
  currentRunId = runId

  if (!sprite || !loaded.value || webglFailed.value) {
    const url = URL.createObjectURL(blob)
    try {
      isSpeaking.value = true
      await playAudioFallback(url, runId)
    } finally {
      if (runId === currentRunId) isSpeaking.value = false
      URL.revokeObjectURL(url)
    }
    return
  }

  try {
    isSpeaking.value = true
    await playWithManualLipSync(blob, runId)
  } finally {
    if (runId === currentRunId) {
      isSpeaking.value = false
      sprite?.setParameterValueById('ParamMouthOpenY', 0)
    }
  }
}

async function playWithManualLipSync(blob: Blob, runId: number) {
  const audioCtx = new AudioContext()
  activeAudioCtx = audioCtx
  const arrayBuffer = await blob.arrayBuffer()
  const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer)

  const source = audioCtx.createBufferSource()
  activeSource = source
  source.buffer = audioBuffer

  const analyser = audioCtx.createAnalyser()
  analyser.fftSize = 256
  source.connect(analyser)
  analyser.connect(audioCtx.destination)

  const dataArray = new Uint8Array(analyser.frequencyBinCount)
  let animId = 0

  const animate = () => {
    if (runId !== currentRunId) return
    analyser.getByteTimeDomainData(dataArray)

    let sum = 0
    for (let i = 0; i < dataArray.length; i++) {
      const v = (dataArray[i] - 128) / 128
      sum += v * v
    }
    const rms = Math.sqrt(sum / dataArray.length)
    sprite?.setParameterValueById('ParamMouthOpenY', Math.min(rms * 3, 2.0))

    animId = requestAnimationFrame(animate)
  }

  source.start()
  animate()

  await new Promise<void>((resolve) => {
    source.onended = () => {
      cancelAnimationFrame(animId)
      resolve()
    }
  })

  sprite?.setParameterValueById('ParamMouthOpenY', 0)
  audioCtx.close()
  activeSource = null
  activeAudioCtx = null
}

function stopVoice() {
  currentRunId++
  try { activeSource?.stop() } catch {}
  try { activeAudioCtx?.close() } catch {}
  sprite?.setParameterValueById('ParamMouthOpenY', 0)
  stopFallbackAudio()
  isSpeaking.value = false
}

function triggerExpression(name: string) {
  sprite?.setExpression({ expressionId: name })
}

async function playAudioFallback(url: string, runId: number) {
  fallbackAudio = new Audio(url)
  await new Promise<void>((resolve, reject) => {
    if (!fallbackAudio) { resolve(); return }
    fallbackAudio.onended = () => resolve()
    fallbackAudio.onerror = () => reject()
    fallbackAudio.play().catch(reject)
  })
}

function stopFallbackAudio() {
  if (fallbackAudio) {
    fallbackAudio.pause()
    fallbackAudio.currentTime = 0
    fallbackAudio = null
  }
}

defineExpose({ playVoice, stopVoice, isSpeaking, triggerExpression })
</script>

<template>
  <div class="live2d-wrapper" ref="wrapperRef">
    <canvas ref="canvasRef" class="live2d-canvas" />

    <div v-if="!loaded && !webglFailed" class="live2d-loading">
      <span class="dot-pulse"></span>
      <span class="debug-label">Live2D 加载中...</span>
    </div>

    <div v-if="webglFailed" class="fallback-avatar">
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

    <div class="debug-status">
      loaded={{ loaded }} webglFailed={{ webglFailed }} w={{ wrapperRef?.clientWidth }}x{{ wrapperRef?.clientHeight }} c={{ canvasRef?.clientWidth }}x{{ canvasRef?.clientHeight }}
    </div>
  </div>
</template>

<style scoped>
.live2d-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 330px;
  overflow: hidden;
}

.live2d-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.live2d-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.dot-pulse {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #6f9b72;
  animation: dotPulse 1.2s ease-in-out infinite;
}

.debug-label {
  font-size: 12px;
  color: #888;
}

.debug-status {
  position: absolute;
  bottom: 4px;
  left: 4px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: #0f0;
  font-size: 10px;
  font-family: monospace;
  z-index: 10;
}

@keyframes dotPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* ---- CSS fallback ---- */
.fallback-avatar {
  position: absolute;
  inset: 0;
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
