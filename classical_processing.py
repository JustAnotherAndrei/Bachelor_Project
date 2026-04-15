def sifting(alice_bases, bob_bases, alice_bits, bob_results):
    final_key_alice = []
    final_key_bob = []
    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            final_key_alice.append(alice_bits[i])
            final_key_bob.append(bob_results[i])
    return final_key_alice, final_key_bob

def calculate_qber(key_alice, key_bob):
    if len(key_alice) == 0: return 0
    errors = sum(1 for a, b in zip(key_alice, key_bob) if a != b)
    return errors / len(key_alice)

def simple_reconciliation(key_alice, key_bob):
    """Corecție simplificată: Alice trimite biții corecți pentru blocurile cu erori."""
    corrected_key_bob = list(key_bob)
    # Împărțim în blocuri de 4 biți
    block_size = 4
    for i in range(0, len(key_alice), block_size):
        b_alice = key_alice[i:i+block_size]
        b_bob = key_bob[i:i+block_size]
        if sum(b_alice) % 2 != sum(b_bob) % 2:
            # Dacă paritatea diferă, Bob corectează blocul (simulat pentru licență)
            for j in range(i, min(i + block_size, len(key_bob))):
                corrected_key_bob[j] = key_alice[j]
    return corrected_key_bob