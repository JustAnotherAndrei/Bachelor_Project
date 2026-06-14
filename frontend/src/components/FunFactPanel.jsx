// Rotating "Did you know?" card with curated QKD trivia.
// Facts are sourced from peer-reviewed history of the field (BB84 paper,
// Ekert 1991, Lo-Ma-Chen 2005, the Micius / Beijing-Shanghai milestones,
// Makarov's detector-blinding work, etc.).

import { useState } from 'react'
import { Lightbulb, Shuffle } from 'lucide-react'


export const FACTS = [
  // ----- History -----
  {
    category: 'History',
    text: "BB84, the first QKD protocol, was published by Charles Bennett (IBM) and Gilles Brassard (Université de Montréal) in 1984. The seminal idea — using non-orthogonal quantum states as 'quantum money' — came from Stephen Wiesner in 1969, but his paper was rejected by the journal Information and Control and was only finally published in 1983.",
  },
  {
    category: 'History',
    text: "The very first physical BB84 demonstration in 1989 ran over just 32 cm of free space inside an IBM laboratory. Today, satellite-to-ground QKD has reached more than 1200 km via China's Micius satellite (launched 2016, entanglement-based QKD demonstrated 2017).",
  },
  {
    category: 'History',
    text: "The Swiss canton of Geneva used BB84-based QKD to secure the transmission of voting results in the 2007 federal election — the first government-level deployment of quantum key distribution outside a lab.",
  },

  // ----- Protocols -----
  {
    category: 'BB84',
    text: "BB84 uses four polarisation states grouped in two non-orthogonal bases (rectilinear ⊕ and diagonal ⊗). The no-cloning theorem (Wootters-Zurek 1982) guarantees that any eavesdropping disturbs roughly 25 % of basis-matched bits on average — the QBER fingerprint that detects Eve.",
  },
  {
    category: 'B92',
    text: "B92 (Bennett 1992) is the minimal QKD protocol: only two non-orthogonal quantum states are needed (e.g. |0⟩ and |+⟩). Simpler hardware, but the sifting efficiency drops to ~25 % versus BB84's 50 %, and any photon loss leaks information to Eve.",
  },
  {
    category: 'SARG04',
    text: "SARG04 (Scarani-Acin-Ribordy-Gisin 2004) uses the same four states as BB84 but announces them in pairs during sifting. This subtle change makes the protocol inherently more resistant to Photon-Number-Splitting attacks against weak-coherent-pulse sources.",
  },
  {
    category: 'E91',
    text: "E91 (Ekert 1991) was the first protocol to base security on entanglement and the violation of Bell inequalities. Any eavesdropping collapses the entangled correlations, dropping the CHSH parameter from the quantum bound 2√2 ≈ 2.83 down toward the classical bound of 2.",
  },

  // ----- Theory -----
  {
    category: 'Theory',
    text: "Tsirelson's bound 2√2 ≈ 2.828 is the maximum value the CHSH inequality can reach in quantum mechanics — strictly above the classical bound of 2, but strictly below the algebraic maximum of 4 that 'super-quantum' theories like PR-boxes would allow.",
  },
  {
    category: 'Theory',
    text: "The no-cloning theorem (Wootters & Zurek; Dieks, 1982) states that no unitary operation can create a perfect copy of an arbitrary unknown quantum state. This single principle is why QKD security holds even against an adversary with unlimited quantum computational power.",
  },
  {
    category: 'Theory',
    text: "The Tomamichel-Renner finite-key bound (2011-2012) extended QKD security from the asymptotic limit to realistic finite block sizes, introducing the Hoeffding correction δ_PE and composable ε-security parameters that modern proofs still use today.",
  },

  // ----- Attacks -----
  {
    category: 'Attacks',
    text: "Decoy-state QKD (Hwang 2003; Lo-Ma-Chen 2005) defeats Photon-Number-Splitting attacks by randomly varying the source intensity between 'signal' and 'decoy' pulses. Eve cannot distinguish them without disturbing the per-intensity gain statistics — a small but decisive change to the protocol.",
  },
  {
    category: 'Attacks',
    text: "In 2010, Vadim Makarov's group demonstrated 'detector-blinding' attacks on commercial QKD systems — by shining bright light, they forced the single-photon detectors into a classical mode where Eve could control the clicks. This led to the development of Measurement-Device-Independent QKD (MDI-QKD).",
  },
  {
    category: 'Attacks',
    text: "Trojan-horse attacks send bright back-reflected pulses INTO Alice's transmitter, then read the reflected signal to learn the basis settings. Modern QKD modules include optical isolators and watchdog detectors specifically to defeat them.",
  },

  // ----- Milestones -----
  {
    category: 'Milestones',
    text: "The Beijing-Shanghai backbone, operational since 2017, is the world's longest QKD network: over 2000 km of trusted-node fiber linking four major Chinese cities. Banks and state agencies are its primary users.",
  },
  {
    category: 'Milestones',
    text: "Twin-Field QKD (Lucamarini et al. 2018) broke the fundamental rate-distance limit of point-to-point QKD: instead of scaling as η (channel transmission), the secret-key rate scales as √η. Fiber records over 830 km were achieved by 2022.",
  },
  {
    category: 'Milestones',
    text: "DARPA QKD Network (2003-2007), built by BBN, Harvard and Boston University, was the first multi-node QKD network — six nodes spanning ~10 km across Cambridge, Massachusetts. Tokyo (2010) and Vienna (2008) followed shortly after.",
  },

  // ----- Open problems -----
  {
    category: 'Open problems',
    text: "Practical quantum repeaters — devices that extend QKD beyond fiber attenuation via entanglement swapping — still require coherent quantum memories with much longer lifetimes than current photonic and atomic systems can reliably deliver. This is the main obstacle to a global QKD network without trusted nodes.",
  },
  {
    category: 'Open problems',
    text: "Truly device-independent QKD, which would remain secure even with arbitrarily malicious hardware, has been demonstrated in proof-of-principle experiments in 2022 — but at key rates orders of magnitude below anything practical.",
  },
  {
    category: 'Open problems',
    text: "QKD ultimately delivers a shared random key — not a digital signature. Pairing it with post-quantum public-key cryptography (NIST PQC standards, 2024) is an open integration challenge: how do you authenticate the classical QKD channel itself in a quantum-resistant way?",
  },

  // ----- Trivia -----
  {
    category: 'Trivia',
    text: "The first commercial QKD product, ID Quantique's Clavis, shipped in 2007 from Geneva. Today the same company supplies hardware used by banks, government networks and the Korean QKD backbone.",
  },
  {
    category: 'Trivia',
    text: "QKD is one of very few cryptographic primitives whose security proof depends on the laws of physics rather than computational hardness — its only conjecture is that quantum mechanics, as we know it, is correct.",
  },

  // ----- More theory -----
  {
    category: 'Theory',
    text: "The Heisenberg uncertainty principle ΔxΔp ≥ ℏ/2 is the conceptual ancestor of QKD security: any measurement of an unknown quantum state inevitably disturbs it. Bennett and Brassard turned this physical fact into a cryptographic guarantee.",
  },
  {
    category: 'Theory',
    text: "Privacy amplification — the final QKD step that turns a partially-known shared string into an (almost) perfectly secret shorter key — relies on the Leftover Hash Lemma. Random Toeplitz matrices or universal hash families do this efficiently, even when Eve knows up to a known fraction of the input bits.",
  },
  {
    category: 'Theory',
    text: "The Holevo bound (Alexander Holevo, 1973) sets a fundamental limit: a single qubit can transmit at most one classical bit of accessible information, no matter how cleverly it is encoded. This is the upper limit on how much Eve can learn per intercepted photon.",
  },
  {
    category: 'Theory',
    text: "The Devetak-Winter formula (2005) gives the asymptotic secret-key rate of any QKD protocol as R = I(A;B) − χ(E;A), the difference between Alice-Bob mutual information and the Holevo bound between Eve and Alice. Every modern security proof reduces to this expression.",
  },

  // ----- More protocols -----
  {
    category: 'BB84',
    text: "BB84 has been physically realized with polarisation, time-bin, phase, and even orbital-angular-momentum encodings. The protocol itself is medium-agnostic — only the photon's degree of freedom changes.",
  },
  {
    category: 'Trivia',
    text: "Continuous-Variable QKD (Grosshans-Grangier 2002) encodes information in the quadratures of coherent laser pulses rather than in single photons. It uses standard telecom hardware (homodyne detection) but is more sensitive to channel excess noise.",
  },
  {
    category: 'Trivia',
    text: "The COW (Coherent One-Way) and DPS (Differential Phase Shift) protocols, developed in the mid-2000s, encode bits in pulse-train timing or phase relations rather than basis choice — simpler hardware, but harder formal security proofs.",
  },

  // ----- Hardware -----
  {
    category: 'Trivia',
    text: "Superconducting Nanowire Single-Photon Detectors (SNSPDs), cooled to ~2 K, now reach >95 % efficiency with sub-100-ps timing jitter. Almost every recent long-distance QKD record is owed to SNSPD technology.",
  },
  {
    category: 'Trivia',
    text: "True single-photon sources are still rare in deployed QKD. Almost all field systems use attenuated laser pulses (weak coherent states) — which is why the decoy-state method is so important.",
  },

  // ----- More history / experiments -----
  {
    category: 'History',
    text: "Alain Aspect's 1982 experiments at Orsay decisively closed the locality loophole in Bell-inequality tests, paving the way for E91. He shared the 2022 Nobel Prize in Physics with John Clauser and Anton Zeilinger.",
  },
  {
    category: 'History',
    text: "In 2015, a team at Delft (Hensen et al.) performed the first 'loophole-free' Bell test — closing the detection, locality and freedom-of-choice loopholes simultaneously. This put device-independent QKD on solid experimental footing.",
  },
  {
    category: 'Milestones',
    text: "The UK Quantum Network, deployed by BT and Toshiba between Cambridge and London, has been carrying live QKD-secured traffic over commercial fiber since 2021 — one of the first sustained government-industry QKD trials in Europe.",
  },
  {
    category: 'Milestones',
    text: "South Korea's SK Telecom and KT operate one of the world's largest commercial QKD networks, spanning multiple cities. Their dedicated QKD-secured connection has been in production use since 2020.",
  },

  // ----- Open problems / debate -----
  {
    category: 'Open problems',
    text: "QKD requires an authenticated classical channel between Alice and Bob to compare bases and check QBER. That authentication itself needs a pre-shared key or a public-key infrastructure — leading to the open question of how to bootstrap QKD in a quantum-resistant way.",
  },
  {
    category: 'Open problems',
    text: "In 2020 the US National Security Agency published a position paper recommending post-quantum cryptography (PQC) over QKD for most national-security uses, citing deployment cost and trusted-node risk. The QKD community continues to push back, especially in long-term-secrecy scenarios.",
  },
  {
    category: 'Open problems',
    text: "Every 'trusted node' in a long-haul QKD network is a single point of compromise: an attacker who breaches one router learns every key passing through it. Removing trusted nodes is the main motivation behind quantum-repeater research.",
  },

  // ----- More attacks -----
  {
    category: 'Attacks',
    text: "The 'photon-number-splitting' attack name predates the decoy-state cure. Lutkenhaus's analysis in the late 1990s showed that without decoy states, no commercial weak-coherent-pulse QKD system could be proven secure at any non-trivial distance.",
  },

  // ----- Industry / trivia -----
  {
    category: 'Trivia',
    text: "ID Quantique (founded 2001 in Geneva) was the first company to commercialise QKD products. Today its hardware is used by banks, governments, and the Korean QKD backbone — but the company is equally well-known for its quantum-random-number-generator (QRNG) chips, which spun off from the same single-photon technology.",
  },
  {
    category: 'Trivia',
    text: "Toshiba's QKD research has been operating out of Cambridge, UK since 2003. Their twin-field QKD breakthroughs and SK Telecom collaboration make them one of the few non-Chinese groups pushing both records and deployment.",
  },
  {
    category: 'Trivia',
    text: "Quantum Random Number Generators (QRNGs) are a spin-off of QKD technology and arguably its first commercial success — millions of QRNG chips ship in mobile phones, cloud-HSMs, and online-gambling regulators, providing certifiable randomness from quantum vacuum fluctuations.",
  },

  // ----- Foundational papers -----
  {
    category: 'History',
    text: "The EPR paradox (Einstein-Podolsky-Rosen 1935) introduced the entanglement scenarios that QKD still relies on. Einstein famously called the resulting correlations 'spooky action at a distance' - modern QKD turns this discomfort into a security feature.",
  },
  {
    category: 'History',
    text: "John Bell's 1964 inequality paper — published in the obscure journal 'Physics Physique Физика' (which folded a few years later) — became one of the most cited results in physics. Without Bell, E91 and device-independent QKD would simply not exist.",
  },
  {
    category: 'History',
    text: "Quantum teleportation (Bennett, Brassard, Crépeau, Jozsa, Peres, Wootters 1993) is not just sci-fi terminology — it is the protocol that lets entanglement swapping work, which in turn enables Measurement-Device-Independent QKD and quantum repeaters.",
  },

  // ----- Security proofs -----
  {
    category: 'Theory',
    text: "The first unconditional security proof of BB84 came from Dominic Mayers in 1996 (published 2001) — running to roughly 90 pages of dense quantum information theory. Simpler proofs followed: Shor-Preskill (2000) via CSS quantum codes, then Renner (2005) using composable security.",
  },

  // ----- Classical processing -----
  {
    category: 'Theory',
    text: "CASCADE (Brassard-Salvail 1994) is the de-facto error correction for QKD: iterative binary search over permuted blocks, leaking just over the Slepian-Wolf bound of N·h(QBER) bits. Modern systems also use LDPC codes for one-pass higher-rate reconciliation.",
  },

  // ----- Hardware + experiments -----
  {
    category: 'Milestones',
    text: "In 2007 a free-space QKD link was demonstrated over 144 km between the Canary Islands of La Palma and Tenerife (Schmitt-Manderbach et al.) — the experimental proof-of-concept that satellite QKD would later make routine.",
  },

  // ----- Wider cryptographic context -----
  {
    category: 'Open problems',
    text: "Peter Shor's 1994 algorithm — which factors integers in polynomial time on a quantum computer — is the threat that put QKD on the map. Breaking RSA-2048 would require roughly 20 million physical qubits with current error-correction overhead. Still a long way off, but the harvest-now-decrypt-later threat is already real.",
  },
  {
    category: 'Open problems',
    text: "Grover's algorithm gives 'only' a quadratic speed-up against symmetric ciphers like AES. AES-256 is still considered safe against a future quantum computer — its effective security drops from 256 bits to roughly 128, which is well within the comfortable range.",
  },

  // ----- Impossibility & negative results -----
  {
    category: 'Theory',
    text: "Quantum bit commitment is provably impossible (Mayers 1997; Lo-Chau 1997) — a famous negative result in quantum cryptography. The same techniques that make QKD secure also forbid Alice from binding herself to a hidden bit she cannot later change.",
  },
]


export const CATEGORY_COLOR = {
  History:        'text-purple-300 bg-purple-950 border-purple-800',
  BB84:           'text-emerald-300 bg-emerald-950 border-emerald-800',
  B92:            'text-emerald-300 bg-emerald-950 border-emerald-800',
  SARG04:         'text-emerald-300 bg-emerald-950 border-emerald-800',
  E91:            'text-emerald-300 bg-emerald-950 border-emerald-800',
  Theory:         'text-cyan-300 bg-cyan-950 border-cyan-800',
  Attacks:        'text-red-300 bg-red-950 border-red-800',
  Milestones:     'text-amber-300 bg-amber-950 border-amber-800',
  'Open problems':'text-pink-300 bg-pink-950 border-pink-800',
  Trivia:         'text-gray-300 bg-gray-800 border-gray-700',
}


export default function FunFactPanel() {
  const [idx, setIdx] = useState(() => Math.floor(Math.random() * FACTS.length))

  const fact = FACTS[idx]
  const categoryClass = CATEGORY_COLOR[fact.category] || CATEGORY_COLOR.Trivia

  function nextFact() {
    let next = idx
    while (next === idx && FACTS.length > 1) {
      next = Math.floor(Math.random() * FACTS.length)
    }
    setIdx(next)
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="text-yellow-400" size={18} />
        <h3 className="text-sm font-semibold text-gray-200">Did you know?</h3>
        <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${categoryClass}`}>
          {fact.category}
        </span>
      </div>

      <p className="text-sm text-gray-300 leading-relaxed mb-4">
        {fact.text}
      </p>

      <div className="flex justify-end">
        <button
          onClick={nextFact}
          className="text-xs px-3 py-1.5 bg-yellow-900/40 hover:bg-yellow-900/60 border border-yellow-800 text-yellow-200 rounded-md transition-colors flex items-center gap-1.5"
        >
          <Shuffle size={12} /> Random
        </button>
      </div>
    </div>
  )
}
