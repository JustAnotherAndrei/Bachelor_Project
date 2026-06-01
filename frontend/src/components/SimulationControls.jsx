const IBM_BACKENDS = ['ibm_fez', 'ibm_marrakesh', 'ibm_kingston']

const PROTOCOLS = [
  { value: 'bb84',   label: 'BB84',   blurb: 'Bennett-Brassard 1984. 4 states, 2 bases. Reference protocol.' },
  { value: 'b92',    label: 'B92',    blurb: 'Bennett 1992. Only 2 non-orthogonal states (|0⟩, |+⟩). Simpler hardware, ~25% sift.' },
  { value: 'sarg04', label: 'SARG04', blurb: 'Scarani-Acin-Ribordy-Gisin 2004. Same 4 states as BB84, pair announcement. PNS-resistant.' },
  { value: 'e91',    label: 'E91',    blurb: 'Ekert 1991. Entangled photon pairs + CHSH Bell test. Eavesdropping = Bell violation collapse.' },
]

export default function SimulationControls({ config, onChange, onRun, onCancel, loading, statusMessage }) {
  const isIBM = config.mode === 'ibm_hardware'
  const protocol = config.protocol || 'bb84'
  const isBB84 = protocol === 'bb84'
  const protocolBlurb = PROTOCOLS.find(p => p.value === protocol)?.blurb

  return (
    <div className="flex flex-col gap-5 h-full">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
        Simulation
      </h2>

      {/* Protocol selector */}
      <div className="flex flex-col gap-1.5">
        <span className="text-sm text-gray-300">Protocol</span>
        <div className="grid grid-cols-4 rounded-lg overflow-hidden border border-gray-700 text-xs font-medium">
          {PROTOCOLS.map(p => (
            <button
              key={p.value}
              onClick={() => onChange('protocol', p.value)}
              disabled={isIBM && p.value !== 'bb84'}
              className={`py-2 transition-colors ${
                protocol === p.value
                  ? 'bg-emerald-700 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-200 disabled:opacity-40 disabled:cursor-not-allowed'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        {protocolBlurb && (
          <p className="text-xs text-emerald-300 bg-emerald-950 border border-emerald-800 rounded-lg px-3 py-2">
            {protocolBlurb}
          </p>
        )}
        {!isBB84 && (
          <p className="text-xs text-gray-500">
            Decoy-state, Smart Eve, and IBM hardware are available only for BB84.
          </p>
        )}
      </div>

      {/* Mode toggle */}
      <div className="flex rounded-lg overflow-hidden border border-gray-700 text-xs font-medium">
        <button
          onClick={() => onChange('mode', 'simulator')}
          className={`flex-1 py-2 transition-colors ${
            !isIBM ? 'bg-violet-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200'
          }`}
        >
          Simulator
        </button>
        <button
          onClick={() => isBB84 && onChange('mode', 'ibm_hardware')}
          disabled={!isBB84}
          className={`flex-1 py-2 transition-colors ${
            isIBM ? 'bg-violet-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200 disabled:opacity-40 disabled:cursor-not-allowed'
          }`}
        >
          IBM Hardware
        </button>
      </div>

      {/* IBM backend selector */}
      {isIBM && (
        <div className="flex flex-col gap-1.5">
          <span className="text-sm text-gray-300">Backend</span>
          <select
            value={config.ibm_backend}
            onChange={e => onChange('ibm_backend', e.target.value)}
            className="bg-gray-800 border border-gray-700 text-gray-100 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-violet-500"
          >
            {IBM_BACKENDS.map(b => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
          <p className="text-xs text-yellow-500 bg-yellow-950 border border-yellow-800 rounded-lg px-3 py-2 mt-1">
            Hardware jobs may take several minutes. Recommend ≤ 30 qubits.
          </p>
        </div>
      )}

      <SliderField
        label="Qubits"
        value={config.n_qubits}
        min={10} max={isIBM ? 30 : 10000} step={isIBM ? 5 : 50}
        display={config.n_qubits}
        onChange={v => onChange('n_qubits', v)}
      />
      {!isIBM && config.n_qubits > 2000 && (
        <p className="text-xs text-gray-500">
          Large runs ({config.n_qubits.toLocaleString()} qubits) may take several seconds and produce dense PhotonGrid output.
        </p>
      )}

      {/* Noise + channel sliders — only for simulator */}
      {!isIBM && (
        <>
          <SliderField
            label="Depolarizing noise"
            value={config.depolarizing_prob}
            min={0} max={0.2} step={0.005}
            display={`${(config.depolarizing_prob * 100).toFixed(1)}%`}
            onChange={v => onChange('depolarizing_prob', v)}
          />
          <SliderField
            label="Measurement error"
            value={config.measurement_error_prob}
            min={0} max={0.2} step={0.005}
            display={`${(config.measurement_error_prob * 100).toFixed(1)}%`}
            onChange={v => onChange('measurement_error_prob', v)}
          />
          <SliderField
            label="Channel distance"
            value={config.channel_distance_km}
            min={0} max={150} step={5}
            display={config.channel_distance_km === 0 ? 'No loss' : `${config.channel_distance_km} km`}
            onChange={v => onChange('channel_distance_km', v)}
          />
          {config.channel_distance_km > 0 && (
            <p className="text-xs text-blue-400 bg-blue-950 border border-blue-800 rounded-lg px-3 py-2">
              η ≈ {(Math.pow(10, -0.2 * config.channel_distance_km / 10) * 100).toFixed(1)}% photon transmission
              (SMF-28, α = 0.2 dB/km)
            </p>
          )}
        </>
      )}

      {isIBM && (
        <p className="text-xs text-gray-500">
          Noise is determined by real hardware — sliders not applicable.
        </p>
      )}

      {/* Photon source selector — simulator + BB84 only */}
      {!isIBM && isBB84 && (
        <div className="flex flex-col gap-1.5">
          <span className="text-sm text-gray-300">Photon source</span>
          <div className="flex rounded-lg overflow-hidden border border-gray-700 text-xs font-medium">
            <button
              onClick={() => onChange('source_type', 'ideal')}
              className={`flex-1 py-2 transition-colors ${
                config.source_type === 'ideal'
                  ? 'bg-amber-700 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-200'
              }`}
            >
              Ideal single-photon
            </button>
            <button
              onClick={() => onChange('source_type', 'wcp')}
              className={`flex-1 py-2 transition-colors ${
                config.source_type === 'wcp'
                  ? 'bg-amber-700 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-200'
              }`}
            >
              WCP + Decoy
            </button>
          </div>
          {config.source_type === 'wcp' && (
            <>
              <p className="text-xs text-amber-400 bg-amber-950 border border-amber-800 rounded-lg px-3 py-2">
                Weak coherent pulses (Poisson) with 3-intensity decoy-state
                (Lo-Ma-Chen 2005). Defends against PNS attacks.
              </p>
              <SliderField
                label="μ signal"
                value={config.mu_signal}
                min={0.1} max={1.0} step={0.05}
                display={config.mu_signal.toFixed(2)}
                onChange={v => onChange('mu_signal', v)}
              />
              <SliderField
                label="ν decoy"
                value={config.mu_decoy}
                min={0.02} max={0.4} step={0.02}
                display={config.mu_decoy.toFixed(2)}
                onChange={v => onChange('mu_decoy', v)}
              />
            </>
          )}
        </div>
      )}

      {/* Error correction selector */}
      <div className="flex flex-col gap-1.5">
        <span className="text-sm text-gray-300">Error correction</span>
        <div className="flex rounded-lg overflow-hidden border border-gray-700 text-xs font-medium">
          <button
            onClick={() => onChange('ec_method', 'parity')}
            className={`flex-1 py-2 transition-colors ${
              config.ec_method === 'parity'
                ? 'bg-blue-700 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-gray-200'
            }`}
          >
            Parity-block
          </button>
          <button
            onClick={() => onChange('ec_method', 'cascade')}
            className={`flex-1 py-2 transition-colors ${
              config.ec_method === 'cascade'
                ? 'bg-blue-700 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-gray-200'
            }`}
          >
            CASCADE
          </button>
        </div>
        <p className="text-xs text-gray-500">
          {config.ec_method === 'cascade'
            ? 'Iterative bit-level reconciliation (Brassard-Salvail 1994).'
            : 'Discards whole 4-bit blocks on parity mismatch.'}
        </p>
      </div>

      {/* Eve mode selector */}
      <div className="flex flex-col gap-1.5">
        <span className="text-sm text-gray-300">Eve</span>
        <div className="grid grid-cols-4 rounded-lg overflow-hidden border border-gray-700 text-xs font-medium">
          {[
            { value: 'none',   label: 'None',   activeBg: 'bg-gray-600',   bb84Only: false },
            { value: 'weak',   label: 'Weak',   activeBg: 'bg-orange-600', bb84Only: false },
            { value: 'strong', label: 'Strong', activeBg: 'bg-red-700',    bb84Only: false },
            { value: 'smart',  label: 'Smart',  activeBg: 'bg-purple-700', bb84Only: true  },
          ].map(opt => {
            const disabled = opt.bb84Only && !isBB84
            return (
              <button
                key={opt.value}
                onClick={() => !disabled && onChange('eve_mode', opt.value)}
                disabled={disabled}
                className={`py-2 transition-colors ${
                  config.eve_mode === opt.value
                    ? `${opt.activeBg} text-white`
                    : 'bg-gray-800 text-gray-400 hover:text-gray-200 disabled:opacity-40 disabled:cursor-not-allowed'
                }`}
              >
                {opt.label}
              </button>
            )
          })}
        </div>
        {config.eve_mode === 'smart' && (
          <>
            <p className="text-xs text-purple-300 bg-purple-950 border border-purple-800 rounded-lg px-3 py-2">
              Adaptive intercept-resend — Eve tracks running QBER and throttles
              herself to stay below the abort threshold.
            </p>
            <SliderField
              label="Target QBER (Eve's ceiling)"
              value={config.smart_target_qber}
              min={0.02} max={0.11} step={0.005}
              display={`${(config.smart_target_qber * 100).toFixed(1)}%`}
              onChange={v => onChange('smart_target_qber', v)}
            />
          </>
        )}
      </div>

      {config.eve_mode === 'weak' && (
        <p className="text-xs text-orange-400 bg-orange-950 border border-orange-800 rounded-lg px-3 py-2">
          Eve intercepts ~30% of qubits — QBER may stay below 11% threshold.
        </p>
      )}
      {config.eve_mode === 'strong' && (
        <p className="text-xs text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">
          Eve intercepts 100% of qubits — expect QBER ~25%, channel compromised.
        </p>
      )}

      {/* IBM status messages */}
      {statusMessage && (
        <p className="text-xs text-violet-300 bg-violet-950 border border-violet-800 rounded-lg px-3 py-2 flex items-center gap-2">
          <span className="w-3 h-3 border-2 border-violet-400/40 border-t-violet-400 rounded-full animate-spin shrink-0" />
          {statusMessage}
        </p>
      )}

      <div className="mt-auto flex flex-col gap-2">
        <button
          onClick={onRun}
          disabled={loading}
          className="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              {isIBM ? 'Running on IBM…' : 'Running…'}
            </>
          ) : isIBM ? 'Run on IBM Hardware' : 'Run Simulation'}
        </button>
        {loading && (
          <button
            onClick={onCancel}
            className="w-full bg-gray-700 hover:bg-gray-600 text-gray-300 font-medium py-2 rounded-lg transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}

function SliderField({ label, value, min, max, step, display, onChange }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-gray-300">{label}</span>
        <span className="text-violet-400 font-mono">{display}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full accent-violet-500"
      />
    </div>
  )
}
