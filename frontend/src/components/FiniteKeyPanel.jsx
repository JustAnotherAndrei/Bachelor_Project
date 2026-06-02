import { Infinity as InfinityIcon, Scale, AlertTriangle, CheckCircle2 } from 'lucide-react'

export default function FiniteKeyPanel({ fk }) {
  if (!fk || !fk.valid) return null

  const asymp = fk.asymptotic_length
  const finite = fk.finite_length
  const finiteRaw = fk.finite_length_raw
  const cost = fk.cost
  const denom = Math.max(asymp, 1)
  const finitePct = Math.max(0, Math.min(100, (finite / denom) * 100))

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Scale className="text-cyan-400" size={18} />
        <h3 className="text-sm font-semibold text-gray-200">Finite-Key Security Analysis</h3>
        <span className="text-xs text-cyan-300 font-mono ml-auto">Tomamichel 2012</span>
      </div>

      <p className="text-xs text-gray-400 mb-4 leading-relaxed">
        Real protocols use a finite block of N qubits, so the QBER estimate
        carries statistical uncertainty (Hoeffding correction δ<sub>PE</sub>).
        Composable security requires extra privacy-amplification overhead.
        The finite-key bound below is what a rigorous proof would actually
        certify — the asymptotic figure is only an idealised upper limit.
      </p>

      {/* Big number comparison */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <InfinityIcon size={12} className="text-gray-400" />
            <span className="text-[10px] uppercase tracking-wider text-gray-500">Asymptotic (N→∞)</span>
          </div>
          <p className="text-2xl font-mono text-gray-300">{asymp.toFixed(0)} <span className="text-xs text-gray-500">bits</span></p>
          <p className="text-[11px] text-gray-500 mt-1">
            Idealised GLLP rate, no statistical penalty.
          </p>
        </div>
        <div className={`border rounded-lg p-3 ${
          fk.secure
            ? 'bg-emerald-950 border-emerald-700'
            : 'bg-red-950 border-red-800'
        }`}>
          <div className="flex items-center gap-1.5 mb-1">
            {fk.secure ? (
              <CheckCircle2 size={12} className="text-emerald-300" />
            ) : (
              <AlertTriangle size={12} className="text-red-300" />
            )}
            <span className={`text-[10px] uppercase tracking-wider ${
              fk.secure ? 'text-emerald-300' : 'text-red-300'
            }`}>
              Finite-key (N = {fk.n_sifted})
            </span>
          </div>
          <p className={`text-2xl font-mono ${fk.secure ? 'text-emerald-200' : 'text-red-200'}`}>
            {finite.toFixed(0)} <span className="text-xs text-gray-500">bits</span>
          </p>
          <p className="text-[11px] text-gray-500 mt-1">
            {fk.secure
              ? 'Rigorous bound — secure under composable security.'
              : 'Insufficient N — bound collapses (raw value: ' + finiteRaw.toFixed(0) + ').'}
          </p>
        </div>
      </div>

      {/* Bar comparison */}
      <div className="mb-4">
        <div className="flex justify-between text-[11px] text-gray-500 mb-1">
          <span>Finite-key / asymptotic ratio</span>
          <span className="font-mono">
            {asymp > 0 ? ((finite / asymp) * 100).toFixed(1) : '0.0'}%
          </span>
        </div>
        <div className="relative h-3 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="absolute left-0 top-0 h-full bg-gray-600"
            style={{ width: '100%' }}
            title="Asymptotic"
          />
          <div
            className={`absolute left-0 top-0 h-full ${fk.secure ? 'bg-cyan-500' : 'bg-red-500'}`}
            style={{ width: `${finitePct}%` }}
          />
        </div>
        <p className="text-[11px] text-gray-500 mt-1">
          Gap of <span className="text-yellow-300 font-mono">{cost.toFixed(0)} bits</span>
          {' '}sacrificed for finite-N rigour.
        </p>
      </div>

      {/* Breakdown */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <Row label="QBER (measured)" value={`${(fk.qber * 100).toFixed(2)}%`} />
        <Row label="QBER + δ (worst case)" value={`${(fk.qber_upper * 100).toFixed(2)}%`} />
        <Row label="Hoeffding δ_PE" value={fk.delta_pe.toFixed(4)} />
        <Row label="h(Q) entropy" value={fk.h_q.toFixed(4)} />
        <Row label="Leak EC (Slepian-Wolf)" value={`${fk.leak_ec.toFixed(0)} bits`} />
        <Row label="PA overhead" value={`${fk.pa_overhead.toFixed(0)} bits`} />
        <Row label="ε_sec total" value={fk.eps_sec_total.toExponential(0)} mono />
        <Row label="EC efficiency f" value={fk.f_ec.toFixed(2)} mono />
      </div>

      {!fk.secure && (
        <p className="text-xs text-yellow-300 bg-yellow-950 border border-yellow-800 rounded-lg px-3 py-2 mt-3">
          With ε_sec = {fk.eps_sec_total.toExponential(0)}, this run's sifted key (N = {fk.n_sifted})
          is below the finite-key threshold. Increase the qubit count or lower QBER to obtain
          a positive bound.
        </p>
      )}
    </div>
  )
}

function Row({ label, value, mono }) {
  return (
    <div className="flex justify-between bg-gray-800 border border-gray-700 rounded-md px-2 py-1.5">
      <span className="text-gray-400">{label}</span>
      <span className={`text-gray-100 ${mono ? 'font-mono' : 'font-mono'}`}>{value}</span>
    </div>
  )
}
