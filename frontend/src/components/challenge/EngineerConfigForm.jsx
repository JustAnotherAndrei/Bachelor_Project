// Engineer-mission config picker. Renders one input per field in
// `mission.user_chooses` and emits a flat config object via onSubmit.

import { useMemo, useState } from 'react'
import { Wrench } from 'lucide-react'

const FIELD_SPEC = {
  protocol: {
    label: 'Protocol',
    type: 'select',
    options: [
      { value: 'bb84',   label: 'BB84' },
      { value: 'b92',    label: 'B92' },
      { value: 'sarg04', label: 'SARG04' },
      { value: 'e91',    label: 'E91' },
    ],
    default: 'bb84',
  },
  ec_method: {
    label: 'Error correction',
    type: 'select',
    options: [
      { value: 'cascade', label: 'CASCADE (Brassard-Salvail 1994)' },
      { value: 'parity',  label: 'Parity-block (discards on mismatch)' },
    ],
    default: 'cascade',
  },
  source_type: {
    label: 'Photon source',
    type: 'select',
    options: [
      { value: 'ideal', label: 'Ideal single-photon' },
      { value: 'wcp',   label: 'WCP + Decoy state' },
    ],
    default: 'ideal',
  },
  n_qubits: {
    label: 'Qubit budget',
    type: 'number',
    min: 50, max: 10000, step: 50,
    default: 500,
  },
  mu_signal: {
    label: 'μ signal intensity',
    type: 'slider',
    min: 0.1, max: 1.0, step: 0.05,
    default: 0.5,
    display: v => v.toFixed(2),
  },
  mu_decoy: {
    label: 'ν decoy intensity',
    type: 'slider',
    min: 0.02, max: 0.4, step: 0.02,
    default: 0.1,
    display: v => v.toFixed(2),
  },
  p_signal: {
    label: 'P(signal)',
    type: 'slider',
    min: 0.4, max: 0.9, step: 0.05,
    default: 0.7,
    display: v => v.toFixed(2),
  },
  p_decoy: {
    label: 'P(decoy)',
    type: 'slider',
    min: 0.05, max: 0.4, step: 0.05,
    default: 0.15,
    display: v => v.toFixed(2),
  },
}


export default function EngineerConfigForm({ mission, onSubmit, disabled }) {
  const fields = mission.user_chooses || []

  const initial = useMemo(() => {
    const o = {}
    for (const f of fields) {
      if (FIELD_SPEC[f]) o[f] = FIELD_SPEC[f].default
    }
    return o
  }, [fields])

  const [values, setValues] = useState(initial)

  function set(k, v) { setValues(prev => ({ ...prev, [k]: v })) }

  return (
    <div className="bg-gray-900 border border-emerald-800/40 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-1">
        <Wrench className="text-emerald-400" size={16} />
        <h3 className="text-sm font-semibold text-gray-200">Engineer config</h3>
      </div>
      <p className="text-xs text-gray-500 mb-4">
        Pick the values you want to test. Other parameters are fixed by the scenario.
      </p>

      <div className="flex flex-col gap-4">
        {fields.map(f => {
          const spec = FIELD_SPEC[f]
          if (!spec) return null
          if (spec.type === 'select') {
            return (
              <div key={f} className="flex flex-col gap-1.5">
                <label className="text-xs text-gray-400">{spec.label}</label>
                <select
                  value={values[f]}
                  onChange={e => set(f, e.target.value)}
                  disabled={disabled}
                  className="bg-gray-800 border border-gray-700 text-gray-100 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500 disabled:opacity-50"
                >
                  {spec.options.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            )
          }
          if (spec.type === 'number') {
            return (
              <div key={f} className="flex flex-col gap-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">{spec.label}</span>
                  <span className="text-emerald-400 font-mono">{values[f]}</span>
                </div>
                <input
                  type="range"
                  min={spec.min} max={spec.max} step={spec.step}
                  value={values[f]}
                  onChange={e => set(f, Number(e.target.value))}
                  disabled={disabled}
                  className="w-full accent-emerald-500"
                />
              </div>
            )
          }
          if (spec.type === 'slider') {
            const display = spec.display ? spec.display(values[f]) : values[f]
            return (
              <div key={f} className="flex flex-col gap-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">{spec.label}</span>
                  <span className="text-emerald-400 font-mono">{display}</span>
                </div>
                <input
                  type="range"
                  min={spec.min} max={spec.max} step={spec.step}
                  value={values[f]}
                  onChange={e => set(f, Number(e.target.value))}
                  disabled={disabled}
                  className="w-full accent-emerald-500"
                />
              </div>
            )
          }
          return null
        })}
      </div>

      <button
        onClick={() => onSubmit(values)}
        disabled={disabled}
        className="mt-5 w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg transition-colors"
      >
        Run simulation with these settings
      </button>
    </div>
  )
}
