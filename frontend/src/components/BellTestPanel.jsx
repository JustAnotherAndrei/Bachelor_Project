import { CheckCircle2, XCircle, Atom } from 'lucide-react'

export default function BellTestPanel({ bell }) {
  if (!bell || bell.chsh_S == null) return null

  const S = bell.chsh_S
  const violation = bell.bell_violation
  const tsirelson = bell.quantum_bound

  // The Bell parameter ranges over [-2*sqrt(2), 2*sqrt(2)] for quantum
  // systems; classical (local hidden-variable) theories are bounded at |S| <= 2.
  // We render a horizontal bar with the |S| value and three reference lines.
  const absS = Math.abs(S)
  const pct = Math.min(absS / tsirelson, 1) * 100
  const classicalPct = (2 / tsirelson) * 100

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Atom className="text-fuchsia-400" size={18} />
        <h3 className="text-sm font-semibold text-gray-200">E91 — CHSH Bell Test</h3>
      </div>

      <p className="text-xs text-gray-400 mb-3 leading-relaxed">
        The CHSH correlator S quantifies entanglement. Local hidden-variable
        theories cannot exceed |S| = 2 — any larger value certifies genuine
        quantum entanglement (Tsirelson bound 2√2 ≈ 2.828).
      </p>

      <div className="flex items-baseline gap-2 mb-2">
        <span className="font-mono text-3xl text-gray-100">
          {S >= 0 ? '+' : ''}{S.toFixed(3)}
        </span>
        <span className="text-xs text-gray-500">|S|</span>
        <span className="ml-2">
          {violation ? (
            <span className="text-xs px-2 py-1 rounded-md bg-emerald-900 text-emerald-300 border border-emerald-700 inline-flex items-center gap-1">
              <CheckCircle2 size={12} /> Bell violated — entanglement intact
            </span>
          ) : (
            <span className="text-xs px-2 py-1 rounded-md bg-red-900 text-red-300 border border-red-700 inline-flex items-center gap-1">
              <XCircle size={12} /> |S| ≤ 2 — entanglement broken (Eve?)
            </span>
          )}
        </span>
      </div>

      {/* Visual bar */}
      <div className="relative h-3 bg-gray-800 rounded-full overflow-hidden mt-3 mb-2">
        <div
          className={`absolute left-0 top-0 h-full ${violation ? 'bg-fuchsia-500' : 'bg-orange-600'}`}
          style={{ width: `${pct}%` }}
        />
        <div
          className="absolute top-0 h-full border-r-2 border-yellow-500"
          style={{ left: `${classicalPct}%`, width: 0 }}
          title="Classical bound |S| = 2"
        />
      </div>
      <div className="flex justify-between text-[10px] text-gray-500 font-mono">
        <span>0</span>
        <span style={{ marginLeft: `${classicalPct - 6}%` }}>2 (classical)</span>
        <span>{tsirelson.toFixed(3)} (quantum)</span>
      </div>

      {bell.chsh_terms && (
        <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
          {Object.entries(bell.chsh_terms).map(([k, v]) => (
            <div key={k} className="bg-gray-800 border border-gray-700 rounded-md px-2 py-1.5 flex justify-between">
              <span className="text-gray-400 font-mono">{k}</span>
              <span className="text-gray-100 font-mono">{Number(v).toFixed(3)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
