import { useState } from 'react'
import { ShieldCheck, ShieldAlert, AlertTriangle, Clock, Key, ArrowRight, Copy, Check, Lock, LockOpen } from 'lucide-react'

function formatElapsed(seconds) {
  if (seconds == null) return '—'
  if (seconds < 60) return `${seconds.toFixed(2)}s`
  const m = Math.floor(seconds / 60)
  const s = (seconds % 60).toFixed(0).padStart(2, '0')
  return `${m}m ${s}s`
}

function pct(num, den) {
  if (!den) return '0%'
  return `${((num / den) * 100).toFixed(1)}%`
}

function formatKey(hex) {
  return hex.match(/.{1,4}/g).join(' ')
}

function StatusBanner({ isSecure, qber, eveMode }) {
  if (!isSecure) {
    return (
      <div className="flex items-start gap-3 bg-red-950 border border-red-700 rounded-xl px-4 py-3">
        <ShieldAlert className="text-red-400 shrink-0 mt-0.5" size={20} />
        <div>
          <p className="text-red-300 font-semibold text-sm">Eavesdropper Detected</p>
          <p className="text-red-500 text-xs mt-0.5">
            QBER {(qber * 100).toFixed(1)}% exceeds 11% security threshold. Key exchange aborted.
          </p>
        </div>
      </div>
    )
  }
  if (eveMode === 'none') {
    return (
      <div className="flex items-start gap-3 bg-green-950 border border-green-700 rounded-xl px-4 py-3">
        <ShieldCheck className="text-green-400 shrink-0 mt-0.5" size={20} />
        <div>
          <p className="text-green-300 font-semibold text-sm">Channel Secure</p>
          <p className="text-green-500 text-xs mt-0.5">No eavesdropping detected. Key exchange successful.</p>
        </div>
      </div>
    )
  }
  return (
    <div className="flex items-start gap-3 bg-orange-950 border border-orange-700 rounded-xl px-4 py-3">
      <AlertTriangle className="text-orange-400 shrink-0 mt-0.5" size={20} />
      <div>
        <p className="text-orange-300 font-semibold text-sm">
          {eveMode === 'strong' ? 'Strong Eve — Below Threshold' : 'Potential Weak Eavesdropping'}
        </p>
        <p className="text-orange-500 text-xs mt-0.5">
          QBER {(qber * 100).toFixed(1)}% — below 11% threshold
          {eveMode === 'strong'
            ? ', but strong interception was active. Small sample size may mask errors.'
            : ', but channel may be partially compromised.'}
        </p>
      </div>
    </div>
  )
}

function PipelineStep({ label, value, subtext, accent = 'gray' }) {
  const colors = {
    gray: 'text-gray-100 border-gray-700',
    violet: 'text-violet-300 border-violet-700',
    blue: 'text-blue-300 border-blue-700',
    green: 'text-green-300 border-green-700',
  }
  return (
    <div className={`flex flex-col items-center border rounded-lg px-3 py-2 min-w-0 ${colors[accent]}`}>
      <span className="text-xs text-gray-500 whitespace-nowrap">{label}</span>
      <span className="text-lg font-mono font-bold">{value}</span>
      <span className="text-xs text-gray-500">{subtext}</span>
    </div>
  )
}

function FinalKeyDisplay({ finalKey, isSecure }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(finalKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!isSecure) {
    return (
      <div className="flex items-start gap-3 bg-red-950 border border-red-800 rounded-lg px-4 py-3">
        <LockOpen className="text-red-400 shrink-0 mt-0.5" size={15} />
        <div>
          <p className="text-red-300 text-sm font-medium">Key exchange aborted</p>
          <p className="text-red-500 text-xs mt-0.5">
            QBER exceeded the security threshold — no shared key was established.
          </p>
        </div>
      </div>
    )
  }

  if (!finalKey) {
    return (
      <div className="flex items-start gap-3 bg-yellow-950 border border-yellow-800 rounded-lg px-4 py-3">
        <AlertTriangle className="text-yellow-400 shrink-0 mt-0.5" size={15} />
        <div>
          <p className="text-yellow-300 text-sm font-medium">Insufficient key material</p>
          <p className="text-yellow-500 text-xs mt-0.5">
            Error correction discarded all bits — try more qubits or lower noise.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-3 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3">
        <Lock className="text-green-400 shrink-0" size={14} />
        <span className="font-mono text-sm text-green-300 tracking-wider flex-1 break-all select-all">
          {formatKey(finalKey)}
        </span>
        <button
          onClick={handleCopy}
          title={copied ? 'Copied!' : 'Copy key'}
          className="shrink-0 p-1.5 rounded-md bg-gray-700 hover:bg-gray-600 text-gray-400 hover:text-white transition-colors"
        >
          {copied
            ? <Check size={14} className="text-green-400" />
            : <Copy size={14} />}
        </button>
      </div>
      <p className="text-xs text-gray-500">
        128-bit key · SHA-256 privacy amplification · usable with AES-128 symmetric encryption
      </p>
    </div>
  )
}

export default function SimulationSummary({ summary, eveMode = 'none' }) {
  if (!summary) return null

  const {
    n_qubits_sent, n_qubits_received, transmission_efficiency, channel_distance_km,
    sifted_key_length, bits_after_ec,
    final_key, qber, is_secure, elapsed_seconds, mode, ibm_backend,
    ec_method, ec_stats,
  } = summary
  const hasChannelLoss = channel_distance_km > 0
  const isCascade = ec_method === 'cascade'

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
          Simulation Summary
        </h3>
        <div className="flex items-center gap-1.5 text-xs text-gray-500 font-mono">
          <Clock size={12} />
          {formatElapsed(elapsed_seconds)}
          {mode === 'ibm_hardware' && (
            <span className="ml-2 text-violet-400">· {ibm_backend}</span>
          )}
        </div>
      </div>

      <StatusBanner isSecure={is_secure} qber={qber} eveMode={eveMode} />

      {isCascade && ec_stats && (
        <div className="bg-blue-950 border border-blue-800 rounded-lg px-4 py-3 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-blue-300 uppercase tracking-widest">
              CASCADE Reconciliation
            </p>
            <span className="text-xs text-blue-500 font-mono">Brassard-Salvail 1994</span>
          </div>
          <div className="grid grid-cols-4 gap-3 text-center">
            <div>
              <p className="text-xs text-gray-500">Initial errors</p>
              <p className="text-sm font-mono font-semibold text-orange-300">
                {ec_stats.initial_errors}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Remaining</p>
              <p className={`text-sm font-mono font-semibold ${
                ec_stats.remaining_errors === 0 ? 'text-green-300' : 'text-red-300'
              }`}>
                {ec_stats.remaining_errors}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Parity bits leaked</p>
              <p className="text-sm font-mono font-semibold text-blue-200">
                {ec_stats.parity_announcements}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Efficiency f</p>
              <p className="text-sm font-mono font-semibold text-blue-200">
                {ec_stats.efficiency}
                <span className="text-xs text-gray-500 ml-1">/ Shannon</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Key distillation pipeline */}
      <div>
        <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
          <Key size={11} /> Key Distillation Pipeline
        </p>
        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          <PipelineStep label="Sent" value={n_qubits_sent} subtext="qubits" accent="gray" />
          {hasChannelLoss && (
            <>
              <ArrowRight size={14} className="text-gray-600 shrink-0" />
              <PipelineStep
                label="Received"
                value={n_qubits_received}
                subtext={pct(n_qubits_received, n_qubits_sent)}
                accent="gray"
              />
            </>
          )}
          <ArrowRight size={14} className="text-gray-600 shrink-0" />
          <PipelineStep
            label="Sifted key"
            value={sifted_key_length}
            subtext={pct(sifted_key_length, n_qubits_sent)}
            accent="violet"
          />
          <ArrowRight size={14} className="text-gray-600 shrink-0" />
          <PipelineStep
            label="After EC"
            value={bits_after_ec ?? '—'}
            subtext={bits_after_ec != null ? pct(bits_after_ec, n_qubits_sent) : ''}
            accent="blue"
          />
          <ArrowRight size={14} className="text-gray-600 shrink-0" />
          <PipelineStep
            label="Final key"
            value={is_secure && final_key ? '128' : '—'}
            subtext={is_secure && final_key ? 'bits · SHA-256' : ''}
            accent={is_secure && final_key ? 'green' : 'gray'}
          />
        </div>
      </div>

      {/* Stats row */}
      <div className={`grid gap-3 text-center ${hasChannelLoss ? 'grid-cols-4' : 'grid-cols-3'}`}>
        {hasChannelLoss && (
          <div className="bg-gray-800 rounded-lg px-3 py-2">
            <p className="text-xs text-gray-500">Channel transmission</p>
            <p className="text-sm font-mono font-semibold text-blue-300">
              {(transmission_efficiency * 100).toFixed(1)}%
              <span className="text-xs text-gray-500 ml-1">{channel_distance_km} km</span>
            </p>
          </div>
        )}
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Sifting efficiency</p>
          <p className="text-sm font-mono font-semibold text-gray-100">
            {pct(sifted_key_length, n_qubits_received)}
            <span className="text-xs text-gray-500 ml-1">~50% expected</span>
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Blocks discarded (EC)</p>
          <p className="text-sm font-mono font-semibold text-gray-100">
            {bits_after_ec != null ? (
              <>{sifted_key_length - bits_after_ec}<span className="text-xs text-gray-500 ml-1">bits</span></>
            ) : '—'}
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Key entropy input</p>
          <p className="text-sm font-mono font-semibold text-gray-100">
            {bits_after_ec != null ? (
              <>{bits_after_ec > 0 ? bits_after_ec : '—'}<span className="text-xs text-gray-500 ml-1">{bits_after_ec > 0 ? 'bits' : ''}</span></>
            ) : '—'}
          </p>
        </div>
      </div>

      {/* Final secret key */}
      <div>
        <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
          <Lock size={11} /> Final Secret Key
        </p>
        <FinalKeyDisplay finalKey={final_key} isSecure={is_secure} />
      </div>
    </div>
  )
}
