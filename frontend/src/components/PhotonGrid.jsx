const BASIS_SYMBOL = ['⊕', '⊗']  // Z = rectilinear, X = diagonal

export default function PhotonGrid({ result, loading, progress }) {
  if (!result) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl flex items-center justify-center" style={{ minHeight: 160 }}>
        <p className="text-gray-600 text-sm">Run a simulation to see the qubit exchange</p>
      </div>
    )
  }

  const { alice_bits, alice_bases, bob_bases, bob_results } = result
  const qubits = alice_bits.slice(0, 80).map((bit, i) => {
    const match = alice_bases[i] === bob_bases[i]
    const error = match && bit !== bob_results[i]
    return { i, bit, a_basis: alice_bases[i], b_basis: bob_bases[i], b_result: bob_results[i], match, error }
  })

  const pct = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 100

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
            Qubit exchange — first 80 qubits
          </p>
          {loading && (
            <span className="text-xs text-violet-400 font-mono">
              {progress.current}/{progress.total}
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-violet-500 inline-block" /> Key bit</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-red-500 inline-block" /> Error</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-gray-700 inline-block" /> Discarded</span>
        </div>
      </div>

      {loading && (
        <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-violet-500 rounded-full transition-all duration-150"
            style={{ width: `${pct}%` }}
          />
        </div>
      )}

      <div className="flex flex-wrap gap-1.5">
        {qubits.map(q => (
          <Qubit key={q.i} {...q} />
        ))}
      </div>

      <div className="grid grid-cols-3 gap-3 pt-2 border-t border-gray-800 text-xs text-gray-400">
        <div>
          <span className="text-gray-500 block mb-1">Alice basis</span>
          <span className="font-mono">⊕ rectilinear (Z) &nbsp; ⊗ diagonal (X)</span>
        </div>
        <div>
          <span className="text-gray-500 block mb-1">Bit value</span>
          <span className="font-mono">● = 1 &nbsp; ○ = 0</span>
        </div>
        <div>
          <span className="text-gray-500 block mb-1">Bob basis</span>
          <span className="font-mono">shown at bottom of each cell</span>
        </div>
      </div>
    </div>
  )
}

function Qubit({ bit, a_basis, b_basis, match, error }) {
  const bg = error
    ? 'bg-red-900 border-red-600'
    : match
      ? 'bg-violet-900 border-violet-600'
      : 'bg-gray-800 border-gray-700'

  const textColor = error ? 'text-red-300' : match ? 'text-violet-300' : 'text-gray-500'

  return (
    <div
      className={`w-10 h-10 rounded-md border flex flex-col items-center justify-center gap-0.5 ${bg}`}
      title={`Alice: ${bit} (${a_basis === 0 ? 'Z' : 'X'}) | Bob basis: ${b_basis === 0 ? 'Z' : 'X'} | Match: ${match}`}
    >
      <span className={`text-xs leading-none ${textColor}`}>
        {BASIS_SYMBOL[a_basis]}
      </span>
      <span className={`text-[10px] leading-none ${textColor}`}>
        {bit === 1 ? '●' : '○'}
      </span>
      <span className={`text-[9px] leading-none ${textColor} opacity-60`}>
        {BASIS_SYMBOL[b_basis]}
      </span>
    </div>
  )
}
