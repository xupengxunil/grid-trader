import axios from 'axios'
import { token, clearAuth } from '../store/auth.js'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach token to every request
http.interceptors.request.use((config) => {
  if (token.value) {
    config.headers['Authorization'] = `Token ${token.value}`
  }
  return config
})

// Redirect to login on 401
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuth()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authRegister = (data) => http.post('/auth/register/', data)
export const authLogin = (data) => http.post('/auth/login/', data)
export const authLogout = () => http.post('/auth/logout/')
export const authMe = () => http.get('/auth/me/')

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
