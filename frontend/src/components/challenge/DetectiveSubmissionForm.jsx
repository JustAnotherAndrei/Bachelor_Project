// Detective-mission verdict form. Shown AFTER the simulation completes.
// Player picks verdict and (if compromised) the attack type, then submits.

import { useState } from 'react'
import { Search, AlertOctagon, ShieldCheck } from 'lucide-react'

const ATTACK_OPTIONS = [
  { value: 'intercept_resend', label: 'Intercept-resend (Weak/Strong)',
    blurb: 'Eve measured photons and resent them — adds noise on basis-matched positions.' },
  { value: 'smart',            label: 'Smart / adaptive',
    blurb: 'Eve throttled her intercept rate to stay below the QBER threshold.' },
  { value: 'pns',              label: 'Photon-Number-Splitting',
    blurb: 'Eve exploited multi-photon pulses — no QBER signature, only decoy bounds expose her.' },
]


export default function DetectiveSubmissionForm({ onSubmit, disabled }) {
  const [verdict, setVerdict] = useState(null)
  const [attack, setAttack] = useState(null)

  const canSubmit = verdict === 'secure' || (verdict === 'compromised' && attack)

  return (
    <div className="bg-gray-900 border border-blue-800/40 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-1">
        <Search className="text-blue-400" size={16} />
        <h3 className="text-sm font-semibold text-gray-200">Your verdict</h3>
      </div>
      <p className="text-xs text-gray-500 mb-4">
        Read the panels above (QBER, LSTM, decoy/PNS, Bell test), then declare whether the channel is compromised — and if so, by which attack.
      </p>

      {/* Verdict toggle */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => { setVerdict('secure'); setAttack(null) }}
          disabled={disabled}
          className={`flex-1 py-3 rounded-lg border transition-colors flex items-center justify-center gap-2 ${
            verdict === 'secure'
              ? 'bg-emerald-900/50 border-emerald-600 text-emerald-200'
              : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200'
          }`}
        >
          <ShieldCheck size={16} /> Secure
        </button>
        <button
          onClick={() => setVerdict('compromised')}
          disabled={disabled}
          className={`flex-1 py-3 rounded-lg border transition-colors flex items-center justify-center gap-2 ${
            verdict === 'compromised'
              ? 'bg-red-900/50 border-red-600 text-red-200'
              : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200'
          }`}
        >
          <AlertOctagon size={16} /> Compromised
        </button>
      </div>

      {/* Attack picker — only when compromised */}
      {verdict === 'compromised' && (
        <div className="flex flex-col gap-2 mb-4">
          <label className="text-xs text-gray-400">Which attack?</label>
          {ATTACK_OPTIONS.map(o => (
            <button
              key={o.value}
              onClick={() => setAttack(o.value)}
              disabled={disabled}
              className={`text-left p-3 rounded-lg border transition-colors ${
                attack === o.value
                  ? 'bg-blue-900/40 border-blue-600 text-blue-100'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
              }`}
            >
              <p className="text-sm font-medium">{o.label}</p>
              <p className="text-[11px] text-gray-500 mt-0.5">{o.blurb}</p>
            </button>
          ))}
        </div>
      )}

      <button
        onClick={() => canSubmit && onSubmit({
          verdict,
          attack_type: verdict === 'secure' ? null : attack,
        })}
        disabled={!canSubmit || disabled}
        className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg transition-colors"
      >
        Submit verdict
      </button>
    </div>
  )
}
