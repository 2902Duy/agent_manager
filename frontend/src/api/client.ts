import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
})

// ===== Agents =====
export const fetchAgents = () => api.get('/agents').then(r => r.data)
export const fetchAgent = (name: string) => api.get(`/agents/${name}`).then(r => r.data)
export const createAgent = (name: string, data: Record<string, unknown>) =>
  api.post(`/agents?name=${encodeURIComponent(name)}`, data).then(r => r.data)
export const updateAgent = (name: string, data: Record<string, unknown>) =>
  api.put(`/agents/${name}`, data).then(r => r.data)
export const deleteAgent = (name: string) => api.delete(`/agents/${name}`).then(r => r.data)
export const toggleAgent = (name: string) => api.patch(`/agents/${name}/toggle`).then(r => r.data)

// ===== Tools =====
export const fetchTools = () => api.get('/tools').then(r => r.data)

// ===== Crew =====
export const runCrew = (data: Record<string, unknown>) =>
  api.post('/crew/run', data).then(r => r.data)
export const getCrewStatus = (sessionId: string) =>
  api.get(`/crew/status/${sessionId}`).then(r => r.data)
export const fetchSessions = () => api.get('/crew/sessions').then(r => r.data)

// ===== Outputs =====
export const fetchOutputs = () => api.get('/outputs').then(r => r.data)
export const getOutputUrl = (filename: string) => `${API_BASE}/api/outputs/${filename}`

// ===== Trace =====
export const fetchTraces = () => api.get('/trace').then(r => r.data)
export const fetchTrace = (sessionId: string) => api.get(`/trace/${sessionId}`).then(r => r.data)

export default api
