import { useState, useEffect, useRef } from 'react'
import { Shield } from 'lucide-react'
import StatusBadge from './StatusBadge'
import SimulationControls from './SimulationControls'
import QBERChart from './QBERChart'
import PhotonGrid from './PhotonGrid'
import useSimulationSocket from '../hooks/useSimulationSocket'

const DEFAULT_CONFIG = {
  n_qubits: 100,
  depolarizing_prob: 0.01,
  measurement_error_prob: 0.02,
  eve_intercept: false,
}

export default function Dashboard() {
  const [config, setConfig] = useState(DEFAULT_CONFIG)
  const [history, setHistory] = useState([])
  const { result, loading, complete, progress, run } = useSimulationSocket()

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
            loading={loading}
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
          </div>

          <QBERChart history={history} />
          <PhotonGrid result={result} loading={loading} progress={progress} />
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
