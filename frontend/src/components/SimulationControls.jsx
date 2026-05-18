const IBM_BACKENDS = ['ibm_fez', 'ibm_marrakesh', 'ibm_kingston']

export default function SimulationControls({ config, onChange, onRun, loading, statusMessage }) {
  const isIBM = config.mode === 'ibm_hardware'

  return (
    <div className="flex flex-col gap-5 h-full">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
        Simulation
      </h2>

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
          onClick={() => onChange('mode', 'ibm_hardware')}
          className={`flex-1 py-2 transition-colors ${
            isIBM ? 'bg-violet-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200'
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
        min={10} max={isIBM ? 30 : 500} step={isIBM ? 5 : 10}
        display={config.n_qubits}
        onChange={v => onChange('n_qubits', v)}
      />

      {/* Noise sliders — only for simulator */}
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
        </>
      )}

      {isIBM && (
        <p className="text-xs text-gray-500">
          Noise is determined by real hardware — sliders not applicable.
        </p>
      )}

      {/* Eve mode selector */}
      <div className="flex flex-col gap-1.5">
        <span className="text-sm text-gray-300">Eve</span>
        <div className="flex rounded-lg overflow-hidden border border-gray-700 text-xs font-medium">
          {[
            { value: 'none',   label: 'None' },
            { value: 'weak',   label: 'Weak' },
            { value: 'strong', label: 'Strong' },
          ].map(opt => (
            <button
              key={opt.value}
              onClick={() => onChange('eve_mode', opt.value)}
              className={`flex-1 py-2 transition-colors ${
                config.eve_mode === opt.value
                  ? opt.value === 'strong' ? 'bg-red-700 text-white'
                    : opt.value === 'weak' ? 'bg-orange-600 text-white'
                    : 'bg-gray-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
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

      <div className="mt-auto">
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
