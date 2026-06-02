import { Brain, CheckCircle2, AlertOctagon } from 'lucide-react'

export default function LstmDetectionPanel({ lstm }) {
  if (!lstm) return null

  const p = lstm.eve_probability
  const compromised = lstm.lstm_verdict === 'compromised'
  const pct = (p * 100).toFixed(1)
  const m = lstm.metrics || {}

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="text-indigo-400" size={18} />
        <h3 className="text-sm font-semibold text-gray-200">LSTM Deep-Learning Detection</h3>
        <span className="text-xs text-indigo-300 font-mono ml-auto">PyTorch · {lstm.sequence_length} qubits</span>
      </div>

      <p className="text-xs text-gray-400 mb-4 leading-relaxed">
        A recurrent neural network reads the entire per-qubit exchange as a
        temporal sequence — alice/bob basis, alice bit, bob result, basis-match,
        error flag — and predicts P(Eve | sequence). Unlike the summary-feature
        Random Forest, it can detect attack <em>patterns</em> that the QBER
        average smooths out.
      </p>

      {/* Probability + verdict */}
      <div className="flex items-baseline gap-3 mb-3">
        <span className={`font-mono text-4xl ${
          compromised ? 'text-red-300' : 'text-emerald-300'
        }`}>
          {pct}%
        </span>
        <span className="text-xs text-gray-500">P(Eve)</span>
        <span className="ml-auto">
          {compromised ? (
            <span className="text-xs px-2 py-1 rounded-md bg-red-900 text-red-200 border border-red-700 inline-flex items-center gap-1">
              <AlertOctagon size={12} /> LSTM flags eavesdropping
            </span>
          ) : (
            <span className="text-xs px-2 py-1 rounded-md bg-emerald-900 text-emerald-200 border border-emerald-700 inline-flex items-center gap-1">
              <CheckCircle2 size={12} /> LSTM clears the run
            </span>
          )}
        </span>
      </div>

      {/* Probability bar */}
      <div className="relative h-3 bg-gray-800 rounded-full overflow-hidden mb-1">
        <div
          className={`absolute left-0 top-0 h-full ${compromised ? 'bg-red-500' : 'bg-emerald-500'}`}
          style={{ width: `${pct}%` }}
        />
        <div
          className="absolute top-0 h-full border-r-2 border-yellow-500"
          style={{ left: '50%', width: 0 }}
          title="Decision threshold (P = 0.5)"
        />
      </div>
      <div className="flex justify-between text-[10px] text-gray-500 font-mono mb-4">
        <span>0 (secure)</span>
        <span style={{ marginLeft: '-10px' }}>0.5 threshold</span>
        <span>1 (compromised)</span>
      </div>

      {/* Model metrics */}
      <div className="grid grid-cols-4 gap-2 text-xs">
        <Metric label="Val accuracy" value={`${(m.val_acc * 100).toFixed(1)}%`} />
        <Metric label="Train accuracy" value={`${(m.train_acc * 100).toFixed(1)}%`} />
        <Metric label="Val loss" value={m.val_loss?.toFixed(3) ?? '—'} />
        <Metric label="Train samples" value={m.n_train ?? '—'} />
      </div>

      <p className="text-[10px] text-gray-600 mt-3">
        LSTM · hidden=64 · 1 layer · trained on {m.n_train ?? '?'} synthetic sequences
        for {m.n_epochs ?? '?'} epochs.
      </p>
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-md px-2 py-1.5">
      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-0.5">{label}</p>
      <p className="text-gray-100 font-mono text-sm">{value}</p>
    </div>
  )
}
