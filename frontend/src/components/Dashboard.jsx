import { useState, useEffect, useRef } from 'react'
import { Shield } from 'lucide-react'
import StatusBadge from './StatusBadge'
import SimulationControls from './SimulationControls'
import QBERChart from './QBERChart'
import PhotonGrid from './PhotonGrid'
import SimulationSummary from './SimulationSummary'
import useSimulationSocket from '../hooks/useSimulationSocket'
import EducationalPanel from './EducationalPanel'
import KeyRateChart from './KeyRateChart'

const DEFAULT_CONFIG = {
  n_qubits: 100,
  depolarizing_prob: 0.01,
  measurement_error_prob: 0.02,
  eve_mode: 'none',
  mode: 'simulator',
  ibm_backend: 'ibm_fez',
  channel_distance_km: 0,
  ec_method: 'cascade',
}

export default function Dashboard() {
  const [config, setConfig] = useState(DEFAULT_CONFIG)
  const [history, setHistory] = useState([])
  const { result, summary, loading, complete, progress, statusMessage, run, cancel } = useSimulationSocket()

  useEffect(() => {
    fetch('/api/v1/history')
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => setHistory(data))
      .catch(() => {})
  }, [])

  const prevCompleteRef = useRef(false)
  useEffect(() => {
    if (complete && !prevCompleteRef.current && result) {
      setHistory(prev => [...prev, result])
    }
    prevCompleteRef.current = complete
  }, [complete, result])

  function handleChange(key, value) {
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  function handleClearHistory() {
    if (!window.confirm('Clear all simulation history? This action cannot be undone. Be careful...')) return
    fetch('/api/v1/history', { method: 'DELETE' })
      .then(r => r.ok ? setHistory([]) : Promise.reject(r.status))
      .catch(() => {})
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">

      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="text-violet-400" size={28} />
          <span className="text-xl font-semibold tracking-tight">Sequre</span>
          <span className="text-xs text-gray-500 font-mono">BB84 QKD Platform</span>
        </div>
        <StatusBadge online />
      </header>

      <main className="flex flex-1 gap-6 p-6">

        <aside className="w-72 shrink-0 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <SimulationControls
            config={config}
            onChange={handleChange}
            onRun={() => run(config)}
            onCancel={cancel}
            loading={loading}
            statusMessage={statusMessage}
          />
        </aside>

        <section className="flex-1 flex flex-col gap-4">
          <div className="grid grid-cols-3 gap-4">
            <StatCard
              label="Sifted Key Length"
              value={result?.sifted_key_length ?? '—'}
              unit={result?.sifted_key_length != null ? 'bits' : ''}
            />
            <StatCard
              label="QBER"
              value={result?.qber != null ? `${(result.qber * 100).toFixed(1)}` : '—'}
              unit={result?.qber != null ? '%' : ''}
            />
            <StatCard
              label="Channel Status"
              value={result?.is_secure != null ? (result.is_secure ? 'Secure' : 'Compromised') : '—'}
              accent={result?.is_secure != null ? (result.is_secure ? 'green' : 'red') : 'gray'}
            />
            {result?.channel_distance_km > 0 && (
              <StatCard
                label={`Transmission (${result.channel_distance_km} km)`}
                value={result.transmission_efficiency != null
                  ? `${(result.transmission_efficiency * 100).toFixed(1)}`
                  : '—'}
                unit={result.transmission_efficiency != null ? '%' : ''}
                accent="blue"
              />
            )}
          </div>

          <PhotonGrid result={result} loading={loading} progress={progress} />
          {summary && (
            <SimulationSummary summary={summary} eveMode={config.eve_mode} />
          )}
          <QBERChart history={history} onClear={handleClearHistory} />
          <KeyRateChart
            depProb={config.depolarizing_prob}
            measProb={config.measurement_error_prob}
            currentDistance={config.channel_distance_km}
          />
          <EducationalPanel />
        </section>

      </main>
    </div>
  )
}

function StatCard({ label, value, unit, accent = 'gray' }) {
  const colors = {
    gray: 'text-gray-100',
    green: 'text-green-400',
    red: 'text-red-400',
    blue: 'text-blue-300',
  }
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-mono font-semibold ${colors[accent]}`}>
        {value}
        {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
      </p>
    </div>
  )
}
