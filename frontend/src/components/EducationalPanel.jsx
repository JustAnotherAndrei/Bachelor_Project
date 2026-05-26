import { useState } from 'react'
import { ChevronDown, BookOpen, GitBranch, Activity, ShieldCheck, Key } from 'lucide-react'

const CARDS = [
  {
    icon: BookOpen,
    color: 'violet',
    title: 'What is the BB84 Protocol?',
    subtitle: 'The first quantum key distribution scheme',
    body: (
      <div className="flex flex-col gap-3 text-sm text-gray-300 leading-relaxed">
        <p>
          BB84 is the first <Hl>Quantum Key Distribution (QKD)</Hl> protocol, proposed by
          Charles Bennett and Gilles Brassard in <Hl>1984</Hl>. Its goal is to allow two
          parties — <Hl color="violet">Alice</Hl> and <Hl color="blue">Bob</Hl> — to
          establish a shared secret key over an insecure channel.
        </p>
        <p>
          Unlike classical cryptography, whose security relies on the computational
          difficulty of mathematical problems (e.g. factoring large numbers), BB84's
          security is guaranteed by the <Hl>laws of quantum physics</Hl> — making it
          immune to any increase in computing power, including quantum computers.
        </p>
        <p>
          The shared key produced by BB84 can then be used for symmetric encryption
          (e.g. <Hl>AES-128</Hl>), enabling provably secure communication.
        </p>
      </div>
    ),
  },
  {
    icon: GitBranch,
    color: 'blue',
    title: 'How Does Key Sifting Work?',
    subtitle: 'Why ~50% of qubits are always discarded',
    body: (
      <div className="flex flex-col gap-3 text-sm text-gray-300 leading-relaxed">
        <p>
          Alice encodes each bit into a photon using one of two randomly chosen
          bases: <Hl>rectilinear (Z ⊕)</Hl> or <Hl>diagonal (X ⊗)</Hl>. Bob
          measures each photon in his own randomly chosen basis.
        </p>
        <p>
          When Alice and Bob happen to use the <Hl>same basis</Hl> (~50% of cases),
          Bob's measurement produces the correct bit. When they use different bases,
          Bob's result is random and useless — those qubits are discarded.
        </p>
        <p>
          After the quantum exchange, Alice and Bob <Hl>compare their bases publicly</Hl> —
          not the bit values themselves — and keep only the matching positions. The
          result is the <Hl color="violet">sifted key</Hl>, approximately 50% of
          the original qubit count.
        </p>
      </div>
    ),
  },
  {
    icon: Activity,
    color: 'orange',
    title: 'What is QBER?',
    subtitle: 'Quantum Bit Error Rate — the security indicator',
    body: (
      <div className="flex flex-col gap-3 text-sm text-gray-300 leading-relaxed">
        <p>
          <Hl>QBER = (mismatched bits) / (total sifted bits)</Hl>. Alice and Bob
          compare a random subset of their sifted keys to estimate the error rate
          without revealing the full key.
        </p>
        <div className="grid grid-cols-3 gap-2 my-1">
          <div className="bg-green-950 border border-green-800 rounded-lg px-3 py-2 text-center">
            <p className="text-green-400 font-mono font-bold text-sm">0 – 5%</p>
            <p className="text-green-600 text-xs mt-0.5">Secure channel</p>
          </div>
          <div className="bg-orange-950 border border-orange-800 rounded-lg px-3 py-2 text-center">
            <p className="text-orange-400 font-mono font-bold text-sm">5 – 11%</p>
            <p className="text-orange-600 text-xs mt-0.5">Noise / weak Eve</p>
          </div>
          <div className="bg-red-950 border border-red-800 rounded-lg px-3 py-2 text-center">
            <p className="text-red-400 font-mono font-bold text-sm">&gt; 11%</p>
            <p className="text-red-600 text-xs mt-0.5">Eve detected</p>
          </div>
        </div>
        <p>
          If Eve intercepts <Hl>100% of qubits</Hl>, she must guess each basis.
          She guesses wrong ~50% of the time, and each wrong guess introduces an
          error in ~50% of those cases — resulting in a QBER of <Hl color="red">~25%</Hl>,
          well above the 11% abort threshold.
        </p>
      </div>
    ),
  },
  {
    icon: ShieldCheck,
    color: 'green',
    title: "Why Can't Eve Listen Undetected?",
    subtitle: 'No-cloning theorem & Heisenberg uncertainty',
    body: (
      <div className="flex flex-col gap-3 text-sm text-gray-300 leading-relaxed">
        <p>
          Two fundamental principles of quantum mechanics make eavesdropping
          physically impossible to hide:
        </p>
        <div className="flex flex-col gap-2">
          <div className="bg-gray-800 rounded-lg px-4 py-3">
            <p className="text-white font-semibold text-sm mb-1">No-Cloning Theorem</p>
            <p className="text-gray-400 text-xs leading-relaxed">
              It is <Hl>impossible to create an exact copy</Hl> of an unknown
              quantum state without disturbing the original. Eve cannot intercept,
              clone, and re-transmit a qubit — she must measure it, collapsing its state.
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg px-4 py-3">
            <p className="text-white font-semibold text-sm mb-1">Heisenberg Uncertainty Principle</p>
            <p className="text-gray-400 text-xs leading-relaxed">
              <Hl>Measuring a qubit inevitably disturbs it.</Hl> When Eve guesses
              the wrong basis, she sends Bob a qubit in the wrong state. This
              introduces detectable errors — Eve's presence leaves a physical trace
              that no amount of technology can eliminate.
            </p>
          </div>
        </div>
      </div>
    ),
  },
  {
    icon: Key,
    color: 'teal',
    title: 'Error Correction & Privacy Amplification',
    subtitle: 'From sifted bits to a provably secret key',
    body: (
      <div className="flex flex-col gap-3 text-sm text-gray-300 leading-relaxed">
        <p>
          Even after sifting, the key may still contain errors from hardware noise
          or partial eavesdropping. Two post-processing steps produce the final key:
        </p>
        <div className="flex flex-col gap-2">
          <div className="bg-gray-800 rounded-lg px-4 py-3">
            <p className="text-white font-semibold text-sm mb-1">
              1. Error Correction <span className="text-gray-500 font-normal text-xs ml-1">(EC)</span>
            </p>
            <p className="text-gray-400 text-xs leading-relaxed">
              The sifted key is split into <Hl>4-bit blocks</Hl>. Alice and Bob compare
              the <Hl>parity</Hl> (XOR) of each block over a public channel. Blocks
              where parities disagree contain errors and are <Hl color="red">discarded</Hl>.
              The remaining blocks form a consistent, error-free key.
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg px-4 py-3">
            <p className="text-white font-semibold text-sm mb-1">
              2. Privacy Amplification <span className="text-gray-500 font-normal text-xs ml-1">(PA)</span>
            </p>
            <p className="text-gray-400 text-xs leading-relaxed">
              During error correction, some information about the key was revealed publicly.
              <Hl>SHA-256</Hl> is applied to compress the key, mathematically eliminating
              any partial knowledge Eve may have gained. The result is a <Hl color="green">128-bit
              key</Hl> that is information-theoretically secure.
            </p>
          </div>
        </div>
      </div>
    ),
  },
]

function Hl({ children, color = 'violet' }) {
  const colors = {
    violet: 'text-violet-300',
    blue: 'text-blue-300',
    green: 'text-green-300',
    red: 'text-red-300',
    orange: 'text-orange-300',
  }
  return <span className={`font-semibold ${colors[color]}`}>{children}</span>
}

function Card({ card, open, onToggle }) {
  const Icon = card.icon
  const accent = {
    violet: 'text-violet-400 border-violet-800 bg-violet-950/40',
    blue:   'text-blue-400 border-blue-800 bg-blue-950/40',
    orange: 'text-orange-400 border-orange-800 bg-orange-950/40',
    green:  'text-green-400 border-green-800 bg-green-950/40',
    teal:   'text-teal-400 border-teal-800 bg-teal-950/40',
  }[card.color]

  return (
    <div className="border border-gray-800 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-5 py-4 hover:bg-gray-800/50 transition-colors text-left"
      >
        <span className={`p-2 rounded-lg border ${accent}`}>
          <Icon size={16} />
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-100">{card.title}</p>
          <p className="text-xs text-gray-500 mt-0.5">{card.subtitle}</p>
        </div>
        <ChevronDown
          size={16}
          className={`text-gray-500 shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>
      {open && (
        <div className="px-5 pb-5 pt-1 border-t border-gray-800 bg-gray-900/50">
          {card.body}
        </div>
      )}
    </div>
  )
}

export default function EducationalPanel() {
  const [openIndex, setOpenIndex] = useState(null)

  function toggle(i) {
    setOpenIndex(prev => prev === i ? null : i)
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
          Quantum Cryptography - some facts to keep in mind
        </h3>
        <span className="text-xs text-gray-600">Click a card to expand</span>
      </div>
      {CARDS.map((card, i) => (
        <Card
          key={i}
          card={card}
          open={openIndex === i}
          onToggle={() => toggle(i)}
        />
      ))}
    </div>
  )
}
