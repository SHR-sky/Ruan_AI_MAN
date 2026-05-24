import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

export async function getDashboard() {
  return api.get('/admin/dashboard')
}

export async function uploadDocument(file: File) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/knowledge/documents/upload', form)
}

export async function addFaq(question: string, answer: string) {
  return api.post('/knowledge/faq', null, { params: { question, answer } })
}

export async function getDigitalHumanConfig() {
  return api.get('/digital-human/config')
}

export async function updateDigitalHumanConfig(config: any) {
  return api.post('/digital-human/config', null, { params: config })
}

export default api
