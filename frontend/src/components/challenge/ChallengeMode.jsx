// Top-level Challenge Mode page. Orchestrates:
//   - the level catalogue and leaderboard (idle/landing view)
//   - the active mission flow (briefing -> running -> awaiting_answer)
//   - the result modal overlay
//
// All simulation work is delegated to useChallengeSession, which itself
// composes the same useSimulationSocket hook the main Dashboard uses — so
// the underlying QKD pipeline is exactly the one the rest of the app exercises.

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Shield, ChevronLeft, LogIn, Trophy, Flame, BadgeCheck } from 'lucide-react'

import { useChallenge } from '../../contexts/ChallengeContext'
import { useAuth } from '../../contexts/AuthContext'
import useChallengeSession from '../../hooks/useChallengeSession'

import LevelGrid from './LevelGrid'
import MissionBriefing from './MissionBriefing'
import MissionResultModal from './MissionResultModal'
import LeaderboardPanel from './LeaderboardPanel'

import AuthModal from '../auth/AuthModal'
import UserMenu from '../auth/UserMenu'


export default function ChallengeMode() {
  const { user, loading: authLoading } = useAuth()
  const {
    levels, progress, leaderboard,
    refreshLevels, refreshProgress, refreshLeaderboard,
  } = useChallenge()
  const session = useChallengeSession()
  const [authOpen, setAuthOpen] = useState(false)

  async function handleStart(level) {
    if (!user) return
    await session.startLevel(level)
  }

  async function handleClose() {
    session.reset()
    await Promise.all([refreshLevels(), refreshProgress(), refreshLeaderboard()])
  }

  async function handleRetry() {
    const level = session.mission?.level
    session.reset()
    if (level) await session.startLevel(level)
  }

  const inMission = session.phase !== 'idle'

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="text-amber-400" size={28} />
          <span className="text-xl font-semibold tracking-tight">Challenge Mode</span>
          <span className="text-xs text-gray-500 font-mono">15 procedurally-generated QKD missions</span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-sm px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition-colors"
          >
            <ChevronLeft size={14} /> Back to Dashboard
          </Link>
          {!authLoading && (user ? <UserMenu /> : (
            <button
              onClick={() => setAuthOpen(true)}
              className="flex items-center gap-2 text-sm px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors"
            >
              <LogIn size={14} /> Sign in to play
            </button>
          ))}
        </div>
      </header>

      <main className="flex-1 p-6 max-w-6xl mx-auto w-full">
        {/* Persistent progress header */}
        <ProgressHeader progress={progress} user={user} />

        {session.error && (
          <div className="mt-4 bg-red-950 border border-red-800 text-red-200 text-sm rounded-lg px-4 py-3">
            {session.error}
          </div>
        )}

        {inMission ? (
          <div className="mt-6">
            <MissionBriefing session={session} onAbort={session.reset} />
          </div>
        ) : (
          <div className="mt-6 flex flex-col gap-6">
            <LevelGrid levels={levels} onStart={handleStart} currentUser={user} />
            <LeaderboardPanel leaderboard={leaderboard} currentUserId={user?.id} />
          </div>
        )}
      </main>

      {session.gradingResult && (
        <MissionResultModal
          mission={session.mission}
          result={session.gradingResult}
          onClose={handleClose}
          onRetry={handleRetry}
        />
      )}

      <AuthModal
        open={authOpen}
        onClose={() => setAuthOpen(false)}
        initialView="login"
      />
    </div>
  )
}


function ProgressHeader({ progress, user }) {
  if (!user) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-sm text-gray-400 text-center">
        Sign in from the dashboard to track your XP, unlock levels and join the leaderboard.
      </div>
    )
  }
  return (
    <div className="grid grid-cols-4 gap-3">
      <Stat icon={<Trophy size={16} className="text-amber-400" />}
            label="Total XP" value={progress?.total_xp ?? 0} accent="text-amber-400" />
      <Stat icon={<BadgeCheck size={16} className="text-emerald-400" />}
            label="Levels completed" value={`${progress?.levels_completed ?? 0} / 15`} accent="text-emerald-400" />
      <Stat icon={<Flame size={16} className="text-pink-400" />}
            label="Current streak" value={progress?.current_streak ?? 0} accent="text-pink-400" />
      <Stat icon={<Flame size={16} className="text-orange-400" />}
            label="Best streak" value={progress?.best_streak ?? 0} accent="text-orange-400" />
    </div>
  )
}


function Stat({ icon, label, value, accent }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 flex items-center gap-3">
      {icon}
      <div className="min-w-0">
        <p className="text-[10px] uppercase tracking-wider text-gray-500">{label}</p>
        <p className={`font-mono text-xl font-semibold ${accent}`}>{value}</p>
      </div>
    </div>
  )
}
