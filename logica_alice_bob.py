from qiskit import QuantumCircuit
from qiskit_aer import Aer
import numpy as np

def create_qubits(bits, bases):
    network = []
    for i in range(len(bits)):
        qc = QuantumCircuit(1, 1)
        if bits[i] == 1:
            qc.x(0) 
        if bases[i] == 1: # Baza Diagonală
            qc.h(0)
        network.append(qc)
    return network

def measure_qubits(network, bases):
    results = []
    backend = Aer.get_backend('qasm_simulator')
    for i in range(len(network)):
        qc = network[i]
        if bases[i] == 1: # Bob măsoară în bază diagonală
            qc.h(0)
        qc.measure(0, 0)
        # În Qiskit 1.0+, rulăm direct cu backend.run
        job = backend.run(qc, shots=1, memory=True)
        result = job.result().get_memory()[0]
        results.append(int(result))
    return results

# --- Simularea Protocolului ---
n = 20 # Începem cu 20 de biți
alice_bits = np.random.randint(2, size=n)
alice_bases = np.random.randint(2, size=n)
bob_bases = np.random.randint(2, size=n)

# 1. Alice trimite qubitii
qubits = create_qubits(alice_bits, alice_bases)

# 2. Bob îi măsoară
bob_results = measure_qubits(qubits, bob_bases)

# 3. SIFTING (Compararea bazelor pe canal clasic)
final_key_alice = []
final_key_bob = []

for i in range(n):
    if alice_bases[i] == bob_bases[i]:
        final_key_alice.append(alice_bits[i])
        final_key_bob.append(bob_results[i])

print(f"Baze Alice: {alice_bases}")
print(f"Baze Bob:   {bob_bases}")
print("-" * 30)
print(f"Cheie Alice: {final_key_alice}")
print(f"Cheie Bob:   {final_key_bob}")
print(f"Succes? {'DA' if final_key_alice == final_key_bob else 'NU'}")