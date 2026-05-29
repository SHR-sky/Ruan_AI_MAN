<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Application, Ticker } from 'pixi.js'
import { Config, Live2DSprite, Priority, LogLevel } from 'easy-live2d'

const props = defineProps<{ speaking?: boolean }>()

const wrapperRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const loaded = ref(false)
const webglFailed = ref(false)
const isSpeaking = ref(false)
const stageMetrics = ref({ width: 0, height: 0, left: 0, top: 0 })

Config.MotionGroupIdle = 'Idle'
Config.MouseFollow = false
Config.CubismLoggingLevel = LogLevel.LogLevel_Error

const STAGE_ASPECT = 0.76
const MODEL_PROFILE = {
  path: '/Resources/Mao/Mao.model3.json',
  x: 0.25,
  floorY: 0.9,
  fitHeight: 0.96,
  maxWidth: 0.7,
}

let app: Application | null = null
let sprite: Live2DSprite | null = null
let currentRunId = 0
let fallbackAudio: HTMLAudioElement | null = null
let activeSource: AudioBufferSourceNode | null = null
let activeAudioCtx: AudioContext | null = null
let resizeObserver: ResizeObserver | null = null

const stageStyle = computed(() => {
  const { width, height, left, top } = stageMetrics.value
  if (!width || !height) return {}
  return {
    width: `${width}px`,
    height: `${height}px`,
    transform: `translate(${left}px, ${top}px)`,
  }
})

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
      modelPath: MODEL_PROFILE.path,
      ticker: Ticker.shared,
    })

    sprite.anchor.set(0.5, 1)
    app.stage.addChild(sprite)
    updateSceneLayout()

    sprite.onLive2D('ready', () => {
      clearTimeout(timeout)
      loaded.value = true
      updateSceneLayout()
      sprite?.startRandomMotion({ group: 'Idle', priority: Priority.Idle })
    })

    if (wrapperRef.value) {
      resizeObserver = new ResizeObserver(() => {
        updateSceneLayout()
      })
      resizeObserver.observe(wrapperRef.value)
    }
  } catch (e) {
    clearTimeout(timeout)
    console.warn('[Live2D] init failed:', e)
    webglFailed.value = true
  }
})

onUnmounted(() => {
  currentRunId++
  resizeObserver?.disconnect()
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
      setLipSyncValue(0)
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
    setLipSyncValue(Math.min(rms * 3, 2.0))

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

  setLipSyncValue(0)
  audioCtx.close()
  activeSource = null
  activeAudioCtx = null
}

function stopVoice() {
  currentRunId++
  try { activeSource?.stop() } catch {}
  try { activeAudioCtx?.close() } catch {}
  setLipSyncValue(0)
  stopFallbackAudio()
  isSpeaking.value = false
}

function triggerExpression(name: string) {
  const expressions = sprite?.getExpressions?.() ?? []
  if (expressions.some((item: any) => item?.name === name)) {
    sprite?.setExpression({ expressionId: name })
    return
  }
  sprite?.setRandomExpression?.()
}

function setLipSyncValue(value: number) {
  sprite?.setParameterValueById('ParamMouthOpenY', value)
  sprite?.setParameterValueById('ParamA', value)
}

function updateSceneLayout() {
  if (!wrapperRef.value) return

  const rect = wrapperRef.value.getBoundingClientRect()
  if (!rect.width || !rect.height) return

  const horizontalPadding = Math.min(rect.width * 0.06, 32)
  const verticalPadding = Math.min(rect.height * 0.05, 28)
  const maxWidth = Math.max(rect.width - horizontalPadding * 2, 0)
  const maxHeight = Math.max(rect.height - verticalPadding * 2, 0)

  let stageWidth = maxWidth
  let stageHeight = stageWidth / STAGE_ASPECT

  if (stageHeight > maxHeight) {
    stageHeight = maxHeight
    stageWidth = stageHeight * STAGE_ASPECT
  }

  const left = (rect.width - stageWidth) / 2
  const top = (rect.height - stageHeight) / 2

  stageMetrics.value = { width: stageWidth, height: stageHeight, left, top }

  if (sprite) {
    const modelSize = sprite.getModelCanvasSize()
    const modelAspect = modelSize && modelSize.height > 0
      ? modelSize.width / modelSize.height
      : 0.72

    let drawHeight = stageHeight * MODEL_PROFILE.fitHeight
    const maxDrawWidth = stageWidth * MODEL_PROFILE.maxWidth
    let drawWidth = drawHeight * modelAspect

    if (drawWidth > maxDrawWidth) {
      drawWidth = maxDrawWidth
      drawHeight = drawWidth / modelAspect
    }

    sprite.height = drawHeight
    sprite.x = left + stageWidth * MODEL_PROFILE.x
    sprite.y = top + stageHeight * MODEL_PROFILE.floorY
  }
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
  <div class="live2d-wrapper" ref="wrapperRef" :class="{ speaking: props.speaking || isSpeaking }">
    <div class="scene-stage" :style="stageStyle">
      <div class="scene-grid"></div>
      <div class="scene-spotlight"></div>
      <div class="scene-arch"></div>
      <div class="scene-platform">
        <span class="platform-ring platform-ring-outer"></span>
        <span class="platform-ring platform-ring-inner"></span>
      </div>
      <div class="scene-foreground"></div>

      <canvas ref="canvasRef" class="live2d-canvas" />

      <div class="scene-status" :class="{ active: props.speaking || isSpeaking }">
        <span class="scene-status-label">导览状态</span>
        <strong>{{ props.speaking || isSpeaking ? '语音讲解中' : '数字人待命' }}</strong>
      </div>

      <div v-if="!loaded && !webglFailed" class="live2d-loading">
        <span class="dot-pulse"></span>
      </div>

      <div v-if="webglFailed" class="fallback-avatar">
        <div class="avatar-silhouette" :class="{ speaking: props.speaking || isSpeaking }">
          <div class="avatar-head"></div>
          <div class="avatar-body"></div>
        </div>
        <p class="fallback-name">小导</p>
        <div class="voice-bars" :class="{ active: props.speaking || isSpeaking }">
          <i></i><i></i><i></i><i></i><i></i>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.live2d-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 420px;
  overflow: hidden;
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.72) 0%, rgba(244, 248, 242, 0.76) 34%, rgba(224, 234, 222, 0.9) 100%),
    linear-gradient(135deg, #efe6d2 0%, #e6efe1 48%, #dbe3d8 100%);
  isolation: isolate;
}

.live2d-wrapper::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0) 24%),
    repeating-linear-gradient(90deg, rgba(76, 96, 80, 0.05) 0 1px, transparent 1px 74px);
  opacity: 0.85;
  pointer-events: none;
}

.live2d-wrapper::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 0%, rgba(40, 59, 49, 0.04) 58%, rgba(40, 59, 49, 0.1) 100%);
  pointer-events: none;
}

.scene-stage {
  position: absolute;
  left: 0;
  top: 0;
  overflow: hidden;
  border-radius: 34px 34px 40px 40px;
  border: 1px solid rgba(61, 82, 65, 0.12);
  background:
    linear-gradient(180deg, rgba(255, 253, 248, 0.92) 0%, rgba(246, 250, 245, 0.8) 42%, rgba(226, 236, 223, 0.92) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.72),
    0 24px 52px rgba(44, 61, 49, 0.12);
}

.scene-grid,
.scene-spotlight,
.scene-arch,
.scene-platform,
.scene-foreground,
.scene-status,
.live2d-loading,
.fallback-avatar,
.live2d-canvas {
  position: absolute;
}

.scene-grid {
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22), transparent 34%),
    repeating-linear-gradient(0deg, rgba(88, 108, 89, 0.06) 0 1px, transparent 1px 72px);
  opacity: 0.55;
  z-index: 0;
}

.scene-spotlight {
  left: 19%;
  right: 19%;
  top: 8%;
  bottom: 17%;
  background: linear-gradient(180deg, rgba(255, 236, 199, 0.6) 0%, rgba(255, 236, 199, 0.16) 56%, rgba(255, 236, 199, 0) 100%);
  clip-path: polygon(34% 0%, 66% 0%, 92% 100%, 8% 100%);
  z-index: 1;
}

.scene-arch {
  inset: 8% 13% 16%;
  border-radius: 220px 220px 36px 36px;
  border: 1px solid rgba(84, 105, 88, 0.16);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.32),
    inset 0 -28px 48px rgba(149, 172, 151, 0.12);
  z-index: 1;
}

.scene-platform {
  left: 16%;
  right: 16%;
  bottom: 7%;
  height: 22%;
  z-index: 2;
}

.platform-ring {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 50%;
}

.platform-ring-outer {
  width: 100%;
  height: 58%;
  bottom: 0;
  background:
    linear-gradient(180deg, rgba(202, 216, 197, 0.34) 0%, rgba(109, 133, 112, 0.24) 100%);
  border: 1px solid rgba(82, 103, 86, 0.16);
}

.platform-ring-inner {
  width: 72%;
  height: 34%;
  bottom: 16%;
  border: 1px solid rgba(255, 255, 255, 0.75);
  background: rgba(255, 255, 255, 0.2);
}

.live2d-canvas {
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  z-index: 4;
}

.scene-foreground {
  left: 0;
  right: 0;
  bottom: 0;
  height: 34%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, rgba(232, 239, 229, 0.56) 42%, rgba(219, 230, 217, 0.9) 100%);
  z-index: 5;
  pointer-events: none;
}

.live2d-loading {
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 6;
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

.scene-status {
  left: 20px;
  top: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(61, 82, 65, 0.1);
  backdrop-filter: blur(10px);
  z-index: 7;
  box-shadow: 0 16px 32px rgba(43, 60, 47, 0.1);
}

.scene-status-label {
  color: #6e7b69;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.scene-status strong {
  color: #20342b;
  font-size: 14px;
}

.scene-status.active {
  border-color: rgba(182, 70, 50, 0.18);
  box-shadow: 0 18px 36px rgba(182, 70, 50, 0.12);
}

.fallback-avatar {
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding-bottom: 18%;
  z-index: 6;
}

.avatar-silhouette {
  position: relative;
  width: 180px;
  height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-head,
.avatar-body {
  position: absolute;
  background: linear-gradient(180deg, #48634f 0%, #6f8f73 100%);
  box-shadow: 0 16px 32px rgba(39, 55, 44, 0.16);
}

.avatar-head {
  top: 18px;
  width: 76px;
  height: 76px;
  border-radius: 50%;
}

.avatar-body {
  bottom: 0;
  width: 156px;
  height: 184px;
  border-radius: 88px 88px 44px 44px;
}

.avatar-silhouette.speaking {
  animation: breathe 1.15s ease-in-out infinite;
}

.fallback-name {
  margin: 16px 0 6px;
  color: #20342b;
  font-size: 20px;
  font-weight: 800;
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
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-4px) scale(1.03); }
}

@keyframes bar {
  0%, 100% { height: 9px; opacity: 0.35; }
  50% { height: 26px; opacity: 1; }
}
</style>
