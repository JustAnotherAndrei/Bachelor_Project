import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend,
} from 'recharts'
import { Brain, AlertTriangle, ShieldCheck } from 'lucide-react'

export default function SmartEvePanel({ smartEve, qberFinal, isSecure }) {
  if (!smartEve) return null

  const { target_qber, total_intercepted, interception_rates,
          observed_qber_trace, intercept_fraction } = smartEve

  // Downsample if the trace is too long for smooth rendering
  const step = Math.max(1, Math.floor(observed_qber_trace.length / 200))
  const data = observed_qber_trace
    .map((q, i) => ({
      qubit: i + 1,
      qber: parseFloat((q * 100).toFixed(2)),
      rate: parseFloat((interception_rates[i] * 100).toFixed(1)),
    }))
    .filter((_, i) => i % step === 0)

  const verdict = !isSecure
    ? { color: 'red',    msg: 'Eve was detected — running QBER drifted above 11%.' }
    : { color: 'green',  msg: `Eve stayed undetected — final QBER ${(qberFinal * 100).toFixed(2)}% kept below the 11% abort threshold.` }

  return (
    <div className="bg-gray-900 border border-purple-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="text-purple-400" size={18} />
          <p className="text-xs font-semibold text-purple-300 uppercase tracking-widest">
            Smart Eve — Adaptive Strategy
          </p>
        </div>
        <span className="text-xs text-purple-500 font-mono">target {(target_qber * 100).toFixed(1)}%</span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Total intercepted</p>
          <p className="text-sm font-mono font-semibold text-purple-300">
            {total_intercepted}
            <span className="text-xs text-gray-500 ml-1">({(intercept_fraction * 100).toFixed(1)}%)</span>
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Final QBER induced</p>
          <p className={`text-sm font-mono font-semibold ${
            qberFinal >= 0.11 ? 'text-red-300' : 'text-green-300'
          }`}>
            {(qberFinal * 100).toFixed(2)}%
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-500">Final rate</p>
          <p className="text-sm font-mono font-semibold text-purple-300">
            {(interception_rates[interception_rates.length - 1] * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="qubit"
            stroke="#4b5563"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            label={{ value: 'Qubit index', position: 'insideBottomRight', offset: -4, fill: '#6b7280', fontSize: 10 }}
          />
          <YAxis
            stroke="#4b5563"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickFormatter={v => `${v}%`}
            domain={[0, 60]}
          />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
            labelStyle={{ color: '#9ca3af' }}
            formatter={(value, name) => [`${value}%`, name === 'qber' ? 'Induced QBER' : 'Intercept rate']}
          />
          <Legend
            wrapperStyle={{ fontSize: 12, color: '#9ca3af', paddingTop: 8 }}
            formatter={name => name === 'qber' ? 'Induced QBER (%)' : 'Intercept rate (%)'}
          />
          <ReferenceLine
            y={11}
            stroke="#ef4444"
            strokeDasharray="6 3"
            label={{ value: '11% abort', position: 'insideTopRight', fill: '#ef4444', fontSize: 10 }}
          />
          <ReferenceLine
            y={target_qber * 100}
            stroke="#a78bfa"
            strokeDasharray="4 2"
            label={{ value: `${(target_qber * 100).toFixed(0)}% target`, position: 'insideBottomRight', fill: '#a78bfa', fontSize: 10 }}
          />
          <Line type="monotone" dataKey="qber"  stroke="#c084fc" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="rate"  stroke="#6b7280" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
        </LineChart>
      </ResponsiveContainer>

      <div className={`flex items-start gap-3 rounded-lg px-4 py-3 ${
        verdict.color === 'red'
          ? 'bg-red-950 border border-red-800'
          : 'bg-green-950 border border-green-800'
      }`}>
        {verdict.color === 'red' ? (
          <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={16} />
        ) : (
          <ShieldCheck className="text-green-400 shrink-0 mt-0.5" size={16} />
        )}
        <p className={`text-xs ${verdict.color === 'red' ? 'text-red-300' : 'text-green-300'}`}>
          {verdict.msg}
        </p>
      </div>
    </div>
  )
}
