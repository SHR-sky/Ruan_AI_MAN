import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
})

export async function textChat(query: string, sessionId: string = 'default') {
  const res = await api.post('/chat/text', null, {
    params: { query, session_id: sessionId },
  })
  return res.data
}

export async function uploadDocument(file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/knowledge/documents/upload', form)
  return res.data
}

export async function searchKnowledge(query: string) {
  const res = await api.get('/knowledge/search', { params: { query } })
  return res.data
}

export default api
