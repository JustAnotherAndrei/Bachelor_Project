// The active-mission screen. Shows briefing + (Engineer) config form, then
// runs the simulation and renders the standard result panels.
//
// Detective missions censor anything that would directly reveal Eve's
// presence until the verdict is submitted: PhotonGrid orange marks,
// PnsAttackPanel, SmartEvePanel, and the SimulationSummary's status banner.
// The rest (QBER stats, decoy bounds, LSTM, Bell, finite-key) is fair
// observable evidence the player must weigh.

import { useMemo } from 'react'
import { ChevronLeft, Play, Search, Wrench } from 'lucide-react'

import PhotonGrid from '../PhotonGrid'
import SimulationSummary from '../SimulationSummary'
import DecoyStatePanel from '../DecoyStatePanel'
import PnsAttackPanel from '../PnsAttackPanel'
import FiniteKeyPanel from '../FiniteKeyPanel'
import LstmDetectionPanel from '../LstmDetectionPanel'
import BellTestPanel from '../BellTestPanel'
import SmartEvePanel from '../SmartEvePanel'

import DetectiveSubmissionForm from './DetectiveSubmissionForm'
import EngineerConfigForm from './EngineerConfigForm'


const DIFFICULTY_COLORS = {
  easy: 'text-emerald-400 bg-emerald-950 border-emerald-800',
  medium: 'text-amber-400 bg-amber-950 border-amber-800',
  hard: 'text-red-400 bg-red-950 border-red-800',
}


export default function MissionBriefing({ session, onAbort }) {
  const { mission, phase, sim, runSimulation, submitAnswer } = session

  if (!mission) return null

  const isDetective = mission.type === 'detective'
  const isEngineer = mission.type === 'engineer'
  const running = phase === 'running'

  // Detective censors Eve-revealing panels until the verdict is in.
  // Engineer always sees everything (player already chose the config).
  const revealEve = isEngineer || phase === 'result'

  const censoredResult = useMemo(() => {
    if (!sim.result) return null
    if (revealEve) return sim.result
    return { ...sim.result, eve_intercepts: [] }
  }, [sim.result, revealEve])

  const summary = sim.summary
  const TypeIcon = isDetective ? Search : Wrench
  const typeBadge = isDetective
    ? 'bg-blue-900/40 border-blue-700 text-blue-300'
    : 'bg-emerald-900/40 border-emerald-700 text-emerald-300'

  return (
    <div className="flex flex-col gap-4">
      <header className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-xs font-mono text-gray-500">Level {mission.level}</span>
            <span className={`text-xs uppercase tracking-wider px-2 py-0.5 rounded border inline-flex items-center gap-1 ${typeBadge}`}>
              <TypeIcon size={11} /> {mission.type}
            </span>
            <span className={`text-xs uppercase tracking-wider px-2 py-0.5 rounded border ${DIFFICULTY_COLORS[mission.difficulty]}`}>
              {mission.difficulty}
            </span>
            <span className="text-xs text-amber-400 font-mono">{mission.xp_reward} XP</span>
          </div>
          <button
            onClick={onAbort}
            disabled={running}
            className="text-xs text-gray-400 hover:text-gray-200 flex items-center gap-1 disabled:opacity-30"
          >
            <ChevronLeft size={14} /> Back to catalogue
          </button>
        </div>
        <h2 className="text-xl font-semibold text-gray-100 mb-2">{mission.scenario}</h2>
        <p className="text-sm text-gray-400 leading-relaxed">{mission.briefing}</p>

        {isEngineer && mission.objective?.constraints && (
          <div className="mt-3 bg-gray-800/50 border border-gray-700 rounded-lg p-3">
            <p className="text-xs uppercase tracking-wider text-emerald-400 mb-2">Required constraints</p>
            <ul className="text-xs text-gray-300 font-mono space-y-1">
              {mission.objective.constraints.map((c, i) => (
                <li key={i}>· {c.metric} {c.op} {String(c.value)}</li>
              ))}
            </ul>
          </div>
        )}
      </header>

      {phase === 'briefing' && isEngineer && (
        <EngineerConfigForm mission={mission} onSubmit={runSimulation} disabled={running} />
      )}
      {phase === 'briefing' && isDetective && (
        <button
          onClick={() => runSimulation()}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <Play size={16} /> Run hidden simulation
        </button>
      )}
      {running && (
        <p className="text-sm text-violet-300 bg-violet-950 border border-violet-800 rounded-lg px-3 py-2 text-center font-mono">
          Running simulation… {sim.progress.current}/{sim.progress.total}
        </p>
      )}

      {sim.result && (
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Sifted key length"
            value={sim.result.sifted_key_length ?? '—'}
            unit={sim.result.sifted_key_length != null ? 'bits' : ''} />
          <StatCard label="QBER"
            value={sim.result.qber != null ? `${(sim.result.qber * 100).toFixed(1)}` : '—'}
            unit={sim.result.qber != null ? '%' : ''} />
          {revealEve ? (
            <StatCard label="Channel status"
              value={sim.result.is_secure != null
                ? (sim.result.is_secure ? 'Secure' : 'Compromised')
                : '—'}
              accent={sim.result.is_secure != null
                ? (sim.result.is_secure ? 'green' : 'red')
                : 'gray'} />
          ) : (
            // Detective: do NOT leak is_secure — it maps 1:1 to the verdict
            // the player must declare. Show a placeholder instead.
            <StatCard label="Channel status"
              value="?"
              unit="submit verdict to reveal"
              accent="gray" />
          )}
        </div>
      )}

      {censoredResult && (
        <PhotonGrid result={censoredResult} loading={running} progress={sim.progress} />
      )}

      {/* The SimulationSummary banner mentions the Eve mode by name, so we
          gate it behind the reveal. */}
      {summary && revealEve && (
        <SimulationSummary summary={summary} eveMode={summary.eve_mode || 'none'} />
      )}
      {summary?.decoy_state && (
        <DecoyStatePanel decoy={summary.decoy_state} />
      )}
      {summary?.finite_key && (
        <FiniteKeyPanel fk={summary.finite_key} />
      )}
      {summary?.lstm_prediction && (
        <LstmDetectionPanel lstm={summary.lstm_prediction} />
      )}
      {summary?.bell_test && (
        <BellTestPanel bell={summary.bell_test} />
      )}

      {revealEve && summary?.pns_attack && (
        <PnsAttackPanel pns={summary.pns_attack} decoy={summary.decoy_state} />
      )}
      {revealEve && summary?.smart_eve && (
        <SmartEvePanel
          smartEve={summary.smart_eve}
          qberFinal={summary.qber}
          isSecure={summary.is_secure}
        />
      )}

      {/* Detective verdict form */}
      {isDetective && phase === 'awaiting_answer' && (
        <DetectiveSubmissionForm onSubmit={submitAnswer} />
      )}
    </div>
  )
}


function StatCard({ label, value, unit, accent = 'gray' }) {
  const colors = {
    gray: 'text-gray-100',
    green: 'text-green-400',
    red: 'text-red-400',
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
