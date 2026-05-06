import { Shield } from 'lucide-react'
import StatusBadge from './StatusBadge'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">

      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="text-violet-400" size={28} />
          <span className="text-xl font-semibold tracking-tight">Q-Shield</span>
          <span className="text-xs text-gray-500 font-mono">BB84 QKD Platform</span>
        </div>
        <StatusBadge online />
      </header>

      {/* Main */}
      <main className="flex flex-1 gap-6 p-6">

        {/* Left panel — controls */}
        <aside className="w-72 shrink-0 bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
            Simulation
          </h2>
          <p className="text-xs text-gray-500">
            Configure and run a BB84 key exchange simulation.
          </p>
          <div className="mt-auto">
            <button
              disabled
              className="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg transition-colors"
            >
              Run Simulation
            </button>
          </div>
        </aside>

        {/* Center — results */}
        <section className="flex-1 flex flex-col gap-4">

          {/* Stats row */}
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Sifted Key Length" value="—" unit="bits" />
            <StatCard label="QBER" value="—" unit="%" />
            <StatCard label="Channel Status" value="—" />
          </div>

          {/* Placeholder chart */}
          <div className="flex-1 bg-gray-900 border border-gray-800 rounded-xl flex items-center justify-center">
            <p className="text-gray-600 text-sm">QBER chart will appear here after simulation</p>
          </div>

        </section>

      </main>
    </div>
  )
}

function StatCard({ label, value, unit }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-mono font-semibold text-gray-100">
        {value}
        {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
      </p>
    </div>
  )
}
