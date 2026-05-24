<script setup lang="ts">
import { ref } from 'vue'

const config = ref({
  name: '小导',
  gender: 'female',
  voice_type: 'default',
})

function saveConfig() {
  // 待接入API
}
</script>

<template>
  <div class="dh-config">
    <h2>数字人配置</h2>

    <section class="section">
      <h3>基本信息</h3>
      <div class="form-group">
        <label>名称</label>
        <input v-model="config.name" />
      </div>
      <div class="form-group">
        <label>性别</label>
        <select v-model="config.gender">
          <option value="female">女性</option>
          <option value="male">男性</option>
        </select>
      </div>
      <div class="form-group">
        <label>声音类型</label>
        <select v-model="config.voice_type">
          <option value="default">默认</option>
          <option value="gentle">温柔</option>
          <option value="lively">活泼</option>
          <option value="professional">专业</option>
        </select>
      </div>
      <button class="btn" @click="saveConfig">保存配置</button>
    </section>

    <section class="section">
      <h3>形象管理</h3>
      <div class="appearance-preview">
        <div class="preview-box">
          <span>待上传形象</span>
        </div>
      </div>
      <input type="file" accept="image/*,video/*" />
      <button class="btn" style="margin-top: 12px">上传形象</button>
    </section>
  </div>
</template>

<style scoped>
.dh-config h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: #1e293b;
}
.section {
  background: white;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.section h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #1e293b;
}
.form-group {
  margin-bottom: 14px;
}
.form-group label {
  display: block;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
}
.form-group input,
.form-group select {
  width: 100%;
  max-width: 360px;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}
.btn {
  padding: 8px 16px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 8px;
}
.appearance-preview {
  margin-bottom: 12px;
}
.preview-box {
  width: 200px;
  height: 240px;
  border: 2px dashed #e2e8f0;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 14px;
  background: #f8fafc;
}
</style>
