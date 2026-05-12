import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend,
} from 'recharts'
import { Trash2 } from 'lucide-react'

const THRESHOLD = 11

export default function QBERChart({ history, onClear }) {
  if (history.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl flex items-center justify-center" style={{ height: 280 }}>
        <p className="text-gray-600 text-sm">Run a simulation to see the QBER chart</p>
      </div>
    )
  }

  const data = history.map((r, i) => ({
    run: i + 1,
    qber: parseFloat((r.qber * 100).toFixed(2)),
    sifted: r.sifted_key_length,
  }))

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
          QBER over simulation runs
        </p>
        <button
          onClick={onClear}
          className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-red-400 transition-colors"
          title="Clear history"
        >
          <Trash2 size={14} />
          Clear
        </button>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="run"
            stroke="#4b5563"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            label={{ value: 'Run', position: 'insideBottomRight', offset: -4, fill: '#6b7280', fontSize: 11 }}
          />
          <YAxis
            stroke="#4b5563"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            tickFormatter={v => `${v}%`}
            domain={[0, 35]}
          />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
            labelStyle={{ color: '#9ca3af' }}
            formatter={(value, name) => [
              name === 'qber' ? `${value}%` : `${value} bits`,
              name === 'qber' ? 'QBER' : 'Sifted Key',
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 12, color: '#9ca3af', paddingTop: 8 }}
            formatter={name => name === 'qber' ? 'QBER (%)' : 'Sifted Key (bits)'}
          />
          <ReferenceLine
            y={THRESHOLD}
            stroke="#ef4444"
            strokeDasharray="6 3"
            label={{ value: '11% threshold', position: 'insideTopRight', fill: '#ef4444', fontSize: 11 }}
          />
          <Line
            type="monotone"
            dataKey="qber"
            stroke="#a78bfa"
            strokeWidth={2}
            dot={{ fill: '#a78bfa', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
