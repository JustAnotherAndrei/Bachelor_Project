import { Sparkles, AlertTriangle, ShieldCheck } from 'lucide-react'

function pct(x) { return `${(x * 100).toFixed(2)}%` }

export default function DecoyStatePanel({ decoy }) {
  if (!decoy) return null

  const { per_intensity, mu_signal, mu_decoy, bounds, secure_key_rate,
          pns_vulnerable, multi_photon_fraction, n_pulses, n_detected } = decoy

  const findRow = (target) => per_intensity.find(r => Math.abs(r.intensity - target) < 1e-3)
  const sig = findRow(mu_signal)
  const dec = findRow(mu_decoy)
  const vac = findRow(0.0)

  return (
    <div className="bg-gray-900 border border-amber-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="text-amber-400" size={18} />
          <p className="text-xs font-semibold text-amber-300 uppercase tracking-widest">
            Decoy-State Analysis
          </p>
        </div>
        <span className="text-xs text-amber-500 font-mono">Lo-Ma-Chen 2005</span>
      </div>

      {/* Source summary */}
      <div className="grid grid-cols-4 gap-3 text-center">
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Pulses sent</p>
          <p className="text-sm font-mono font-semibold text-gray-100">{n_pulses}</p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Detections</p>
          <p className="text-sm font-mono font-semibold text-blue-300">
            {n_detected}
            <span className="text-xs text-gray-500 ml-1">({pct(n_detected / n_pulses)})</span>
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Multi-photon pulses</p>
          <p className="text-sm font-mono font-semibold text-orange-300">
            {pns_vulnerable}
            <span className="text-xs text-gray-500 ml-1">({pct(multi_photon_fraction)})</span>
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Secure key rate</p>
          <p className="text-sm font-mono font-semibold text-green-300">
            {secure_key_rate.toFixed(5)}
            <span className="text-xs text-gray-500 ml-1">bit/pulse</span>
          </p>
        </div>
      </div>

      {/* Per-intensity table */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Gains and error rates per intensity</p>
        <table className="w-full text-xs">
          <thead className="text-gray-500">
            <tr>
              <th className="text-left py-1">Intensity</th>
              <th className="text-right py-1">Pulses</th>
              <th className="text-right py-1">Detections</th>
              <th className="text-right py-1">Gain Q</th>
              <th className="text-right py-1">QBER E</th>
            </tr>
          </thead>
          <tbody className="text-gray-200 font-mono">
            <tr className="border-t border-gray-800">
              <td className="py-1.5 text-amber-300">μ = {mu_signal.toFixed(2)} (signal)</td>
              <td className="text-right">{sig?.pulses ?? 0}</td>
              <td className="text-right">{sig?.detections ?? 0}</td>
              <td className="text-right">{sig ? sig.gain.toFixed(5) : '—'}</td>
              <td className="text-right">{sig ? pct(sig.qber) : '—'}</td>
            </tr>
            <tr className="border-t border-gray-800">
              <td className="py-1.5 text-amber-300">ν = {mu_decoy.toFixed(2)} (decoy)</td>
              <td className="text-right">{dec?.pulses ?? 0}</td>
              <td className="text-right">{dec?.detections ?? 0}</td>
              <td className="text-right">{dec ? dec.gain.toFixed(5) : '—'}</td>
              <td className="text-right">{dec ? pct(dec.qber) : '—'}</td>
            </tr>
            <tr className="border-t border-gray-800">
              <td className="py-1.5 text-gray-400">0 (vacuum)</td>
              <td className="text-right">{vac?.pulses ?? 0}</td>
              <td className="text-right">{vac?.detections ?? 0}</td>
              <td className="text-right">{vac ? vac.gain.toFixed(5) : '0.00000'}</td>
              <td className="text-right">—</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Bounds */}
      {bounds?.valid && (
        <div className="bg-amber-950 border border-amber-800 rounded-lg px-4 py-3">
          <p className="text-xs text-amber-400 mb-2 font-semibold">Single-photon bounds (decoy estimation)</p>
          <div className="grid grid-cols-3 gap-3 text-center text-xs">
            <div>
              <p className="text-gray-500">Y₁ lower bound</p>
              <p className="font-mono text-amber-200 text-sm">{bounds.Y_1.toFixed(5)}</p>
            </div>
            <div>
              <p className="text-gray-500">e₁ upper bound</p>
              <p className="font-mono text-amber-200 text-sm">{pct(bounds.e_1)}</p>
            </div>
            <div>
              <p className="text-gray-500">Q₁ = μ·e⁻μ·Y₁</p>
              <p className="font-mono text-amber-200 text-sm">{bounds.Q_1.toFixed(5)}</p>
            </div>
          </div>
        </div>
      )}

      {/* PNS verdict */}
      <div className={`flex items-start gap-3 rounded-lg px-4 py-3 ${
        secure_key_rate > 0
          ? 'bg-green-950 border border-green-800'
          : 'bg-red-950 border border-red-800'
      }`}>
        {secure_key_rate > 0 ? (
          <ShieldCheck className="text-green-400 shrink-0 mt-0.5" size={16} />
        ) : (
          <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={16} />
        )}
        <div className="text-xs">
          {secure_key_rate > 0 ? (
            <>
              <p className="text-green-300 font-semibold">PNS-resistant secure key derivable</p>
              <p className="text-green-500 mt-0.5">
                The decoy-state bounds show a positive key rate even accounting for
                {' '}{pns_vulnerable} multi-photon pulses Eve could have intercepted via PNS.
              </p>
            </>
          ) : (
            <>
              <p className="text-red-300 font-semibold">Key rate insufficient for PNS-secure key</p>
              <p className="text-red-500 mt-0.5">
                Decoy-state analysis yields R ≤ 0 — channel too lossy or too noisy
                to derive a key secure against PNS at the chosen intensities.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
