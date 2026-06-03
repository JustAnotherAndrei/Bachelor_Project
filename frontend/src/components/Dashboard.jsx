import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, LogIn, Trophy } from 'lucide-react'
import StatusBadge from './StatusBadge'
import SimulationControls from './SimulationControls'
import QBERChart from './QBERChart'
import PhotonGrid from './PhotonGrid'
import SimulationSummary from './SimulationSummary'
import useSimulationSocket from '../hooks/useSimulationSocket'
import EducationalPanel from './EducationalPanel'
import FunFactPanel from './FunFactPanel'
import SessionMeta from './SessionMeta'
import KeyRateChart from './KeyRateChart'
import DecoyStatePanel from './DecoyStatePanel'
import SmartEvePanel from './SmartEvePanel'
import MLDetectionPanel from './MLDetectionPanel'
import LstmDetectionPanel from './LstmDetectionPanel'
import BellTestPanel from './BellTestPanel'
import PnsAttackPanel from './PnsAttackPanel'
import FiniteKeyPanel from './FiniteKeyPanel'
import AuthModal from './auth/AuthModal'
import UserMenu from './auth/UserMenu'
import { useAuth } from '../contexts/AuthContext'

const DEFAULT_CONFIG = {
  protocol: 'bb84',
  n_qubits: 100,
  depolarizing_prob: 0.01,
  measurement_error_prob: 0.02,
  eve_mode: 'none',
  mode: 'simulator',
  ibm_backend: 'ibm_fez',
  channel_distance_km: 0,
  ec_method: 'cascade',
  source_type: 'ideal',
  mu_signal: 0.5,
  mu_decoy: 0.1,
  p_signal: 0.7,
  p_decoy: 0.15,
  smart_target_qber: 0.09,
}

export default function Dashboard() {
  const [config, setConfig] = useState(DEFAULT_CONFIG)
  const [history, setHistory] = useState([])
  const { result, summary, loading, complete, progress, statusMessage, run, cancel } = useSimulationSocket()
  const { user, loading: authLoading } = useAuth()

  const [authOpen, setAuthOpen] = useState(false)
  const [authView, setAuthView] = useState('login')
  const [authToken, setAuthToken] = useState('')

  // Handle deep-links: ?token=… opens the reset form; ?auth=google_success
  // just cleans up the URL after the OAuth callback redirect.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const auth = params.get('auth')
    if (token) {
      setAuthToken(token)
      setAuthView('reset')
      setAuthOpen(true)
    }
    if (token || auth) {
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

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
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3">
            <Shield className="text-violet-400" size={28} />
            <span className="text-xl font-semibold tracking-tight">Sequre</span>
            <span className="text-xs text-gray-500 font-mono">An interactive QKD Platform</span>
          </div>
          <SessionMeta />
        </div>
        <div className="flex items-center gap-4">
          <Link
            to="/challenge"
            className="flex items-center gap-2 text-sm px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg transition-colors"
            title="15 procedurally-generated QKD missions"
          >
            <Trophy size={14} /> Challenge Mode
          </Link>
          <StatusBadge online />
          {authLoading ? null : user ? (
            <UserMenu />
          ) : (
            <button
              onClick={() => { setAuthView('login'); setAuthOpen(true) }}
              className="flex items-center gap-2 text-sm px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors"
            >
              <LogIn size={14} /> Sign in
            </button>
          )}
        </div>
      </header>

      <AuthModal
        open={authOpen}
        onClose={() => setAuthOpen(false)}
        initialView={authView}
        initialToken={authToken}
      />

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
          {summary?.decoy_state && (
            <DecoyStatePanel decoy={summary.decoy_state} />
          )}
          {summary?.pns_attack && (
            <PnsAttackPanel pns={summary.pns_attack} decoy={summary.decoy_state} />
          )}
          {summary?.finite_key && (
            <FiniteKeyPanel fk={summary.finite_key} />
          )}
          {summary?.smart_eve && (
            <SmartEvePanel
              smartEve={summary.smart_eve}
              qberFinal={summary.qber}
              isSecure={summary.is_secure}
            />
          )}
          {summary?.bell_test && (
            <BellTestPanel bell={summary.bell_test} />
          )}
          <QBERChart history={history} onClear={handleClearHistory} />
          <MLDetectionPanel
            mlPrediction={summary?.ml_prediction}
            refreshSignal={history.length}
          />
          {summary?.lstm_prediction && (
            <LstmDetectionPanel lstm={summary.lstm_prediction} />
          )}
          <KeyRateChart
            depProb={config.depolarizing_prob}
            measProb={config.measurement_error_prob}
            currentDistance={config.channel_distance_km}
          />
          <FunFactPanel />
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
