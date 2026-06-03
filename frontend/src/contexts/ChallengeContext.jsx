// Global Challenge Mode state — progress, level catalog, leaderboard.
// Fetched on mount and re-fetched after a successful attempt.

import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { api } from '../lib/api'
import { useAuth } from './AuthContext'

const ChallengeContext = createContext(null)

const EMPTY_PROGRESS = {
  levels_unlocked: 1,
  levels_completed: 0,
  total_xp: 0,
  current_streak: 0,
  best_streak: 0,
}

export function ChallengeProvider({ children }) {
  const { user } = useAuth()
  const [progress, setProgress] = useState(EMPTY_PROGRESS)
  const [levels, setLevels] = useState([])
  const [leaderboard, setLeaderboard] = useState([])
  const [loaded, setLoaded] = useState(false)

  const refreshLevels = useCallback(async () => {
    try {
      const data = await api('/api/v1/challenge/levels')
      setLevels(data?.levels || [])
    } catch {
      setLevels([])
    }
  }, [])

  const refreshProgress = useCallback(async () => {
    try {
      const data = await api('/api/v1/challenge/progress')
      setProgress(data || EMPTY_PROGRESS)
    } catch {
      setProgress(EMPTY_PROGRESS)
    }
  }, [])

  const refreshLeaderboard = useCallback(async () => {
    try {
      const data = await api('/api/v1/challenge/leaderboard?limit=50')
      setLeaderboard(data?.leaderboard || [])
    } catch {
      setLeaderboard([])
    }
  }, [])

  const refreshAll = useCallback(async () => {
    await Promise.all([refreshLevels(), refreshProgress(), refreshLeaderboard()])
    setLoaded(true)
  }, [refreshLevels, refreshProgress, refreshLeaderboard])

  // Re-fetch when the auth state changes (sign-in unlocks personal data).
  useEffect(() => { refreshAll() }, [user, refreshAll])

  const value = {
    progress, levels, leaderboard, loaded,
    refreshLevels, refreshProgress, refreshLeaderboard, refreshAll,
  }
  return <ChallengeContext.Provider value={value}>{children}</ChallengeContext.Provider>
}

export function useChallenge() {
  const ctx = useContext(ChallengeContext)
  if (!ctx) throw new Error('useChallenge must be used inside <ChallengeProvider>')
  return ctx
}
