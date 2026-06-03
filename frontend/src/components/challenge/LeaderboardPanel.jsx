// Global top-N players, sorted by total_xp.
// The rank-1 row gets a gold halo, rank 2/3 silver/bronze.

import { Trophy, Medal, Award } from 'lucide-react'

const RANK_STYLE = {
  1: { ring: 'ring-2 ring-yellow-400/60', icon: <Trophy size={14} className="text-yellow-400" /> },
  2: { ring: 'ring-2 ring-gray-300/40',   icon: <Medal  size={14} className="text-gray-300" /> },
  3: { ring: 'ring-2 ring-amber-700/60',  icon: <Award  size={14} className="text-amber-700" /> },
}

export default function LeaderboardPanel({ leaderboard, currentUserId }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Trophy className="text-amber-400" size={18} />
        <h3 className="text-sm font-semibold text-gray-200">Global leaderboard</h3>
        <span className="text-xs text-gray-500 font-mono ml-auto">Top {leaderboard.length}</span>
      </div>

      {leaderboard.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-6">
          No completed missions yet — be the first on the board.
        </p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-gray-800">
              <th className="text-left py-2 font-medium">Rank</th>
              <th className="text-left py-2 font-medium">Player</th>
              <th className="text-right py-2 font-medium">XP</th>
              <th className="text-right py-2 font-medium">Levels</th>
              <th className="text-right py-2 font-medium">Streak</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map(row => {
              const style = RANK_STYLE[row.rank] || {}
              const isMe = currentUserId && row.user_id === currentUserId
              return (
                <tr
                  key={row.user_id}
                  className={`border-b border-gray-800/50 last:border-b-0 ${
                    isMe ? 'bg-violet-950/40' : ''
                  }`}
                >
                  <td className="py-2">
                    <span className="flex items-center gap-2 font-mono text-gray-400">
                      {style.icon || <span className="w-3.5" />}
                      #{row.rank}
                    </span>
                  </td>
                  <td className="py-2">
                    <span className="flex items-center gap-2">
                      {row.avatar_url ? (
                        <img
                          src={row.avatar_url}
                          alt=""
                          className={`w-6 h-6 rounded-full ${style.ring || ''}`}
                          referrerPolicy="no-referrer"
                        />
                      ) : (
                        <span className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-xs">
                          {(row.display_name || '?')[0].toUpperCase()}
                        </span>
                      )}
                      <span className={`${isMe ? 'text-violet-300 font-semibold' : 'text-gray-200'}`}>
                        {row.display_name}
                        {isMe && <span className="text-[10px] text-violet-400 ml-1">(you)</span>}
                      </span>
                    </span>
                  </td>
                  <td className="text-right py-2 font-mono text-amber-400">{row.total_xp}</td>
                  <td className="text-right py-2 font-mono text-gray-300">{row.levels_completed}/15</td>
                  <td className="text-right py-2 font-mono text-emerald-400">{row.best_streak}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
