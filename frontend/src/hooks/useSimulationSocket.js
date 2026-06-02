import { useState, useRef, useCallback } from 'react'

export default function useSimulationSocket() {
  const [result, setResult] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [complete, setComplete] = useState(false)
  const [progress, setProgress] = useState({ current: 0, total: 0 })
  const [statusMessage, setStatusMessage] = useState(null)
  const wsRef = useRef(null)

  const cancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.onmessage = null
      wsRef.current.close()
    }
    setLoading(false)
    setStatusMessage(null)
  }, [])

  const run = useCallback((config) => {
    if (wsRef.current) {
      wsRef.current.onmessage = null
      wsRef.current.close()
    }

    const sessionId = crypto.randomUUID()
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/simulate/${sessionId}`)
    wsRef.current = ws

    setLoading(true)
    setComplete(false)
    setProgress({ current: 0, total: config.n_qubits })
    setResult(null)
    setSummary(null)
    setStatusMessage(null)

    ws.onopen = () => ws.send(JSON.stringify(config))

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)

      if (msg.type === 'status') {
        setStatusMessage(msg.message)
      } else if (msg.type === 'qubit') {
        setStatusMessage(null)
        setProgress(p => ({ ...p, current: msg.index + 1 }))
        setResult(prev => ({
          alice_bits: [...(prev?.alice_bits ?? []), msg.alice_bit],
          alice_bases: [...(prev?.alice_bases ?? []), msg.alice_basis],
          bob_bases: [...(prev?.bob_bases ?? []), msg.bob_basis],
          bob_results: [...(prev?.bob_results ?? []), msg.bob_result],
          eve_intercepts: [...(prev?.eve_intercepts ?? []), msg.eve_intercept ?? false],
        }))
      } else if (msg.type === 'result') {
        const common = {
          protocol: msg.protocol,
          protocol_display_name: msg.protocol_display_name,
          n_qubits_sent: msg.n_qubits_sent,
          n_qubits_received: msg.n_qubits_received,
          transmission_efficiency: msg.transmission_efficiency,
          channel_distance_km: msg.channel_distance_km,
          sifted_key_length: msg.sifted_key_length,
          sifting_efficiency: msg.sifting_efficiency,
          bits_after_ec: msg.bits_after_ec,
          final_key_length: msg.final_key_length,
          final_key: msg.final_key,
          qber: msg.qber,
          is_secure: msg.is_secure,
          elapsed_seconds: msg.elapsed_seconds,
          mode: msg.mode,
          ibm_backend: msg.ibm_backend,
          ec_method: msg.ec_method,
          ec_stats: msg.ec_stats,
          source_type: msg.source_type,
          decoy_state: msg.decoy_state,
          pns_attack: msg.pns_attack,
          finite_key: msg.finite_key,
          lstm_prediction: msg.lstm_prediction,
          smart_eve: msg.smart_eve,
          ml_prediction: msg.ml_prediction,
          bell_test: msg.bell_test,
        }
        setResult(prev => prev ? { ...prev, ...common } : null)
        setSummary(common)
        setComplete(true)
        setLoading(false)
      } else if (msg.type === 'error') {
        setStatusMessage(`Error: ${msg.message}`)
        setLoading(false)
      }
    }

    ws.onerror = () => setLoading(false)
    ws.onclose = () => { setLoading(false) }
  }, [])

  return { result, summary, loading, complete, progress, statusMessage, run, cancel }
}
