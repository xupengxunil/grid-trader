import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Plans ────────────────────────────────────────────────────────────────────
export const getPlans = () => http.get('/plans/')
export const createPlan = (data) => http.post('/plans/', data)
export const getPlan = (id) => http.get(`/plans/${id}/`)
export const deletePlan = (id) => http.delete(`/plans/${id}/`)

// ── Records ──────────────────────────────────────────────────────────────────
export const executeBuy = (recordId, price) =>
  http.post(`/records/${recordId}/buy/`, { price })

export const executeSell = (recordId, price) =>
  http.post(`/records/${recordId}/sell/`, { price })

// ── Statistics ───────────────────────────────────────────────────────────────
export const getStatistics = (params) => http.get('/statistics/', { params })

export default http
