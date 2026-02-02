import axios from 'axios'
import { apiBaseURL } from '../config/apiConfig'

const ACCESS_TOKEN_KEY = 'drillquiz.access'
const REFRESH_TOKEN_KEY = 'drillquiz.refresh'
const ACCESS_EXPIRES_AT_KEY = 'drillquiz.access.expiresAt'
const REFRESH_EXPIRES_AT_KEY = 'drillquiz.refresh.expiresAt'
const USER_KEY = 'drillquiz.user'
const DEFAULT_ACCESS_TOKEN_TTL = 30 * 60 // 30 minutes
const DEFAULT_REFRESH_TOKEN_TTL = 7 * 24 * 60 * 60 // 7 days
const LEGACY_USER_KEY = 'user'
const LEGACY_TOKEN_KEY = 'token'
const isBrowserEnv = typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'

const decodeJwt = (token) => {
  if (!token || typeof token !== 'string') {
    return null
  }
  try {
    const base64 = token.split('.')[1]
    if (!base64) {
      return null
    }
    if (typeof atob === 'function') {
      return JSON.parse(decodeURIComponent(escape(atob(base64.replace(/-/g, '+').replace(/_/g, '/')))))
    }
    // Node.js fallback
    return JSON.parse(
      Buffer.from(base64.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf-8')
    )
  } catch (error) {
    console.warn('[authService] failed to decode JWT', error)
    return null
  }
}

const enrichUserWithToken = (user, token) => {
  const payload = decodeJwt(token)
  if (!payload) {
    return user
  }
  const enriched = { ...(user || {}) }
  if (!enriched.username && payload.username) {
    enriched.username = payload.username
  }
  if (!enriched.email && payload.email) {
    enriched.email = payload.email
  }
  if (!enriched.id && payload.user_id) {
    enriched.id = payload.user_id
  }
  if (!enriched.is_superuser && typeof payload.is_superuser === 'boolean') {
    enriched.is_superuser = payload.is_superuser
  }
  if (!enriched.is_staff && typeof payload.is_staff === 'boolean') {
    enriched.is_staff = payload.is_staff
  }
  // role 정보 추가 (JWT 토큰에 포함된 경우)
  if (!enriched.role && payload.role) {
    enriched.role = payload.role
  }
  // language 정보 추가 (JWT 토큰에 포함된 경우)
  if (!enriched.language && payload.language) {
    enriched.language = payload.language
  }
  return enriched
}

const storage = {
  async set(key, value) {
    localStorage.setItem(key, value)
  },
  async get(key) {
    return localStorage.getItem(key)
  },
  async remove(key) {
    localStorage.removeItem(key)
  },
  async clear(keys) {
    await Promise.all(keys.map(key => this.remove(key)))
  }
}

let cachedUser = null
let cachedAccessToken = null
let cachedRefreshToken = null
let hydrationAttempted = false
const subscribers = new Set()

const cloneUser = (user) => {
  if (!user) {
    return null
  }
  try {
    return JSON.parse(JSON.stringify(user))
  } catch (error) {
    return { ...user }
  }
}

const safeParseJSON = (value) => {
  if (typeof value !== 'string' || value.trim() === '') {
    return null
  }
  try {
    return JSON.parse(value)
  } catch (error) {
    return null
  }
}

const hydrateFromBrowserStorage = () => {
  if (hydrationAttempted) {
    return
  }
  hydrationAttempted = true
  if (!isBrowserEnv) {
    return
  }

  try {
    const rawUser =
      window.localStorage.getItem(USER_KEY) ||
      window.localStorage.getItem(LEGACY_USER_KEY)
    cachedUser = safeParseJSON(rawUser)
  } catch (error) {
    cachedUser = null
  }

  try {
    cachedAccessToken =
      window.localStorage.getItem(ACCESS_TOKEN_KEY) ||
      window.localStorage.getItem(LEGACY_TOKEN_KEY) ||
      null
  } catch (error) {
    cachedAccessToken = null
  }

  try {
    cachedRefreshToken = window.localStorage.getItem(REFRESH_TOKEN_KEY) || null
  } catch (error) {
    cachedRefreshToken = null
  }
}

const notifyAuthSubscribers = () => {
  if (!subscribers.size) {
    return
  }
  const snapshot = getAuthSnapshot()
  subscribers.forEach((handler) => {
    try {
      handler(snapshot)
    } catch (error) {
      console.error('[authService] subscriber error', error)
    }
  })
}

const setCachedUser = (user) => {
  cachedUser = user ? cloneUser(user) : null
  if (isBrowserEnv) {
    if (cachedUser) {
      window.localStorage.setItem(USER_KEY, JSON.stringify(cachedUser))
      window.localStorage.setItem(LEGACY_USER_KEY, JSON.stringify(cachedUser))
    } else {
      window.localStorage.removeItem(USER_KEY)
      window.localStorage.removeItem(LEGACY_USER_KEY)
    }
  }
  notifyAuthSubscribers()
}

const setCachedAccessToken = (token) => {
  cachedAccessToken = token || null
  if (isBrowserEnv) {
    if (cachedAccessToken) {
      window.localStorage.setItem(ACCESS_TOKEN_KEY, cachedAccessToken)
      window.localStorage.setItem(LEGACY_TOKEN_KEY, 'jwt')
    } else {
      window.localStorage.removeItem(ACCESS_TOKEN_KEY)
      window.localStorage.removeItem(LEGACY_TOKEN_KEY)
    }
  }
  notifyAuthSubscribers()
}

const setCachedRefreshToken = (token) => {
  cachedRefreshToken = token || null
  if (isBrowserEnv) {
    if (cachedRefreshToken) {
      window.localStorage.setItem(REFRESH_TOKEN_KEY, cachedRefreshToken)
    } else {
      window.localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
  }
}

const getCachedUser = () => {
  if (!hydrationAttempted) {
    hydrateFromBrowserStorage()
  }
  return cachedUser ? cloneUser(cachedUser) : null
}

const getAuthSnapshot = () => ({
  user: getCachedUser(),
  isAuthenticated: isAuthenticatedSync(),
  isAdmin: isAdminSync()
})

const isAuthenticatedSync = () => {
  const user = getCachedUser()
  if (user) {
    return true
  }
  if (!hydrationAttempted) {
    hydrateFromBrowserStorage()
  }
  if (cachedAccessToken) {
    return true
  }
  if (isBrowserEnv) {
    try {
      return Boolean(window.localStorage.getItem(LEGACY_TOKEN_KEY))
    } catch (error) {
      return false
    }
  }
  return false
}

const isAdminSync = () => {
  const user = getCachedUser()
  if (!user) {
    return false
  }
  // UserProfile의 role 필드를 우선 확인 (백엔드에서 제공하는 정확한 권한 정보)
  // role이 'admin_role'이면 관리자
  if (user.role === 'admin_role') {
    return true
  }
  // role 필드가 없거나 'admin_role'이 아닌 경우, Django의 is_superuser/is_staff 확인
  // (하지만 이것은 실제 권한과 다를 수 있으므로 주의)
  return (
    user.is_superuser === true ||
    user.is_staff === true
  )
}

const subscribeToAuthChanges = (handler) => {
  if (typeof handler !== 'function') {
    return () => {}
  }
  subscribers.add(handler)
  handler(getAuthSnapshot())
  return () => {
    subscribers.delete(handler)
  }
}

const refreshAuthCache = async () => {
  const [rawUser, accessToken, refreshToken] = await Promise.all([
    storage.get(USER_KEY),
    storage.get(ACCESS_TOKEN_KEY),
    storage.get(REFRESH_TOKEN_KEY)
  ])

  const parsedAccessToken = typeof accessToken === 'string' ? accessToken : null
  const enrichedUser = enrichUserWithToken(
    safeParseJSON(rawUser),
    parsedAccessToken
  )

  setCachedUser(enrichedUser)
  setCachedAccessToken(parsedAccessToken)
  setCachedRefreshToken(typeof refreshToken === 'string' ? refreshToken : null)

  return getAuthSnapshot()
}

hydrateFromBrowserStorage()

const toTimestamp = (secondsFromNow) => {
  if (!secondsFromNow && secondsFromNow !== 0) {
    return null
  }
  return Date.now() + secondsFromNow * 1000
}

const authService = {
  async storeAuthResult({ access, refresh, access_expires_in, refresh_expires_in, user }) {
    if (typeof access === 'string') {
      await storage.set(ACCESS_TOKEN_KEY, access)
      const expiresAt = toTimestamp(access_expires_in ?? DEFAULT_ACCESS_TOKEN_TTL)
      if (expiresAt) {
        await storage.set(ACCESS_EXPIRES_AT_KEY, String(expiresAt))
      }
      setCachedAccessToken(access)
    }

    if (typeof refresh === 'string') {
      await storage.set(REFRESH_TOKEN_KEY, refresh)
      const refreshExpiresAt = toTimestamp(refresh_expires_in ?? DEFAULT_REFRESH_TOKEN_TTL)
      if (refreshExpiresAt) {
        await storage.set(REFRESH_EXPIRES_AT_KEY, String(refreshExpiresAt))
      }
      setCachedRefreshToken(refresh)
    }

    let processedUser = user
    if (!processedUser && typeof access === 'string') {
      processedUser = enrichUserWithToken({}, access)
    } else if (processedUser && typeof access === 'string') {
      processedUser = enrichUserWithToken(processedUser, access)
    }

    const existingCachedUser = getCachedUser()
    if (existingCachedUser) {
      processedUser = {
        ...(existingCachedUser || {}),
        ...(processedUser || {})
      }
    }

    if (user) {
      await storage.set(USER_KEY, JSON.stringify(processedUser))
      setCachedUser(processedUser)
    } else if (processedUser && Object.keys(processedUser).length > 0) {
      await storage.set(USER_KEY, JSON.stringify(processedUser))
      setCachedUser(processedUser)
    }
  },

  async getAccessToken() {
    if (cachedAccessToken) {
      return cachedAccessToken
    }
    const token = await storage.get(ACCESS_TOKEN_KEY)
    if (typeof token === 'string') {
      setCachedAccessToken(token)
    }
    return token
  },

  async getRefreshToken() {
    if (cachedRefreshToken) {
      return cachedRefreshToken
    }
    const token = await storage.get(REFRESH_TOKEN_KEY)
    if (typeof token === 'string') {
      setCachedRefreshToken(token)
    }
    return token
  },

  async getAccessTokenExpiry() {
    const raw = await storage.get(ACCESS_EXPIRES_AT_KEY)
    return raw ? Number(raw) : null
  },

  async getRefreshTokenExpiry() {
    const raw = await storage.get(REFRESH_EXPIRES_AT_KEY)
    return raw ? Number(raw) : null
  },

  async clearAuth() {
    await storage.clear([
      ACCESS_TOKEN_KEY,
      REFRESH_TOKEN_KEY,
      ACCESS_EXPIRES_AT_KEY,
      REFRESH_EXPIRES_AT_KEY,
      USER_KEY
    ])
    setCachedAccessToken(null)
    setCachedRefreshToken(null)
    setCachedUser(null)
  },

  async getUser() {
    const cached = getCachedUser()
    if (cached) {
      return cached
    }
    const raw = await storage.get(USER_KEY)
    if (!raw) {
      return null
    }
    const parsed = safeParseJSON(raw)
    if (parsed) {
      setCachedUser(parsed)
    }
    return parsed
  },

  async refreshAccessToken() {
    const refresh = await this.getRefreshToken()
    if (!refresh) {
      throw new Error('No refresh token available')
    }
    const response = await axios.post('/api/token/refresh/', { refresh })
    const access = response.data.access
    const access_expires_in = response.data.expires_in ?? DEFAULT_ACCESS_TOKEN_TTL
    if (!access) {
      throw new Error('Failed to refresh access token')
    }
    await storage.set(ACCESS_TOKEN_KEY, access)
    await storage.set(ACCESS_EXPIRES_AT_KEY, String(toTimestamp(access_expires_in)))
    setCachedAccessToken(access)
    return access
  },

  getCachedUser() {
    return getCachedUser()
  },

  getUserSync() {
    return getCachedUser()
  },

  isAuthenticatedSync() {
    return isAuthenticatedSync()
  },

  async isAuthenticated() {
    const [user, token] = await Promise.all([
      this.getUser(),
      this.getAccessToken()
    ])
    return Boolean(user && token)
  },

  isAdminSync() {
    return isAdminSync()
  },

  subscribe(handler) {
    return subscribeToAuthChanges(handler)
  },

  getAuthSnapshot() {
    return getAuthSnapshot()
  },

  async refreshAuthCache() {
    return refreshAuthCache()
  },

  async checkAuthStatus() {
    try {
      const axiosInstance = axios.create({
        baseURL: apiBaseURL,
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      const response = await axiosInstance.get('/api/auth/status/')
      
      if (response.data && response.data.authenticated && response.data.user) {
        const user = response.data.user
        await this.storeAuthResult({ user })
        return { authenticated: true, user }
      }
      
      return { authenticated: false, user: null }
    } catch (error) {
      // 400 Bad Request는 인증되지 않은 상태로 정상 처리
      if (error.response && error.response.status === 400) {
        return { authenticated: false, user: null }
      }
      console.error('[authService] checkAuthStatus failed:', error)
      return { authenticated: false, user: null }
    }
  }
}

export default authService

