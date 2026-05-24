<script setup lang="ts">
import { ref } from 'vue'

const documents = ref<Array<{ id: string; filename: string }>>([])
const faqs = ref<Array<{ question: string; answer: string }>>([])
const newFaq = ref({ question: '', answer: '' })

function addFaq() {
  if (!newFaq.value.question.trim() || !newFaq.value.answer.trim()) return
  faqs.value.push({ ...newFaq.value })
  newFaq.value = { question: '', answer: '' }
}

function removeFaq(index: number) {
  faqs.value.splice(index, 1)
}
</script>

<template>
  <div class="knowledge">
    <h2>知识库管理</h2>

    <section class="section">
      <h3>文档管理</h3>
      <div class="upload-area">
        <input type="file" accept=".pdf,.docx,.md,.txt" />
        <button class="btn">上传</button>
      </div>
      <div v-if="documents.length" class="list">
        <div v-for="doc in documents" :key="doc.id" class="list-item">
          <span>{{ doc.filename }}</span>
          <button class="btn-danger">删除</button>
        </div>
      </div>
      <p v-else class="empty">暂无文档，请上传景区资料</p>
    </section>

    <section class="section">
      <h3>常见问答 (FAQ)</h3>
      <div class="faq-form">
        <input v-model="newFaq.question" placeholder="问题" />
        <input v-model="newFaq.answer" placeholder="答案" />
        <button class="btn" @click="addFaq">添加</button>
      </div>
      <div class="list">
        <div v-for="(faq, idx) in faqs" :key="idx" class="list-item">
          <div class="faq-content">
            <strong>Q: {{ faq.question }}</strong>
            <p>A: {{ faq.answer }}</p>
          </div>
          <button class="btn-danger" @click="removeFaq(idx)">删除</button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.knowledge h2 {
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
.upload-area {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.upload-area input {
  flex: 1;
}
.btn {
  padding: 8px 16px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.btn-danger {
  padding: 6px 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}
.faq-content strong {
  display: block;
  margin-bottom: 4px;
}
.faq-content p {
  margin: 0;
  color: #64748b;
}
.empty {
  color: #94a3b8;
  font-size: 14px;
}
.faq-form {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.faq-form input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}
</style>
