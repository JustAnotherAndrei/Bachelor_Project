import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { api } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On mount: try /me. If 401, we stay as guest.
  useEffect(() => {
    api('/api/v1/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const { user } = await api('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    setUser(user)
    return user
  }, [])

  const register = useCallback(async (email, password, full_name) => {
    const { user } = await api('/api/v1/auth/register', {
      method: 'POST',
      body: { email, password, full_name },
    })
    setUser(user)
    return user
  }, [])

  const logout = useCallback(async () => {
    try { await api('/api/v1/auth/logout', { method: 'POST' }) } catch { /* ignore */ }
    setUser(null)
  }, [])

  const forgotPassword = useCallback(async (email) => {
    return api('/api/v1/auth/password/forgot', { method: 'POST', body: { email } })
  }, [])

  const resetPassword = useCallback(async (token, new_password) => {
    const { user } = await api('/api/v1/auth/password/reset', {
      method: 'POST',
      body: { token, new_password },
    })
    setUser(user)
    return user
  }, [])

  const value = { user, loading, login, register, logout, forgotPassword, resetPassword }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
