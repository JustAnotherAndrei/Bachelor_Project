import numpy as np
from quantum_core import create_qubits, measure_qubits
from classical_processing import sifting, calculate_qber, simple_reconciliation
from privacy_amplification import apply_privacy_amplification

# --- CONFIGURARE ---
n = 100 
noise = 0.03 # 3% zgomot în canalul cuantic

# 1. GENERARE DATE (Alice)
alice_bits = np.random.randint(2, size=n)
alice_bases = np.random.randint(2, size=n)
bob_bases = np.random.randint(2, size=n)

# 2. TRANSMISIE CUANTICĂ (Alice -> Canal -> Bob)
qubits = create_qubits(alice_bits, alice_bases)
bob_results = measure_qubits(qubits, bob_bases, noise_prob=noise)

# 3. SIFTING (Canal Clasic)
key_alice, key_bob = sifting(alice_bases, bob_bases, alice_bits, bob_results)

# 4. ANALIZĂ ȘI POST-PROCESARE
qber = calculate_qber(key_alice, key_bob)
print(f"QBER detectat: {qber*100:.2f}%")

if qber < 0.11: # Dacă eroarea e sub 11%, continuăm
    # Corecție
    key_bob_final = simple_reconciliation(key_alice, key_bob)
    
    # Privacy Amplification
    final_shared_key = apply_privacy_amplification(key_bob_final)
    
    print("-" * 30)
    print(f"Cheia Sifted (Alice): {key_alice[:10]}...")
    print(f"Cheia Sifted (Bob):   {key_bob[:10]}...")
    print(f"Sunt identice după corecție? {key_alice == key_bob_final}")
    print(f"CHEIE FINALĂ SECURIZATĂ (Hex): {final_shared_key}")
else:
    print("ALERTĂ: Prea mult zgomot sau spion (Eve)! Protocol întrerupt.")