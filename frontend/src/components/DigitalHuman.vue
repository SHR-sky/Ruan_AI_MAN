<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Application, Ticker } from 'pixi.js'
import { Config, Live2DSprite, Priority, LogLevel } from 'easy-live2d'

const props = defineProps<{ speaking?: boolean }>()

const wrapperRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const loaded = ref(false)
const webglFailed = ref(false)
const isSpeaking = ref(false)

let app: Application | null = null
let sprite: Live2DSprite | null = null
let currentRunId = 0
let fallbackAudio: HTMLAudioElement | null = null

onMounted(async () => {
  await nextTick()
  console.log('[Live2D] mount start, wrapper size:', wrapperRef.value?.clientWidth, 'x', wrapperRef.value?.clientHeight)

  const timeout = setTimeout(() => {
    if (!loaded.value) {
      console.warn('[Live2D] model load timeout (10s), using CSS fallback')
      webglFailed.value = true
    }
  }, 10000)

  try {
    console.log('[Live2D] setting Config...')
    Config.MotionGroupIdle = 'Idle'
    Config.MouseFollow = false
    Config.CubismLoggingLevel = LogLevel.LogLevel_Error

    console.log('[Live2D] creating Pixi Application...')
    app = new Application()
    await app.init({
      canvas: canvasRef.value!,
      backgroundAlpha: 0,
      autoDensity: true,
      antialias: true,
      resolution: Math.min(window.devicePixelRatio || 1, 2),
      resizeTo: wrapperRef.value!,
    })
    console.log('[Live2D] Pixi app init done, canvas:', canvasRef.value?.clientWidth, 'x', canvasRef.value?.clientHeight)

    console.log('[Live2D] creating Live2DSprite...')
    sprite = new Live2DSprite({
      modelPath: '/Resources/Hiyori/Hiyori.model3.json',
      ticker: Ticker.shared,
    })

    sprite.anchor.set(0.5, 1)
    sprite.x = canvasRef.value!.clientWidth / 2
    sprite.y = canvasRef.value!.clientHeight
    sprite.width = canvasRef.value!.clientWidth * 1.2
    console.log('[Live2D] sprite created, waiting for ready...')

    app.stage.addChild(sprite)

    sprite.onLive2D('ready', () => {
      clearTimeout(timeout)
      loaded.value = true
      console.log('[Live2D] MODEL READY!')
      sprite?.startRandomMotion({ group: 'Idle', priority: Priority.Idle })
    })

    sprite.onLive2D('hit', async ({ hitAreaName }) => {
      if (hitAreaName === 'Body') {
        await sprite?.startMotion({ group: 'TapBody', no: 0, priority: Priority.Normal })
      }
    })
  } catch (e) {
    clearTimeout(timeout)
    console.warn('[Live2D] init failed, using CSS fallback:', e)
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
  const url = URL.createObjectURL(blob)

  if (sprite && loaded.value && !webglFailed.value) {
    try {
      isSpeaking.value = true
      await sprite.playVoice({ voicePath: url, immediate: true })
    } finally {
      if (runId === currentRunId) isSpeaking.value = false
      URL.revokeObjectURL(url)
    }
  } else {
    try {
      isSpeaking.value = true
      await playAudioFallback(url, runId)
    } finally {
      if (runId === currentRunId) isSpeaking.value = false
      URL.revokeObjectURL(url)
    }
  }
}

function stopVoice() {
  currentRunId++
  sprite?.stopVoice()
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
    <canvas ref="canvasRef" v-show="loaded && !webglFailed" class="live2d-canvas" />

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
      loaded={{ loaded }} webglFailed={{ webglFailed }} wrapper={{ wrapperRef?.clientWidth }}x{{ wrapperRef?.clientHeight }} canvas={{ canvasRef?.clientWidth }}x{{ canvasRef?.clientHeight }}
    </div>
  </div>
</template>

<style scoped>
.live2d-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 330px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.live2d-canvas {
  width: 100%;
  height: 100%;
  display: block;
  background: rgba(255, 0, 0, 0.05);
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
  white-space: nowrap;
}

.dot-pulse {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #6f9b72;
  animation: dotPulse 1.2s ease-in-out infinite;
}

@keyframes dotPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* ---- CSS fallback ---- */
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
