export default function SimulationControls({ config, onChange, onRun, loading }) {
  return (
    <div className="flex flex-col gap-5 h-full">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
        Simulation
      </h2>

      <SliderField
        label="Qubits"
        value={config.n_qubits}
        min={10} max={500} step={10}
        display={config.n_qubits}
        onChange={v => onChange('n_qubits', v)}
      />

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

      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-300">Simulate Eve</span>
        <button
          onClick={() => onChange('eve_intercept', !config.eve_intercept)}
          className={`relative inline-flex w-12 h-6 rounded-full transition-colors duration-200 ${
            config.eve_intercept ? 'bg-purple-500' : 'bg-gray-600'
          }`}
        >
          <span className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 ${
            config.eve_intercept ? 'translate-x-6' : 'translate-x-0'
          }`} />
        </button>
      </div>

      {config.eve_intercept && (
        <p className="text-xs text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">
          Eve intercepts 100% of qubits — expect QBER ~25%.
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
              Running…
            </>
          ) : 'Run Simulation'}
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
