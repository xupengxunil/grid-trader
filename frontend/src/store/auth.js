/**
 * Auth store – persists token and user info in localStorage.
 */
import { ref, computed } from 'vue'

const TOKEN_KEY = 'grid_token'
const USER_KEY = 'grid_user'

export const token = ref(localStorage.getItem(TOKEN_KEY) || '')
export const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

export const isLoggedIn = computed(() => !!token.value)
export const isApproved = computed(() => user.value?.status === 'APPROVED')

export function setAuth(newToken, userInfo) {
  token.value = newToken
  user.value = userInfo
  localStorage.setItem(TOKEN_KEY, newToken)
  localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
}

export function clearAuth() {
  token.value = ''
  user.value = null
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}
