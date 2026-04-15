from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit_aer.noise import NoiseModel, depolarizing_error
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

def measure_qubits(network, bases, noise_prob=0.0):
    results = []
    backend = Aer.get_backend('qasm_simulator')
    
    # Adăugăm Noise Model dacă probabilitatea e > 0
    noise_model = None
    if noise_prob > 0:
        noise_model = NoiseModel()
        error = depolarizing_error(noise_prob, 1)
        noise_model.add_all_qubit_quantum_error(error, ['h', 'x', 'measure'])

    for i in range(len(network)):
        qc = network[i]
        if bases[i] == 1: 
            qc.h(0)
        qc.measure(0, 0)
        # Rulăm cu noise_model (dacă există)
        job = backend.run(qc, shots=1, noise_model=noise_model, memory=True)
        result = job.result().get_memory()[0]
        results.append(int(result))
    return results