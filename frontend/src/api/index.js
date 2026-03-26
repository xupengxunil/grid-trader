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
export const updatePlan = (id, data) => http.patch(`/plans/${id}/`, data)

// ── Records ──────────────────────────────────────────────────────────────────
export const executeBuy = (recordId, price) =>
  http.post(`/records/${recordId}/buy/`, { price })

export const executeSell = (recordId, price) =>
  http.post(`/records/${recordId}/sell/`, { price })

export const restartRecord = (recordId) =>
  http.post(`/records/${recordId}/restart/`)

// ── Statistics ───────────────────────────────────────────────────────────────
export const getStatistics = (params) => http.get('/statistics/', { params })

// ── Quotes ───────────────────────────────────────────────────────────────────
export const getQuotes = (codes) => http.get('/quotes/', { params: { codes } })
export const searchStocks = (keyword) => http.get('/search/', { params: { keyword } })

// ── K-Line ───────────────────────────────────────────────────────────────────
export const getKLine = (symbol, scale = 60, datalen = 100) => 
  http.get('/kline/', { params: { symbol, scale, datalen } })



// Watchlist
export const getWatchlist = () => http.get('/watchlist/')
export const addWatchlist = (data) => http.post('/watchlist/', data)
export const deleteWatchlist = (code) => http.delete(`/watchlist/${code}/`)


export default http