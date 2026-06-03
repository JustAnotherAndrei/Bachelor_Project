// Catalog of the 15 missions as click-able cards.
//
// A card is one of three states:
//   - locked    : greyed out, lock icon, no action
//   - unlocked  : violet border, click to start
//   - completed : green border, check icon, best score shown — still playable

import { Lock, CheckCircle2, Trophy, Search, Wrench } from 'lucide-react'

const DIFFICULTY_COLORS = {
  easy:   'text-emerald-400',
  medium: 'text-amber-400',
  hard:   'text-red-400',
}

export default function LevelGrid({ levels, onStart, currentUser }) {
  if (!levels?.length) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center text-gray-500 text-sm">
        Loading missions…
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-200">Mission catalogue</h3>
        {!currentUser && (
          <span className="text-xs text-amber-400 bg-amber-950 border border-amber-800 rounded-md px-2 py-1">
            Sign in to track progress and unlock levels
          </span>
        )}
      </div>
      <div className="grid grid-cols-3 gap-3">
        {levels.map(m => (
          <Card key={m.id} mission={m} onStart={onStart} />
        ))}
      </div>
    </div>
  )
}

function Card({ mission: m, onStart }) {
  const TypeIcon = m.type === 'detective' ? Search : Wrench
  const typeColor = m.type === 'detective' ? 'text-blue-300' : 'text-emerald-300'
  const typeBg = m.type === 'detective' ? 'bg-blue-900/40 border-blue-800/60' : 'bg-emerald-900/40 border-emerald-800/60'
  const disabled = !m.unlocked

  const borderColor = m.completed
    ? 'border-emerald-700'
    : disabled
    ? 'border-gray-800'
    : 'border-gray-700 hover:border-violet-500'

  return (
    <button
      onClick={() => !disabled && onStart(m.level)}
      disabled={disabled}
      className={`text-left border rounded-lg p-3 transition-colors ${
        borderColor
      } ${
        disabled ? 'bg-gray-900 opacity-50 cursor-not-allowed' : 'bg-gray-800/50 hover:bg-gray-800 cursor-pointer'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono text-gray-500">Level {m.level}</span>
        <div className="flex items-center gap-1.5">
          {m.completed && <CheckCircle2 size={14} className="text-emerald-400" />}
          {disabled && <Lock size={14} className="text-gray-500" />}
          <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${typeBg} ${typeColor}`}>
            <TypeIcon size={9} className="inline mr-0.5" />
            {m.type}
          </span>
        </div>
      </div>
      <p className="text-sm font-medium text-gray-100 mb-1 leading-tight">{m.scenario}</p>
      <div className="flex items-center justify-between text-[11px]">
        <span className={`uppercase tracking-wider ${DIFFICULTY_COLORS[m.difficulty]}`}>
          {m.difficulty}
        </span>
        <span className="flex items-center gap-1 text-amber-400 font-mono">
          <Trophy size={10} /> {m.xp_reward} XP
        </span>
      </div>
      {m.completed && m.best_score > 0 && (
        <p className="text-[10px] text-emerald-400 mt-1 font-mono">Best score: {m.best_score}</p>
      )}
    </button>
  )
}
