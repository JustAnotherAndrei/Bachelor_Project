// Challenge Mode session state machine.
//
// Flow:
//   idle -> briefing -> running -> awaiting_answer -> result
//
// Detective: after running, user submits {verdict, attack_type}
// Engineer:  after running, auto-submit with the config that was used
//            (the grader checks sim_result against the mission's constraints)

import { useState, useCallback, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import useSimulationSocket from './useSimulationSocket'

export default function useChallengeSession() {
  const [phase, setPhase] = useState('idle')
  const [mission, setMission] = useState(null)
  const [instantiated, setInstantiated] = useState(null)
  const [nonce, setNonce] = useState(null)
  const [userChoices, setUserChoices] = useState({})
  const [gradingResult, setGradingResult] = useState(null)
  const [error, setError] = useState(null)
  const sim = useSimulationSocket()
  const lastCompletedRef = useRef(false)

  const startLevel = useCallback(async (level) => {
    setError(null)
    setGradingResult(null)
    setUserChoices({})
    try {
      const res = await api(`/api/v1/challenge/level/${level}/start`, { method: 'POST' })
      setMission(res.mission)
      setInstantiated(res.instantiated_params)
      setNonce(res.nonce)
      setPhase('briefing')
    } catch (e) {
      setError(e?.detail || 'Failed to start level')
    }
  }, [])

  const runSimulation = useCallback((choices = {}) => {
    if (!instantiated || !mission) return
    setUserChoices(choices)
    const config = { ...instantiated, ...choices }
    lastCompletedRef.current = false
    sim.run(config)
    setPhase('running')
  }, [instantiated, mission, sim])

  const submitAnswer = useCallback(async (userAnswer) => {
    if (!mission || !instantiated || !sim.summary) return null
    setError(null)
    try {
      const res = await api('/api/v1/challenge/attempts', {
        method: 'POST',
        body: {
          template_id: mission.id,
          instantiated_params: instantiated,
          sim_result: sim.summary,
          user_answer: userAnswer,
          nonce,
        },
      })
      setGradingResult(res)
      setPhase('result')
      return res
    } catch (e) {
      setError(e?.detail || 'Failed to submit attempt')
      return null
    }
  }, [mission, instantiated, sim.summary, nonce])

  // When the simulation finishes, transition phase. For Engineer missions
  // we auto-submit (the user's "answer" is the config they chose); for
  // Detective the form takes it from here.
  useEffect(() => {
    if (phase !== 'running') return
    if (!sim.complete || !sim.summary) return
    if (lastCompletedRef.current) return
    lastCompletedRef.current = true

    if (mission?.type === 'engineer') {
      submitAnswer({ config: userChoices })
    } else {
      setPhase('awaiting_answer')
    }
  }, [phase, sim.complete, sim.summary, mission, userChoices, submitAnswer])

  const reset = useCallback(() => {
    setPhase('idle')
    setMission(null)
    setInstantiated(null)
    setNonce(null)
    setUserChoices({})
    setGradingResult(null)
    setError(null)
  }, [])

  const retry = useCallback(() => {
    // Same mission, fresh roll — restart from scratch.
    if (mission?.level) startLevel(mission.level)
  }, [mission, startLevel])

  return {
    phase, mission, instantiated, userChoices,
    gradingResult, error, sim,
    startLevel, runSimulation, submitAnswer, reset, retry,
  }
}
