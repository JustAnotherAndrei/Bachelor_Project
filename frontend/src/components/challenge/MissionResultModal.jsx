// Result overlay shown after the player submits an attempt.
// Three states: correct (green), incorrect (red), partial (amber).
// Renders a Detective-style breakdown (verdict + attack truth) or an
// Engineer-style breakdown (constraints actual vs expected).

import { CheckCircle2, XCircle, RotateCcw, ChevronRight, Trophy, Lightbulb, Compass } from 'lucide-react'
import { FACTS, CATEGORY_COLOR } from '../FunFactPanel'


const WIN_MESSAGES = [
  'Congratulations — sharp deduction!',
  'Nailed it. Clean call.',
  'Spot on. Eve had nowhere to hide.',
  'Textbook reading of the evidence.',
  'Bullseye. Your instincts are sharp.',
  'Crystal clear call. Well played.',
  'Decisive and correct — well done.',
  "That's the kind of read a quantum cryptographer wants.",
  'Right on the money.',
  'Beautifully reasoned. Keep going.',
]

const FAIL_MESSAGES = [
  "Not quite. The evidence pointed elsewhere — read the breakdown below.",
  "Close, but the channel told a different story.",
  "Eve fooled you on this one. Don't take it personally.",
  "Missed it. The noise floor played a trick.",
  "So close — give it another roll.",
  "Not the right call. Try a fresh roll and look at the panels again.",
  "Better luck on the next roll.",
  "Tricky one. Even seasoned cryptographers second-guess themselves here.",
  "The QBER lied today. Retry with new parameters?",
  "Tough call, but the truth is in the breakdown.",
]


function pickMessage(pool, key) {
  // Deterministic pick based on the attempt's content so the same result
  // always shows the same message (avoids flicker on re-render).
  let hash = 0
  for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) | 0
  return pool[Math.abs(hash) % pool.length]
}


export default function MissionResultModal({ mission, result, onClose, onRetry }) {
  if (!result) return null

  const passed = result.correct
  const isDetective = mission?.type === 'detective'

  const ring = passed
    ? 'border-emerald-600 bg-gradient-to-br from-emerald-950 to-gray-900'
    : 'border-red-600 bg-gradient-to-br from-red-950 to-gray-900'

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div className={`bg-gray-900 border-2 rounded-xl shadow-2xl max-w-2xl w-full ${ring}`}>
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start gap-4 mb-5">
            {passed ? (
              <CheckCircle2 className="text-emerald-400 shrink-0" size={42} />
            ) : (
              <XCircle className="text-red-400 shrink-0" size={42} />
            )}
            <div className="flex-1">
              <h2 className={`text-2xl font-semibold ${passed ? 'text-emerald-200' : 'text-red-200'}`}>
                {passed ? 'Mission complete' : 'Mission failed'}
              </h2>
              <p className={`text-sm italic font-medium mt-0.5 ${passed ? 'text-emerald-300' : 'text-red-300'}`}>
                {pickMessage(
                  passed ? WIN_MESSAGES : FAIL_MESSAGES,
                  `${mission?.id ?? ''}-${result.score}-${result.correct}-${result.progress?.total_xp ?? 0}`,
                )}
              </p>
              <p className="text-sm text-gray-400 mt-0.5">
                Level {mission?.level} — {mission?.scenario}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Score</p>
              <p className="text-3xl font-mono font-bold text-gray-100">{result.score}</p>
              {result.xp_earned > 0 && (
                <p className="text-xs text-amber-400 font-mono flex items-center justify-end gap-1 mt-1">
                  <Trophy size={11} /> +{result.xp_earned} XP
                </p>
              )}
            </div>
          </div>

          {/* Breakdown */}
          {isDetective ? <DetectiveBreakdown breakdown={result.breakdown} truth={result.truth} />
                       : <EngineerBreakdown breakdown={result.breakdown} />}

          {/* Explanation */}
          {result.explanation && (
            <div className="mt-5 bg-gray-800/50 border border-gray-700 rounded-lg p-3">
              <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Why this verdict</p>
              <p className="text-sm text-gray-300 leading-relaxed">{result.explanation}</p>
            </div>
          )}

          {/* Progress snapshot */}
          {result.progress && (
            <div className="mt-5 grid grid-cols-4 gap-2 text-center text-xs">
              <ProgressCell label="Total XP" value={result.progress.total_xp} accent="text-amber-400" />
              <ProgressCell label="Levels done" value={`${result.progress.levels_completed}/15`} accent="text-emerald-400" />
              <ProgressCell label="Unlocked" value={`L${result.progress.levels_unlocked}`} accent="text-violet-400" />
              <ProgressCell label="Streak" value={result.progress.current_streak} accent="text-pink-400" />
            </div>
          )}

          {/* On success show a QKD fact as reward · on failure show targeted hints. */}
          {passed ? (
            <ResultFunFact seedKey={`${mission?.id ?? ''}-${result.score}-${result.progress?.total_xp ?? 0}`} />
          ) : (
            <ResultHints mission={mission} result={result} />
          )}

          {/* Actions */}
          <div className="mt-6 flex gap-3">
            <button
              onClick={onRetry}
              className="flex-1 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <RotateCcw size={14} /> Retry with new roll
            </button>
            <button
              onClick={onClose}
              className="flex-1 bg-violet-600 hover:bg-violet-500 text-white font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              Back to catalogue <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


function DetectiveBreakdown({ breakdown, truth }) {
  if (!breakdown) return null
  const v = breakdown.verdict || {}
  const a = breakdown.attack_type || {}
  return (
    <div className="bg-gray-800/40 border border-gray-700 rounded-lg p-4">
      <p className="text-xs uppercase tracking-wider text-gray-500 mb-3">Verdict breakdown</p>
      <BreakdownRow label="Verdict"      user={v.user} truth={v.truth} ok={v.ok} />
      <BreakdownRow label="Attack type"  user={a.user ?? '—'} truth={a.truth ?? '—'} ok={a.ok} />
      {truth?.eve_mode && (
        <p className="text-[11px] text-gray-500 mt-2 font-mono">
          Actual Eve mode: <span className="text-gray-300">{truth.eve_mode}</span>
        </p>
      )}
    </div>
  )
}


function BreakdownRow({ label, user, truth, ok }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm border-b border-gray-800 last:border-b-0">
      <span className="text-gray-400">{label}</span>
      <span className="flex items-center gap-3 font-mono">
        <span className={ok ? 'text-emerald-300' : 'text-red-300'}>
          you: {String(user)}
        </span>
        <span className="text-gray-500">·</span>
        <span className="text-gray-300">truth: {String(truth)}</span>
        {ok
          ? <CheckCircle2 size={14} className="text-emerald-400" />
          : <XCircle size={14} className="text-red-400" />}
      </span>
    </div>
  )
}


function EngineerBreakdown({ breakdown }) {
  if (!breakdown?.constraints) return null
  return (
    <div className="bg-gray-800/40 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs uppercase tracking-wider text-gray-500">Constraints</p>
        <p className="text-xs text-gray-400 font-mono">
          {breakdown.n_passed}/{breakdown.n_total} satisfied
        </p>
      </div>
      <ul className="space-y-1.5">
        {breakdown.constraints.map((c, i) => (
          <li key={i} className="flex items-center justify-between text-sm font-mono">
            <span className="text-gray-300">
              {c.metric} {c.op} {String(c.value)}
            </span>
            <span className="flex items-center gap-2">
              <span className={c.ok ? 'text-emerald-300' : 'text-red-300'}>
                actual: {formatActual(c.actual)}
              </span>
              {c.ok
                ? <CheckCircle2 size={14} className="text-emerald-400" />
                : <XCircle size={14} className="text-red-400" />}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}


function formatActual(v) {
  if (typeof v === 'number') {
    return Number.isInteger(v) ? v : v.toFixed(3)
  }
  if (v === null || v === undefined) return '—'
  return String(v)
}


function ResultHints({ mission, result }) {
  const hints = generateHints(mission, result)
  if (hints.length === 0) return null

  return (
    <div className="mt-5 bg-blue-950/30 border border-blue-900/60 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <Compass className="text-blue-400" size={14} />
        <span className="text-xs font-semibold text-blue-200">Hints for next time</span>
      </div>
      <ul className="space-y-2.5">
        {hints.map((h, i) => (
          <li key={i} className="text-xs">
            <p className="text-blue-200 font-medium mb-0.5">· {h.title}</p>
            <p className="text-gray-300 leading-relaxed pl-2">{h.text}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}


function generateHints(mission, result) {
  const hints = []
  const breakdown = result?.breakdown || {}

  if (mission?.type === 'detective') {
    const truth = result.truth || {}
    const verdictWrong = breakdown.verdict && !breakdown.verdict.ok
    const attackWrong = breakdown.attack_type && !breakdown.attack_type.ok &&
                        truth.verdict === 'compromised'

    // False positive — user called Eve where there wasn't one
    if (verdictWrong && truth.verdict === 'secure') {
      hints.push({
        title: "You called Eve where there wasn't one",
        text: "When QBER stays under ~5 % and the LSTM panel reads close to 0, the channel is almost certainly honest. Channel noise alone (depolarising + measurement error) accounts for 2–4 % QBER on a clean link.",
      })
    }

    // False negative — user missed a real attack; tailor by attack type
    if (verdictWrong && truth.verdict === 'compromised') {
      if (truth.attack_type === 'intercept_resend') {
        hints.push({
          title: 'Intercept-resend leaves a QBER fingerprint',
          text: "Each intercepted qubit has a 50 % chance of arriving in the wrong basis, adding ~25 % per-qubit noise. Even Weak Eve (~30 % intercept rate) pushes the observed QBER ~6 % above the honest noise floor.",
        })
      } else if (truth.attack_type === 'smart') {
        hints.push({
          title: 'Smart Eve hides in the QBER gray zone',
          text: "She throttles her intercept rate to stay just under the 11 % abort threshold. When QBER looks borderline (7–10 %) but the LSTM panel flags eavesdropping, trust the LSTM.",
        })
      } else if (truth.attack_type === 'pns') {
        hints.push({
          title: "PNS doesn't disturb QBER at all",
          text: "Photon-Number-Splitting reads multi-photon pulses without touching the singles, so QBER stays clean. The fingerprint is the decoy-state Y₁ bound: when it collapses near zero, it's PNS.",
        })
      }
    }

    // Verdict was right, but the attack picked was wrong
    if (!verdictWrong && attackWrong) {
      hints.push({
        title: 'Match the attack to its fingerprint',
        text: "High QBER (>10 %) ⇒ intercept-resend. QBER in 7–10 % with LSTM strong ⇒ smart Eve. QBER normal but decoy Y₁ collapses ⇒ PNS. Pick the attack whose signature actually appeared on the panels.",
      })
    }

    // Always end with a process tip
    hints.push({
      title: 'Three panels to weigh together',
      text: "QBER stat for the obvious cases · LSTM detection for pattern-based attacks the average smooths out · Decoy-state Y₁ for PNS (which leaves QBER untouched).",
    })
    return hints
  }

  if (mission?.type === 'engineer') {
    const constraints = breakdown.constraints || []
    const failed = constraints.filter(c => !c.ok)

    for (const c of failed) {
      const metric = c.metric || ''
      if (metric.startsWith('finite_key.')) {
        hints.push({
          title: `Finite-key bound was ${formatNum(c.actual)} (need ${c.op} ${c.value})`,
          text: "Boost N (more qubits → smaller Hoeffding correction δ_PE → larger bound), or reduce QBER (lower channel noise, shorter distance). CASCADE EC usually leaks less than parity-block on tight budgets.",
        })
      } else if (metric.startsWith('decoy_state.Y1') && c.op.startsWith('>')) {
        hints.push({
          title: 'Decoy Y₁ bound was too low',
          text: "μ_signal and μ_decoy must be far enough apart for the bound to mean something. Try μ_signal ≈ 0.5 with μ_decoy ≈ 0.1, and probabilities around 70 / 15 / 15 (signal / decoy / vacuum).",
        })
      } else if (metric.startsWith('decoy_state.Y1') && c.op.startsWith('<')) {
        hints.push({
          title: "Decoy didn't catch the attack",
          text: "For PNS detection you want the decoy bound to collapse. Make sure μ_decoy is much smaller than μ_signal so the per-intensity gain difference is sharp enough.",
        })
      } else if (metric.startsWith('bell_test')) {
        hints.push({
          title: 'Bell violation was insufficient',
          text: "E91 needs clean entanglement. Lower depolarising and measurement-error noise, and run enough qubits for the S parameter to stabilise above the classical bound of 2.",
        })
      } else if (metric === 'is_secure') {
        hints.push({
          title: 'QBER above the secure threshold',
          text: "The classical secure threshold sits at ~11 %. Reduce channel noise, shorten the distance, or pick a protocol/source that reconciles less of your key away.",
        })
      } else {
        hints.push({
          title: `${metric} didn't meet target`,
          text: `Required ${c.op} ${c.value}, run produced ${formatNum(c.actual)}. Adjust the parameter most directly tied to this metric and try again.`,
        })
      }
    }
    if (hints.length === 0) {
      hints.push({
        title: 'Read the constraints box above',
        text: "Each row shows actual vs required. Find the one that failed and tune the parameter that drives it on the next attempt.",
      })
    }
    return hints
  }

  return hints
}


function formatNum(v) {
  if (typeof v === 'number') return Number.isInteger(v) ? v : v.toFixed(3)
  if (v === null || v === undefined) return '—'
  return String(v)
}


function ResultFunFact({ seedKey }) {
  // Deterministic pick from the attempt's seedKey — a fresh roll naturally
  // produces a different key (new score / total_xp), so the fact rotates
  // on every retry without needing an explicit shuffle button.
  let hash = 0
  for (let i = 0; i < seedKey.length; i++) hash = (hash * 31 + seedKey.charCodeAt(i)) | 0
  const fact = FACTS[Math.abs(hash) % FACTS.length]
  const categoryClass = CATEGORY_COLOR[fact.category] || CATEGORY_COLOR.Trivia

  return (
    <div className="mt-5 bg-yellow-950/30 border border-yellow-900/60 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <Lightbulb className="text-yellow-400" size={14} />
        <span className="text-xs font-semibold text-yellow-200">Did you know?</span>
        <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${categoryClass}`}>
          {fact.category}
        </span>
      </div>
      <p className="text-xs text-gray-300 leading-relaxed">{fact.text}</p>
    </div>
  )
}


function ProgressCell({ label, value, accent }) {
  return (
    <div className="bg-gray-800/60 border border-gray-700 rounded-md py-2 px-1">
      <p className="text-[10px] uppercase tracking-wider text-gray-500">{label}</p>
      <p className={`font-mono font-semibold ${accent}`}>{value}</p>
    </div>
  )
}
