import { Skull, ShieldAlert, ShieldCheck } from 'lucide-react'

export default function PnsAttackPanel({ pns, decoy }) {
  if (!pns) return null

  const leakPct = (pns.info_leaked_fraction * 100).toFixed(2)
  const blockPct = (pns.block_rate * 100).toFixed(2)

  // Decoy detection: Y_1 lower bound collapses under PNS (Eve blocks all
  // single-photon pulses, so the decoy/signal gain ratio shifts sharply).
  // Normal Y_1 ≈ 0.15–0.5; under PNS it drops to < 0.05 and R → 0.
  const Y1 = decoy?.bounds?.Y_1
  const R = decoy?.secure_key_rate
  const detected = decoy && (
    (R !== undefined && R < 0.002) ||
    (Y1 !== undefined && Y1 < 0.05)
  )

  return (
    <div className="bg-gray-900 border border-pink-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Skull className="text-pink-400" size={18} />
        <h3 className="text-sm font-semibold text-gray-200">PNS Attack — Eve Splitting Photons</h3>
      </div>

      <p className="text-xs text-gray-400 mb-3 leading-relaxed">
        Eve performs a Photon-Number-Splitting attack: she blocks every
        single-photon pulse (cannot copy due to no-cloning) and splits every
        multi-photon pulse — keeping one photon in quantum memory until Alice
        announces the basis, then measuring it perfectly. The pulses she
        forwards reach Bob through a lossless replacement channel, so QBER
        stays low. The defence is the decoy-state method.
      </p>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <StatBox label="Pulses split (Eve has photon)" value={pns.n_split_multi} accent="pink" />
        <StatBox label="Pulses blocked (single-photon)" value={pns.n_blocked_single} accent="red" />
        <StatBox label="Info leaked to Eve" value={`${leakPct}%`} accent="pink" />
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs text-gray-400 mb-3">
        <Row label="Total pulses" value={pns.n_pulses} />
        <Row label="Vacuum pulses" value={pns.n_vacuum} />
        <Row label="Block rate (single-photon)" value={`${blockPct}%`} />
        <Row label="Multi-photon split rate" value={`${leakPct}%`} />
      </div>

      {decoy && (
        <div className={`mt-3 px-3 py-2 rounded-lg border ${
          detected
            ? 'bg-emerald-950 border-emerald-700'
            : 'bg-yellow-950 border-yellow-700'
        }`}>
          <div className="flex items-center gap-2 mb-1">
            {detected ? (
              <ShieldCheck size={14} className="text-emerald-300" />
            ) : (
              <ShieldAlert size={14} className="text-yellow-300" />
            )}
            <span className={`text-xs font-semibold ${
              detected ? 'text-emerald-200' : 'text-yellow-200'
            }`}>
              {detected
                ? 'Decoy-state caught the attack'
                : 'Decoy-state bounds suspicious'}
            </span>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            {detected ? (
              <>
                Single-photon yield <span className="font-mono text-emerald-300">Y₁ ≈ {Y1?.toFixed(4) ?? '0'}</span>
                {' '}and secure key rate <span className="font-mono text-emerald-300">R = {R?.toFixed(6) ?? '0'}</span>.
                {' '}Lo-Ma-Chen bounds exposed the PNS attack — Alice aborts the
                key.
              </>
            ) : (
              <>
                Y₁ = <span className="font-mono">{Y1?.toFixed(4) ?? '—'}</span>,
                R = <span className="font-mono">{R?.toFixed(6) ?? '—'}</span>.
                {' '}Attack present but bounds did not fully collapse — try a
                larger qubit count.
              </>
            )}
          </p>
        </div>
      )}

      {!decoy && (
        <p className="text-xs text-yellow-300 bg-yellow-950 border border-yellow-800 rounded-lg px-3 py-2 mt-3">
          No decoy-state analysis available — the attack proceeds undetected.
          Switch the Photon Source to <strong>WCP + Decoy</strong> to enable
          the standard defence.
        </p>
      )}
    </div>
  )
}

function StatBox({ label, value, accent = 'pink' }) {
  const colors = {
    pink: 'text-pink-300',
    red: 'text-red-300',
  }
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2">
      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{label}</p>
      <p className={`text-xl font-mono font-semibold ${colors[accent]}`}>{value}</p>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between bg-gray-800 border border-gray-700 rounded-md px-2 py-1.5">
      <span className="text-gray-400">{label}</span>
      <span className="text-gray-100 font-mono">{value}</span>
    </div>
  )
}
