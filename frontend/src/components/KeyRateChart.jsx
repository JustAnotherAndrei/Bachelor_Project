import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend,
} from 'recharts'

export default function KeyRateChart({ depProb, measProb, currentDistance }) {
  const [data, setData] = useState([])

  useEffect(() => {
    fetch(`/api/v1/key-rate-curve?dep_prob=${depProb}&meas_prob=${measProb}`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(points => setData(points.map(p => ({
        distance: p.distance_km,
        keyRate: parseFloat((p.key_rate * 100).toFixed(3)),
        transmittance: parseFloat((p.transmittance * 100).toFixed(2)),
      }))))
      .catch(() => {})
  }, [depProb, measProb])

  if (data.length === 0) {
    return (
      <div
        className="bg-gray-900 border border-gray-800 rounded-xl flex items-center justify-center"
        style={{ height: 280 }}
      >
        <p className="text-gray-600 text-sm">Loading key-rate curve…</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
          Secure Key Rate vs. Fiber Distance
        </p>
        <span className="text-xs text-gray-500 font-mono">α = 0.2 dB/km · SMF-28</span>
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="distance"
            stroke="#4b5563"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            label={{ value: 'Distance (km)', position: 'insideBottomRight', offset: -4, fill: '#6b7280', fontSize: 11 }}
          />
          <YAxis
            stroke="#4b5563"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            tickFormatter={v => `${v}%`}
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
            labelStyle={{ color: '#9ca3af' }}
            labelFormatter={v => `${v} km`}
            formatter={(value, name) => [
              `${value}%`,
              name === 'keyRate' ? 'Secure Key Rate' : 'Transmittance η',
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 12, color: '#9ca3af', paddingTop: 8 }}
            formatter={name => name === 'keyRate' ? 'Secure Key Rate (%)' : 'Transmittance η (%)'}
          />
          {currentDistance > 0 && (
            <ReferenceLine
              x={currentDistance}
              stroke="#60a5fa"
              strokeDasharray="6 3"
              label={{
                value: `${currentDistance} km`,
                position: 'insideTopRight',
                fill: '#60a5fa',
                fontSize: 11,
              }}
            />
          )}
          <Line
            type="monotone"
            dataKey="transmittance"
            stroke="#6b7280"
            strokeWidth={1.5}
            strokeDasharray="4 2"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="keyRate"
            stroke="#34d399"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: '#34d399' }}
          />
        </LineChart>
      </ResponsiveContainer>

      <p className="text-xs text-gray-600">
        Model: R(L) = η(L) × max(0, 1 − 2h(Q<sub>noise</sub>)) — simplified BB84 key rate,
        where h is the binary entropy function.
      </p>
    </div>
  )
}
