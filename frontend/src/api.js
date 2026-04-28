const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_SECRET = import.meta.env.VITE_API_SECRET || ''

function authHeaders() {
  return API_SECRET ? { 'X-API-Key': API_SECRET } : {}
}

async function handle(res) {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {}
    throw new Error(detail)
  }
  return res.json()
}

export async function uploadManual(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${API_URL}/api/manuals`, {
    method: 'POST',
    headers: authHeaders(),
    body: fd,
  })
  return handle(res)
}

export async function askQuestion({ manualId, question, image, history = [] }) {
  const fd = new FormData()
  fd.append('manual_id', manualId)
  fd.append('question', question)
  fd.append('history', JSON.stringify(history))
  if (image) fd.append('image', image)
  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body: fd,
  })
  return handle(res)
}

export async function checkHealth() {
  const res = await fetch(`${API_URL}/api/health`, { headers: authHeaders() })
  return handle(res)
}

export { API_URL }
