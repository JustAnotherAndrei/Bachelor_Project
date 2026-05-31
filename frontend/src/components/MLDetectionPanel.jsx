import { useEffect, useState } from 'react'
import { Brain, RefreshCw, AlertTriangle, ShieldCheck, ShieldAlert, Sparkles } from 'lucide-react'

const FEATURE_LABELS = {
  qber: 'QBER',
  sifting_efficiency: 'Sifting efficiency',
  depolarizing_prob: 'Depolarizing noise',
  measurement_error_prob: 'Measurement error',
  channel_distance_km: 'Channel distance',
  n_qubits: 'Qubits per run',
}

export default function MLDetectionPanel({ mlPrediction, refreshSignal }) {
  const [status, setStatus] = useState(null)
  const [training, setTraining] = useState(false)
  const [trainError, setTrainError] = useState(null)

  function loadStatus() {
    fetch('/api/v1/ml/status')
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(setStatus)
      .catch(() => {})
  }

  useEffect(() => { loadStatus() }, [refreshSignal])

  function trainModel() {
    setTraining(true)
    setTrainError(null)
    fetch('/api/v1/ml/train?model_type=random_forest', { method: 'POST' })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(s => {
        setStatus(prev => ({ ...prev, ...s }))
        if (!s.trained && s.error) setTrainError(s.error)
      })
      .catch(() => setTrainError('Training request failed.'))
      .finally(() => setTraining(false))
  }

  if (!status) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl flex items-center justify-center" style={{ height: 180 }}>
        <p className="text-gray-600 text-sm">Loading ML status…</p>
      </div>
    )
  }

  const ready = status.history_total >= 20 && status.history_eve_present >= 5 && status.history_eve_absent >= 5

  return (
    <div className="bg-gray-900 border border-emerald-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="text-emerald-400" size={18} />
          <p className="text-xs font-semibold text-emerald-300 uppercase tracking-widest">
            ML Eavesdropper Detector
          </p>
        </div>
        <button
          onClick={trainModel}
          disabled={training || !ready}
          className="flex items-center gap-1.5 text-xs font-medium bg-emerald-700 hover:bg-emerald-600 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded-md transition-colors"
        >
          <RefreshCw size={12} className={training ? 'animate-spin' : ''} />
          {training ? 'Training…' : status.trained ? 'Retrain' : 'Train'}
        </button>
      </div>

      {/* Dataset summary */}
      <div className="grid grid-cols-4 gap-3 text-center">
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">History runs</p>
          <p className="text-sm font-mono font-semibold text-gray-100">{status.history_total}</p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Eve present</p>
          <p className="text-sm font-mono font-semibold text-red-300">{status.history_eve_present}</p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Eve absent</p>
          <p className="text-sm font-mono font-semibold text-green-300">{status.history_eve_absent}</p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Model</p>
          <p className="text-sm font-mono font-semibold text-emerald-300">
            {status.trained ? (status.model_type ?? 'RF') : '—'}
          </p>
        </div>
      </div>

      {/* Pre-training guidance */}
      {!ready && (
        <div className="flex items-start gap-3 bg-yellow-950 border border-yellow-800 rounded-lg px-4 py-3">
          <AlertTriangle className="text-yellow-400 shrink-0 mt-0.5" size={16} />
          <div className="text-xs text-yellow-300">
            <p className="font-semibold">Not enough data to train yet</p>
            <p className="text-yellow-500 mt-0.5">
              Need ≥ 20 runs total with at least 5 of each class (Eve / no-Eve).
              Run a mix of simulations with Eve = None / Weak / Strong / Smart to build a dataset.
            </p>
          </div>
        </div>
      )}

      {trainError && (
        <div className="flex items-start gap-3 bg-red-950 border border-red-800 rounded-lg px-4 py-3">
          <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={16} />
          <p className="text-xs text-red-300">{trainError}</p>
        </div>
      )}

      {/* Model metrics */}
      {status.trained && (
        <>
          <div className="grid grid-cols-4 gap-3 text-center">
            <div className="bg-gray-800 rounded-lg px-3 py-2">
              <p className="text-xs text-gray-500">Accuracy</p>
              <p className="text-sm font-mono font-semibold text-emerald-300">
                {(status.accuracy * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg px-3 py-2">
              <p className="text-xs text-gray-500">F1</p>
              <p className="text-sm font-mono font-semibold text-emerald-300">
                {status.f1.toFixed(3)}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg px-3 py-2">
              <p className="text-xs text-gray-500">Trained on</p>
              <p className="text-sm font-mono font-semibold text-gray-100">
                {status.n_samples} <span className="text-xs text-gray-500">runs</span>
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg px-3 py-2">
              <p className="text-xs text-gray-500">Holdout</p>
              <p className="text-sm font-mono font-semibold text-gray-100">25%</p>
            </div>
          </div>

          {status.feature_importance && (
            <div>
              <p className="text-xs text-gray-500 mb-2">Feature importance (Random Forest)</p>
              <div className="flex flex-col gap-1.5">
                {Object.entries(status.feature_importance)
                  .sort(([, a], [, b]) => b - a)
                  .map(([feat, imp]) => (
                    <div key={feat} className="flex items-center gap-2 text-xs">
                      <span className="w-36 text-gray-400">{FEATURE_LABELS[feat] ?? feat}</span>
                      <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${Math.max(2, imp * 100)}%` }}
                        />
                      </div>
                      <span className="font-mono text-emerald-300 w-12 text-right">
                        {(imp * 100).toFixed(1)}%
                      </span>
                    </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Current run prediction */}
      {mlPrediction && (
        <div className={`rounded-lg px-4 py-3 border ${
          mlPrediction.ml_verdict === 'compromised'
            ? 'bg-red-950 border-red-800'
            : 'bg-green-950 border-green-800'
        }`}>
          <div className="flex items-start gap-3">
            {mlPrediction.ml_verdict === 'compromised' ? (
              <ShieldAlert className="text-red-400 shrink-0 mt-0.5" size={18} />
            ) : (
              <ShieldCheck className="text-green-400 shrink-0 mt-0.5" size={18} />
            )}
            <div className="flex-1">
              <p className={`text-sm font-semibold ${
                mlPrediction.ml_verdict === 'compromised' ? 'text-red-300' : 'text-green-300'
              }`}>
                ML verdict: {mlPrediction.ml_verdict}
                <span className="text-xs text-gray-500 ml-2">(decision threshold = 50%)</span>
              </p>
              <div className="mt-2 flex items-center gap-3">
                <span className="text-xs text-gray-500 w-32">P(Eve present)</span>
                <div className="flex-1 h-3 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      mlPrediction.eve_probability >= 0.5 ? 'bg-red-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${mlPrediction.eve_probability * 100}%` }}
                  />
                </div>
                <span className={`font-mono text-sm w-16 text-right ${
                  mlPrediction.eve_probability >= 0.5 ? 'text-red-300' : 'text-green-300'
                }`}>
                  {(mlPrediction.eve_probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {status.trained && !mlPrediction && (
        <div className="flex items-start gap-3 bg-emerald-950 border border-emerald-800 rounded-lg px-4 py-3">
          <Sparkles className="text-emerald-400 shrink-0 mt-0.5" size={14} />
          <p className="text-xs text-emerald-300">
            Model ready. Run a new simulation and an ML prediction will appear here automatically.
          </p>
        </div>
      )}
    </div>
  )
}
